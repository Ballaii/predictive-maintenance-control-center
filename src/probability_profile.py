"""Persist an already evaluated calibrated candidate without replacing the original experiment."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from src.config import ARTIFACTS, DATA_PATH, DEFAULT_POLICY, FEATURES, MODELS, TARGET
from src.data_loader import load_dataset
from src.evaluate import evaluate_scores
from src.preprocessing import model_candidates
from src.train import save_json, split_dataset

PROTECTED_FILES = [
    ARTIFACTS / "evaluation.json", ARTIFACTS / "frozen_selection.json",
    ARTIFACTS / "split_membership.csv", ARTIFACTS / "historical_predictions.csv",
    MODELS / "selected_model.joblib", MODELS / "metadata.json",
]


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def best_f1_point(curve: dict) -> dict:
    precision = np.asarray(curve["precision"][:-1])
    recall = np.asarray(curve["recall"][:-1])
    f1 = np.divide(2 * precision * recall, precision + recall,
                   out=np.zeros_like(precision), where=(precision + recall) > 0)
    index = int(np.argmax(f1))
    return {
        "threshold": float(curve["thresholds"][index]),
        "method": "maximum validation F1; no 90% precision constraint",
        "precision": float(precision[index]), "recall": float(recall[index]),
        "f1": float(f1[index]),
    }


def select_probability_plan(validation: dict) -> dict:
    calibrated = [name for name in validation if name.startswith("Calibrated ")]
    if not calibrated:
        raise ValueError("No previously evaluated calibrated candidate is available.")
    selected = min(calibrated, key=lambda name: (
        validation[name]["metrics"]["brier_score"],
        validation[name]["metrics"]["log_loss"],
    ))
    previous = validation[selected]
    return {
        "selected_model": selected,
        "selection_rule": "Among existing calibrated candidates: lowest validation Brier, then log loss.",
        "default_policy": DEFAULT_POLICY,
        "policies": {
            "high_precision": previous["operating_point"],
            "balanced": best_f1_point(previous["metrics"]["pr_curve"]),
        },
        "calibration_method": "sigmoid, 3-fold CV wholly within the original training partition",
        "evidence_scope": (
            "Assignment-alignment extension after original test results were already inspected. "
            "Model and both thresholds use saved validation evidence only. Test results reuse "
            "the original held-out partition; this is not a new untouched test experiment."
        ),
    }


def assert_reconstruction(actual: dict, recorded: dict) -> None:
    for key in ["average_precision", "roc_auc", "brier_score", "log_loss", "precision", "recall"]:
        if not np.isclose(actual[key], recorded[key], rtol=0, atol=1e-12):
            raise ValueError(f"Reconstructed calibrated candidate differs from original {key}.")
    for key in ["precision", "recall", "thresholds"]:
        if not np.allclose(actual["pr_curve"][key], recorded["pr_curve"][key], rtol=0, atol=1e-12):
            raise ValueError("Reconstructed probability rankings differ from the original experiment.")


def profile_metadata(plan: dict, base: dict, model_path: Path) -> dict:
    metadata = dict(base)
    for key in ["test_metrics", "threshold_method", "model_sha256", "created_utc"]:
        metadata.pop(key, None)
    metadata.update(
        version="1.1.0", selected_model=plan["selected_model"],
        created_utc=datetime.now(timezone.utc).isoformat(),
        threshold=plan["policies"][DEFAULT_POLICY]["threshold"],
        threshold_method=plan["policies"][DEFAULT_POLICY]["method"],
        default_policy=DEFAULT_POLICY, policies=plan["policies"],
        score_kind="calibrated probability estimate", probability_column="failure_probability",
        calibration_method=plan["calibration_method"], evidence_scope=plan["evidence_scope"],
        selection_rule=plan["selection_rule"], model_sha256=file_hash(model_path),
        risk_categories="Elevated if estimated probability >= chosen policy threshold; Lower otherwise.",
    )
    return metadata


def main() -> None:
    if (MODELS / "probability_metadata.json").exists():
        raise RuntimeError("Probability profile already exists. Do not retrain it at dashboard startup.")
    original = json.loads((ARTIFACTS / "evaluation.json").read_text(encoding="utf-8"))
    base = json.loads((MODELS / "metadata.json").read_text(encoding="utf-8"))
    if file_hash(DATA_PATH) != base["dataset_sha256"]:
        raise ValueError("Dataset differs from the original experiment.")
    validation = {name: result["validation"] for name, result in original.items()}
    plan = select_probability_plan(validation)
    protected_hashes = {path.name: file_hash(path) for path in PROTECTED_FILES}
    plan["original_file_hashes"] = protected_hashes
    save_json(ARTIFACTS / "probability_profile_plan.json", plan)
    frame = load_dataset()
    splits = split_dataset(frame)
    saved_splits = pd.read_csv(ARTIFACTS / "split_membership.csv").set_index("UDI")["split"]
    for name, part in splits.items():
        if not saved_splits.loc[part.UDI].eq(name).all():
            raise ValueError("Reconstruction split differs from original saved membership.")
    model = model_candidates()[plan["selected_model"]]
    print(f"Reconstructing {plan['selected_model']} on the original training partition.", flush=True)
    model.fit(splits["train"][FEATURES], splits["train"][TARGET])
    evaluations = {key: {"threshold": value["threshold"], "method": value["method"]}
                   for key, value in plan["policies"].items()}
    for name in ["validation", "test"]:
        part = splits[name]
        probabilities = model.predict_proba(part[FEATURES])[:, 1]
        for key, policy in plan["policies"].items():
            evaluations[key][name] = evaluate_scores(part[TARGET].to_numpy(), probabilities, policy["threshold"])
        recorded = original[plan["selected_model"]]
        expected = recorded["validation"]["metrics"] if name == "validation" else recorded["test"]
        assert_reconstruction(evaluations[DEFAULT_POLICY][name], expected)
    model_path = MODELS / "probability_model.joblib"
    joblib.dump(model, model_path, compress=3)
    save_json(MODELS / "probability_metadata.json", profile_metadata(plan, base, model_path))
    save_json(ARTIFACTS / "probability_evaluation.json", {
        "selected_model": plan["selected_model"], "evidence_scope": plan["evidence_scope"],
        "policies": evaluations,
    })
    history = frame[["UDI", "Product ID", *FEATURES, TARGET]].copy()
    history["split"] = history.UDI.map(saved_splits)
    history["failure_probability"] = model.predict_proba(frame[FEATURES])[:, 1]
    history.to_csv(ARTIFACTS / "historical_probabilities.csv", index=False)
    if any(file_hash(path) != protected_hashes[path.name] for path in PROTECTED_FILES):
        raise RuntimeError("Original experiment files changed during probability preparation.")
    print(json.dumps({key: {field: value["test"][field] for field in
                           ["threshold", "precision", "recall", "f1", "confusion_matrix"]}
                      for key, value in evaluations.items()}, indent=2))
    print("Original experiment hashes unchanged; reconstructed validation/test results match.")


if __name__ == "__main__":
    main()
