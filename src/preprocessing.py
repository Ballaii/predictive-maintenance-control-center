from sklearn.calibration import CalibratedClassifierCV
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from src.config import CATEGORY, NUMERIC, SEED


def logistic_pipeline() -> Pipeline:
    preprocessing = ColumnTransformer([
        ("numeric", StandardScaler(), NUMERIC),
        ("category", OneHotEncoder(handle_unknown="error", sparse_output=False), [CATEGORY]),
    ])
    return Pipeline([
        ("pre", preprocessing),
        ("classifier", LogisticRegression(
            class_weight="balanced", solver="liblinear", max_iter=5000, random_state=SEED,
        )),
    ])


def forest_pipeline() -> Pipeline:
    preprocessing = ColumnTransformer([
        ("numeric", "passthrough", NUMERIC),
        ("category", OneHotEncoder(handle_unknown="error", sparse_output=False), [CATEGORY]),
    ])
    return Pipeline([
        ("pre", preprocessing),
        ("classifier", RandomForestClassifier(
            n_estimators=400, class_weight="balanced", random_state=SEED, n_jobs=2,
        )),
    ])


def model_candidates() -> dict:
    return {
        "Majority baseline": DummyClassifier(strategy="most_frequent"),
        "Calibrated Logistic Regression": CalibratedClassifierCV(
            estimator=logistic_pipeline(), cv=3, method="sigmoid",
        ),
        "Random Forest": forest_pipeline(),
        "Calibrated Random Forest": CalibratedClassifierCV(
            estimator=forest_pipeline(), cv=3, method="sigmoid",
        ),
    }
