import pytest

from src.config import FEATURES
from src.data_loader import load_dataset
from src.inference import Predictor


@pytest.fixture(scope="session")
def dataset():
    return load_dataset()


@pytest.fixture
def observations(dataset):
    return dataset[FEATURES].head(5).copy()


@pytest.fixture(scope="session")
def predictor():
    return Predictor.load()


@pytest.fixture(scope="session")
def original_predictor():
    return Predictor.load_original_classifier()
