import csv
import hashlib
import io
import json
from dataclasses import dataclass

import joblib
import numpy as np
import pandas as pd

from src.config import DEFAULT_POLICY, FEATURES, MAX_BATCH_ROWS, MAX_UPLOAD_BYTES, MODELS, NUMERIC
from src.data_loader import validate_features


@dataclass
class Predictor:
    model: object
    metadata: dict

    @classmethod
    def load(cls) -> "Predictor":
        return cls._load_artifacts("probability")

    @classmethod
    def load_original_classifier(cls) -> "Predictor":
        return cls._load_artifacts("original")

    @classmethod
    def _load_artifacts(cls, profile: str) -> "Predictor":
        path = MODELS / ("probability_model.joblib" if profile == "probability" else "selected_model.joblib")
        metadata_path = MODELS / ("probability_metadata.json" if profile == "probability" else "metadata.json")
        try:
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
            if hashlib.sha256(path.read_bytes()).hexdigest() != metadata["model_sha256"]:
                raise ValueError("Model checksum differs from trusted project metadata.")
            model = joblib.load(path)
        except FileNotFoundError as error:
            raise FileNotFoundError(
                "Model not found. Run python -m src.train for a fresh experiment, "
                "then python -m src.probability_profile."
            ) from error
        if metadata["features"] != FEATURES or list(model.feature_names_in_) != FEATURES:
            raise ValueError("Stored model feature schema does not match the application.")
        return cls(model, metadata)

    def policy(self, name: str = DEFAULT_POLICY) -> dict:
        if "policies" not in self.metadata:
            if name != DEFAULT_POLICY:
                raise ValueError("The original classifier has only its frozen high-precision policy.")
            return {"threshold": self.metadata["threshold"], "method": self.metadata["threshold_method"]}
        if name not in self.metadata["policies"]:
            raise ValueError(f"Unknown classification policy: {name}")
        return self.metadata["policies"][name]

    def predict(self, frame: pd.DataFrame, policy: str = DEFAULT_POLICY) -> pd.DataFrame:
        clean = validate_features(frame)
        threshold = self.policy(policy)["threshold"]
        scores = self.model.predict_proba(clean)[:, 1]
        if not np.isfinite(scores).all() or not ((scores >= 0) & (scores <= 1)).all():
            raise ValueError("Model returned invalid scores.")
        result = clean.copy()
        score_column = self.metadata.get("probability_column", "model_score")
        result[score_column] = scores
        result["classification_policy"] = policy
        result["decision_threshold"] = threshold
        result["elevated_risk"] = scores >= threshold
        result["risk_category"] = np.where(result.elevated_risk, "Elevated", "Lower")
        result["outside_training_range"] = False
        for column in NUMERIC:
            low, high = self.metadata["training_ranges"][column]
            result["outside_training_range"] |= ~clean[column].between(low, high)
        return result


def parse_batch_csv(content: bytes) -> pd.DataFrame:
    if len(content) > MAX_UPLOAD_BYTES:
        raise ValueError("CSV exceeds the 5 MiB upload limit.")
    try:
        text = content.decode("utf-8-sig")
        if "\x00" in text:
            raise ValueError("CSV contains null bytes.")
        rows = csv.reader(io.StringIO(text), strict=True)
        header = next(rows, [])
        if len(header) != len(set(header)):
            raise ValueError("Duplicate CSV column headers are not allowed.")
        for row_number, row in enumerate(rows, start=2):
            if row and len(row) != len(header):
                raise ValueError(f"CSV row {row_number} has the wrong number of fields.")
        frame = pd.read_csv(io.StringIO(text), nrows=MAX_BATCH_ROWS + 1)
    except (UnicodeError, pd.errors.ParserError, pd.errors.EmptyDataError, csv.Error) as error:
        raise ValueError("Upload a nonempty UTF-8 CSV with the six predictor columns.") from error
    if len(frame) > MAX_BATCH_ROWS:
        raise ValueError("CSV exceeds the 10,000-row limit.")
    return validate_features(frame)
