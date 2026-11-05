import json

import joblib
import numpy as np

from src.config import ARTIFACTS, FEATURES, FLAGS, MODELS, TARGET
from src.evaluate import evaluate_scores, select_threshold
from src.preprocessing import forest_pipeline, logistic_pipeline
from src.train import choose_model


def test_threshold_uses_best_eligible_recall():
    labels = np.array([1, 0, 1, 0, 1])
    scores = np.array([0.99, 0.1, 0.98, 0.97, 0.96])
    point = select_threshold(labels, scores)
    assert point["threshold"] == 0.98
    assert point["precision"] == 1
    assert point["recall"] == 2 / 3


def test_threshold_fallback():
    point = select_threshold(np.array([0, 0, 1]), np.array([0.9, 0.8, 0.1]))
    assert not point["precision_target_achieved"]
    assert point["threshold"] == 0.1


def test_known_confusion_matrix():
    metrics = evaluate_scores(np.array([0, 0, 1, 1]), np.array([0.1, 0.9, 0.7, 0.2]), 0.7)
    assert metrics["confusion_matrix"] == [[1, 1], [1, 1]]
    assert metrics["precision"] == metrics["recall"] == metrics["f1"] == 0.5
    assert metrics["false_positives"] == metrics["false_negatives"] == 1


def test_model_training_and_pipeline_schema(dataset):
    sample = dataset.groupby(TARGET).head(100)
    for model in [logistic_pipeline(), forest_pipeline()]:
        model.fit(sample[FEATURES], sample[TARGET])
        assert list(model.feature_names_in_) == FEATURES
        assert not set(FEATURES) & set([TARGET, *FLAGS, "UDI", "Product ID"])
        assert np.isfinite(model.predict_proba(sample[FEATURES])).all()


def test_scaler_fits_training_values_only(observations):
    model = logistic_pipeline().named_steps["pre"]
    model.fit(observations)
    original_mean = model.named_transformers_["numeric"].mean_.copy()
    changed = observations.copy()
    changed.iloc[:, 1:] = changed.iloc[:, 1:] * 2
    model.transform(changed)
    np.testing.assert_array_equal(original_mean, model.named_transformers_["numeric"].mean_)


def test_serialization_and_threshold(predictor, observations, tmp_path):
    before = predictor.predict(observations)
    model_path = tmp_path / "model.joblib"
    joblib.dump(predictor.model, model_path)
    restored = joblib.load(model_path)
    np.testing.assert_array_equal(before.failure_probability, restored.predict_proba(observations)[:, 1])
    assert before.failure_probability.between(0, 1).all()
    np.testing.assert_array_equal(before.elevated_risk, before.failure_probability >= predictor.metadata["threshold"])


def test_selection_frozen_and_test_results_consistent(original_predictor):
    selection = json.loads((ARTIFACTS / "frozen_selection.json").read_text())
    evaluation = json.loads((ARTIFACTS / "evaluation.json").read_text())
    assert choose_model(selection["validation"]) == original_predictor.metadata["selected_model"]
    for result in evaluation.values():
        assert result["test"]["threshold"] == result["validation"]["metrics"]["threshold"]
    assert (MODELS / "selected_model.joblib").exists()
