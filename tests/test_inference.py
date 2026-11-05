import numpy as np
import pytest

from src.config import FEATURES, MAX_UPLOAD_BYTES
from src.inference import parse_batch_csv


def test_batch_matches_individual(predictor, observations):
    parsed = parse_batch_csv(observations.to_csv(index=False).encode())
    batch = predictor.predict(parsed)
    for index, row in parsed.iterrows():
        individual = predictor.predict(row.to_frame().T)
        assert batch.loc[index, "failure_probability"] == individual.iloc[0].failure_probability
    assert len(batch) == len(observations)


@pytest.mark.parametrize("content", [
    b"", b"hello", b"\x00", b"\xff\xfe", b"Type,Type\nL,M",
    (",".join(FEATURES) + "\n").encode(), b"Machine failure\n1",
    (",".join(FEATURES) + "\nL,300,310,1500,40,100,extra").encode(),
])
def test_bad_csv(content):
    with pytest.raises(ValueError):
        parse_batch_csv(content)


def test_oversize_csv():
    with pytest.raises(ValueError, match="5 MiB"):
        parse_batch_csv(b"x" * (MAX_UPLOAD_BYTES + 1))


def test_batch_row_limit(observations):
    content = observations.head(1).to_csv(index=False)
    content += observations.head(1).to_csv(index=False, header=False) * 10000
    with pytest.raises(ValueError, match="10,000"):
        parse_batch_csv(content.encode())


def test_outside_training_range_warning(predictor, observations):
    observations["Tool wear [min]"] = 500
    result = predictor.predict(observations)
    assert result.outside_training_range.all()
    assert np.isfinite(result.failure_probability).all()
