import hashlib
import io
import json
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

from src.config import (
    ARTIFACTS, CATEGORY, COLUMNS, DATA_PATH, DATA_SHA256, DATA_URL,
    FEATURES, FLAGS, NUMERIC, PHYSICAL_BOUNDS, TARGET,
)


def validate_features(frame: pd.DataFrame) -> pd.DataFrame:
    """Validate the external six-column inference contract, returning canonical order."""
    if frame.empty:
        raise ValueError("No observations supplied. Include at least one data row.")
    missing = sorted(set(FEATURES) - set(frame.columns))
    extra = sorted(set(frame.columns) - set(FEATURES))
    if missing or extra or frame.columns.duplicated().any():
        raise ValueError(f"Expected exactly six predictor columns. Missing: {missing}; extra: {extra}")
    clean = frame.loc[:, FEATURES].copy()
    if clean.isna().any().any():
        raise ValueError("Missing values are not supported. Complete every predictor.")
    if not clean[CATEGORY].isin(["L", "M", "H"]).all():
        raise ValueError("Type must be exactly L, M, or H.")
    for column in NUMERIC:
        if clean[column].map(lambda value: isinstance(value, (bool, np.bool_))).any():
            raise ValueError(f"{column} must be numeric, not Boolean.")
        try:
            clean[column] = pd.to_numeric(clean[column], errors="raise")
        except (TypeError, ValueError) as error:
            raise ValueError(f"{column} must contain numeric measurements.") from error
        lower, upper = PHYSICAL_BOUNDS[column]
        if not np.isfinite(clean[column]).all() or not clean[column].between(lower, upper).all():
            raise ValueError(f"{column} must be finite and between {lower} and {upper}.")
    for column in ["Rotational speed [rpm]", "Tool wear [min]"]:
        if (clean[column] % 1 != 0).any():
            raise ValueError(f"{column} must contain whole numbers.")
    return clean


def dataset_report(frame: pd.DataFrame) -> dict:
    if list(frame.columns) != COLUMNS:
        raise ValueError(f"Unexpected dataset schema. Expected: {COLUMNS}")
    if len(frame) != 10000:
        raise ValueError(f"Expected 10,000 observations, found {len(frame):,}.")
    validate_features(frame[FEATURES])
    if frame.isna().any().any():
        raise ValueError("Dataset contains missing values.")
    for column in [TARGET, *FLAGS]:
        if not frame[column].isin([0, 1]).all():
            raise ValueError(f"{column} must be binary.")
    if not np.array_equal(frame.UDI.to_numpy(), np.arange(1, 10001)):
        raise ValueError("UDI must be the original sequence 1 through 10000.")
    if not frame["Product ID"].str.fullmatch(r"[LMH]\d+").all():
        raise ValueError("Malformed Product ID.")
    if not frame["Product ID"].str[0].eq(frame.Type).all():
        raise ValueError("Product ID category and Type disagree.")
    mismatches = frame[TARGET].ne(frame[FLAGS].max(axis=1))
    measurements = frame[NUMERIC]
    q1, q3 = measurements.quantile(0.25), measurements.quantile(0.75)
    iqr = q3 - q1
    outliers = ((measurements < q1 - 1.5 * iqr) | (measurements > q3 + 1.5 * iqr)).sum()
    return {
        "rows": len(frame), "columns": list(frame.columns),
        "dtypes": frame.dtypes.astype(str).to_dict(),
        "missing_cells": int(frame.isna().sum().sum()),
        "duplicate_records": int(frame.duplicated().sum()),
        "duplicate_predictors": int(frame.duplicated(FEATURES).sum()),
        "duplicate_product_ids": int(frame["Product ID"].duplicated().sum()),
        "target_counts": {str(k): int(v) for k, v in frame[TARGET].value_counts().items()},
        "failure_rate": float(frame[TARGET].mean()),
        "label_inconsistencies": int(mismatches.sum()),
        "inconsistent_udis": frame.loc[mismatches, "UDI"].tolist(),
        "observed_ranges": {c: [float(frame[c].min()), float(frame[c].max())] for c in NUMERIC},
        "iqr_outlier_counts": {c: int(v) for c, v in outliers.items()},
        "outlier_policy": "Retain valid extreme conditions; they may be meaningful failure signals.",
        "label_policy": "Retain official target labels; subtype flags are audit-only.",
    }


def load_dataset(path: Path = DATA_PATH) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError("Dataset missing. Run: python -m src.data_loader")
    frame = pd.read_csv(path)
    dataset_report(frame)
    return frame


def download_dataset() -> Path:
    try:
        with urllib.request.urlopen(DATA_URL, timeout=60) as response:
            archive = response.read()
        with zipfile.ZipFile(io.BytesIO(archive)) as bundle:
            content = bundle.read("ai4i2020.csv")
    except (urllib.error.URLError, OSError, zipfile.BadZipFile, KeyError) as error:
        raise RuntimeError(
            "UCI download failed. Retry python -m src.data_loader, or download dataset 601 "
            "from archive.ics.uci.edu and extract ai4i2020.csv into data/raw/."
        ) from error
    digest = hashlib.sha256(content).hexdigest()
    if digest != DATA_SHA256:
        raise ValueError("Official CSV checksum changed. Inspect the source before accepting new data.")
    dataset_report(pd.read_csv(io.BytesIO(content)))
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    DATA_PATH.write_bytes(content)
    return DATA_PATH


def main() -> None:
    path = download_dataset()
    report = dataset_report(load_dataset(path))
    report.update(source=DATA_URL, sha256=hashlib.sha256(path.read_bytes()).hexdigest())
    ARTIFACTS.mkdir(exist_ok=True)
    (ARTIFACTS / "dataset_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
