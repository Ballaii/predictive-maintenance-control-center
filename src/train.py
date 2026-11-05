import hashlib
import importlib.metadata
import json
import platform
from datetime import datetime, timezone

import joblib
import pandas as pd
from sklearn.inspection import permutation_importance
from sklearn.model_selection import train_test_split

from src.config import ARTIFACTS, DATA_PATH, FEATURES, MODELS, NUMERIC, SEED, TARGET
from src.data_loader import dataset_report, load_dataset
from src.evaluate import evaluate_scores, select_threshold
from src.preprocessing import model_candidates


def split_dataset(frame: pd.DataFrame) -> dict[str, pd.DataFrame]:
    development, test = train_test_split(
        frame, test_size=0.2, stratify=frame[TARGET], random_state=SEED,
    )
    train, validation = train_test_split(
        development, test_size=0.25, stratify=development[TARGET], random_state=SEED,
    )
    return {"train": train, "validation": validation, "test": test}


def save_json(path, value) -> None:
    path.write_text(json.dumps(value, indent=2, allow_nan=False), encoding="utf-8")


def fit_candidates(splits: dict) -> tuple[dict, dict]:
    trained, validation_results = {}, {}
    for name, model in model_candidates().items():
        print(f"Training {name} ...", flush=True)
        model.fit(splits["train"][FEATURES], splits["train"][TARGET])
        scores = model.predict_proba(splits["validation"][FEATURES])[:, 1]
        operating_point = select_threshold(splits["validation"][TARGET].to_numpy(), scores)
        if name == "Majority baseline":
            operating_point = {"threshold": 0.5, "method": "fixed majority-class baseline",
                               "precision_target_achieved": False, "recall": 0.0}
        metrics = evaluate_scores(
            splits["validation"][TARGET].to_numpy(), scores, operating_point["threshold"],
        )
        trained[name] = model
        validation_results[name] = {"operating_point": operating_point, "metrics": metrics}
    return trained, validation_results


def choose_model(validation_results: dict) -> str:
    candidates = {k: v for k, v in validation_results.items() if k != "Majority baseline"}

    def ranking(name: str) -> tuple:
        result = candidates[name]
        metrics, operating_point = result["metrics"], result["operating_point"]
        return (
            operating_point["precision_target_achieved"],
            metrics["recall"] if operating_point["precision_target_achieved"] else metrics["f1"],
            metrics["average_precision"], -metrics["brier_score"],
        )

    return max(candidates, key=ranking)


def feature_importance(forest, splits: dict) -> dict:
    transformed = forest.named_steps["pre"].get_feature_names_out()
    impurity = forest.named_steps["classifier"].feature_importances_
    permutation = permutation_importance(
        forest, splits["test"][FEATURES], splits["test"][TARGET],
        scoring="average_precision", n_repeats=5, random_state=SEED, n_jobs=2,
    )
    return {
        "model": "Random Forest (uncalibrated comparison model)",
        "impurity": dict(zip(transformed.tolist(), impurity.tolist())),
        "permutation_test_ap_decrease": dict(zip(FEATURES, permutation.importances_mean.tolist())),
        "permutation_std": dict(zip(FEATURES, permutation.importances_std.tolist())),
        "warning": "Post-freeze descriptive analysis only. Associations do not establish causality.",
    }


def main() -> None:
    ARTIFACTS.mkdir(exist_ok=True)
    MODELS.mkdir(exist_ok=True)
    if (MODELS / "metadata.json").exists():
        raise RuntimeError(
            "A completed experiment already exists. Archive models/ and artifacts/ before a new "
            "pre-specified experiment; do not tune repeatedly against the reported test set."
        )
    frame = load_dataset()
    splits = split_dataset(frame)
    report = dataset_report(frame)
    report["sha256"] = hashlib.sha256(DATA_PATH.read_bytes()).hexdigest()
    save_json(ARTIFACTS / "dataset_report.json", report)
    membership = pd.concat([
        part[["UDI", TARGET]].assign(split=name) for name, part in splits.items()
    ]).sort_values("UDI")
    membership.to_csv(ARTIFACTS / "split_membership.csv", index=False)
    distributions = {
        name: {"rows": len(part), "failures": int(part[TARGET].sum()),
               "failure_rate": float(part[TARGET].mean())} for name, part in splits.items()
    }
    save_json(ARTIFACTS / "split_distribution.json", distributions)
    trained, validation_results = fit_candidates(splits)
    selected = choose_model(validation_results)
    decision = {"selected_model": selected, "validation": validation_results,
                "selection_rule": "precision-target feasibility, recall (else F1), AP, then Brier"}
    save_json(ARTIFACTS / "frozen_selection.json", decision)
    print(f"Frozen model selection: {selected}. Beginning final test evaluation.", flush=True)
    results = {}
    for name, model in trained.items():
        threshold = validation_results[name]["operating_point"]["threshold"]
        test_scores = model.predict_proba(splits["test"][FEATURES])[:, 1]
        results[name] = {
            "validation": validation_results[name],
            "test": evaluate_scores(splits["test"][TARGET].to_numpy(), test_scores, threshold),
        }
    save_json(ARTIFACTS / "evaluation.json", results)
    save_json(ARTIFACTS / "feature_importance.json", feature_importance(trained["Random Forest"], splits))
    model_path = MODELS / "selected_model.joblib"
    joblib.dump(trained[selected], model_path, compress=3)
    metadata = {
        "version": "1.0.0", "created_utc": datetime.now(timezone.utc).isoformat(),
        "selected_model": selected, "features": FEATURES, "target": TARGET,
        "threshold": validation_results[selected]["operating_point"]["threshold"],
        "threshold_method": validation_results[selected]["operating_point"]["method"],
        "score_kind": "calibrated probability estimate" if selected.startswith("Calibrated")
                      else "uncalibrated model score",
        "calibration_caveat": "Calibration assessed on this synthetic sample; no external guarantee.",
        "training_ranges": {
            c: [float(splits["train"][c].min()), float(splits["train"][c].max())] for c in NUMERIC
        },
        "defaults": {c: float(splits["train"][c].median()) for c in NUMERIC},
        "seed": SEED, "python": platform.python_version(),
        "packages": {p: importlib.metadata.version(p) for p in
                     ["numpy", "pandas", "scikit-learn", "joblib", "scipy"]},
        "dataset_sha256": report["sha256"],
        "model_sha256": hashlib.sha256(model_path.read_bytes()).hexdigest(),
        "test_metrics": {k: v for k, v in results[selected]["test"].items()
                         if k not in ["pr_curve", "roc_curve", "calibration"]},
        "risk_categories": "Elevated: score >= validation-selected threshold; lower: below threshold.",
    }
    save_json(MODELS / "metadata.json", metadata)
    save_json(MODELS / "input_schema.json", {
        "columns": FEATURES, "categories": ["L", "M", "H"], "numeric": NUMERIC,
        "additional_columns": False,
    })
    predictions = frame[["UDI", "Product ID", *FEATURES, TARGET]].copy()
    predictions["split"] = predictions.UDI.map(membership.set_index("UDI")["split"])
    predictions["model_score"] = trained[selected].predict_proba(frame[FEATURES])[:, 1]
    predictions["elevated_risk"] = predictions.model_score >= metadata["threshold"]
    predictions.to_csv(ARTIFACTS / "historical_predictions.csv", index=False)
    print(json.dumps({"selected_model": selected, "test": metadata["test_metrics"]}, indent=2))


if __name__ == "__main__":
    main()
