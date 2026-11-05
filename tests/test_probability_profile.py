import json

import numpy as np
import pytest
from sklearn.calibration import CalibratedClassifierCV

from src.config import ARTIFACTS, FEATURES, TARGET
from src.evaluate import evaluate_scores
from src.probability_profile import PROTECTED_FILES, best_f1_point, file_hash, select_probability_plan
from src.train import split_dataset


def test_original_experiment_unchanged():
    plan = json.loads((ARTIFACTS / "probability_profile_plan.json").read_text())
    assert all(file_hash(path) == plan["original_file_hashes"][path.name] for path in PROTECTED_FILES)


def test_probability_choice_uses_validation_evidence():
    def candidate(brier, threshold):
        return {"metrics": {"brier_score": brier, "log_loss": brier,
                            "pr_curve": {"precision": [0.5, 1], "recall": [1, 0], "thresholds": [0.3]}},
                "operating_point": {"threshold": threshold}}

    validation = {"Calibrated Logistic Regression": candidate(0.01, 0.8),
                  "Calibrated Random Forest": candidate(0.02, 0.9),
                  "Random Forest": candidate(0.001, 0.5)}
    plan = select_probability_plan(validation)
    assert plan["selected_model"] == "Calibrated Logistic Regression"
    assert plan["policies"]["high_precision"]["threshold"] == 0.8
    assert plan["policies"]["balanced"]["threshold"] == 0.3


def test_best_f1_ignores_synthetic_terminal_pr_point():
    curve = {"precision": [0.25, 0.75, 1], "recall": [1, 0.75, 0], "thresholds": [0.1, 0.4]}
    point = best_f1_point(curve)
    assert point["threshold"] == 0.4
    assert point["f1"] == 0.75


def test_actual_calibration_and_canonical_schema(predictor):
    assert isinstance(predictor.model, CalibratedClassifierCV)
    assert predictor.model.method == "sigmoid"
    assert len(predictor.model.calibrated_classifiers_) == 3
    assert list(predictor.model.feature_names_in_) == FEATURES
    assert predictor.metadata["probability_column"] == "failure_probability"


@pytest.mark.parametrize("policy", ["high_precision", "balanced"])
def test_probability_unchanged_by_policy(predictor, dataset, policy):
    observations = dataset[FEATURES].iloc[::20]
    results = predictor.predict(observations, policy)
    default = predictor.predict(observations)
    np.testing.assert_array_equal(results.failure_probability, default.failure_probability)
    threshold = predictor.policy(policy)["threshold"]
    np.testing.assert_array_equal(results.elevated_risk, results.failure_probability >= threshold)
    assert results.classification_policy.eq(policy).all()
    assert results.decision_threshold.eq(threshold).all()


def test_unknown_policy_rejected(predictor, observations):
    with pytest.raises(ValueError, match="Unknown classification policy"):
        predictor.predict(observations, "arbitrary")


@pytest.mark.parametrize("policy", ["high_precision", "balanced"])
def test_saved_policy_metrics_match_predictions(predictor, dataset, policy):
    report = json.loads((ARTIFACTS / "probability_evaluation.json").read_text())
    for partition in ["validation", "test"]:
        part = split_dataset(dataset)[partition]
        predictions = predictor.predict(part[FEATURES], policy)
        metrics = evaluate_scores(part[TARGET].to_numpy(), predictions.failure_probability.to_numpy(),
                                  predictor.policy(policy)["threshold"])
        saved = report["policies"][policy][partition]
        assert metrics["confusion_matrix"] == saved["confusion_matrix"]
        assert metrics["brier_score"] == saved["brier_score"]
        assert metrics["precision"] == saved["precision"]


def test_history_probabilities_match_persisted_pipeline(predictor):
    import pandas as pd

    history = pd.read_csv(ARTIFACTS / "historical_probabilities.csv")
    subset = history.iloc[::100]
    predicted = predictor.predict(subset[FEATURES])
    np.testing.assert_allclose(subset.failure_probability, predicted.failure_probability, rtol=0, atol=1e-15)


def test_probability_is_not_a_relabelled_uncalibrated_score(predictor, original_predictor, observations):
    probability = predictor.predict(observations).failure_probability
    raw_score = original_predictor.predict(observations).model_score
    assert not np.allclose(probability, raw_score)
