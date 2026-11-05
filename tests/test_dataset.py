import hashlib

import numpy as np
import pytest

from src.config import DATA_PATH, DATA_SHA256, FEATURES, FLAGS, TARGET
from src.data_loader import dataset_report, validate_features
from src.train import split_dataset


def test_official_dataset(dataset):
    report = dataset_report(dataset)
    assert hashlib.sha256(DATA_PATH.read_bytes()).hexdigest() == DATA_SHA256
    assert report["rows"] == 10000
    assert report["target_counts"] == {"0": 9661, "1": 339}
    assert report["missing_cells"] == 0
    assert report["duplicate_records"] == 0


def test_disjoint_stratified_reproducible_splits(dataset):
    splits = split_dataset(dataset)
    assert [len(part) for part in splits.values()] == [6000, 2000, 2000]
    identifiers = [set(part.UDI) for part in splits.values()]
    assert all(not identifiers[i] & identifiers[j] for i in range(3) for j in range(i))
    assert set.union(*identifiers) == set(dataset.UDI)
    for name, part in splits.items():
        assert abs(part[TARGET].mean() - dataset[TARGET].mean()) < 0.001
        assert part.UDI.tolist() == split_dataset(dataset)[name].UDI.tolist()


@pytest.mark.parametrize("column,value", [
    ("Type", "X"), ("Type", "=cmd()"), ("Tool wear [min]", -1),
    ("Torque [Nm]", np.inf), ("Torque [Nm]", np.nan), ("Torque [Nm]", True),
    ("Air temperature [K]", 20), ("Process temperature [K]", "=1+2"),
    ("Rotational speed [rpm]", 1000.5), ("Tool wear [min]", 1.5),
])
def test_invalid_measurements(observations, column, value):
    observations[column] = observations[column].astype(object)
    observations.loc[observations.index[0], column] = value
    with pytest.raises(ValueError):
        validate_features(observations)


@pytest.mark.parametrize("column", [TARGET, *FLAGS, "UDI", "Product ID", "unexpected"])
def test_reject_extra_or_leaking_columns(observations, column):
    observations[column] = 1
    with pytest.raises(ValueError, match="extra"):
        validate_features(observations)


def test_missing_column(observations):
    with pytest.raises(ValueError, match="Missing"):
        validate_features(observations.drop(columns=[FEATURES[0]]))


def test_canonical_feature_order(observations):
    assert list(validate_features(observations[FEATURES[::-1]])) == FEATURES
