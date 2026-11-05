from unittest.mock import MagicMock

import pytest

from cloud.analytics import MAX_QUERY_BYTES, fetch_summary
from cloud.bigquery_setup import COLUMN_TYPES, setup
from cloud.bigquery_upload import cloud_rows, upload
from cloud.config import CloudConfig


def test_no_configuration(monkeypatch):
    monkeypatch.delenv("GOOGLE_CLOUD_PROJECT", raising=False)
    assert CloudConfig.from_environment() is None


@pytest.mark.parametrize("variable,value", [
    ("GOOGLE_CLOUD_PROJECT", "bad`project"), ("BQ_DATASET", "x`; DROP TABLE data"),
])
def test_sql_identifier_rejection(monkeypatch, variable, value):
    monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", "demo-project-123")
    monkeypatch.setenv(variable, value)
    with pytest.raises(ValueError):
        CloudConfig.from_environment()


def test_cloud_export_schema():
    rows = cloud_rows()
    assert list(rows) == [name for name, _ in COLUMN_TYPES]
    assert len(rows) == 10000
    assert rows.udi.is_unique
    assert rows.model_version.notna().all()
    assert rows.failure_probability.between(0, 1).all()
    assert rows.classification_policy.eq("high_precision").all()
    assert rows.score_kind.eq("calibrated probability estimate").all()
    assert rows.elevated_risk.eq(rows.failure_probability >= rows.threshold).all()


def test_upload_replaces_demo_table(monkeypatch):
    client = MagicMock()
    monkeypatch.setattr("cloud.bigquery_upload.bigquery.Client", lambda **kwargs: client)
    upload(CloudConfig("demo-project-123", "maintenance_demo", "EU"))
    settings = client.load_table_from_file.call_args.kwargs["job_config"]
    assert settings.write_disposition == "WRITE_TRUNCATE"
    assert settings.skip_leading_rows == 1
    client.load_table_from_file.return_value.result.assert_called_once()


def test_summary_query_has_cost_limit(monkeypatch):
    client = MagicMock()
    job = client.query.return_value
    job.result.return_value = [{"observations": 10000}]
    monkeypatch.setattr("cloud.analytics.bigquery.Client", lambda **kwargs: client)
    result = fetch_summary(CloudConfig("demo-project-123", "maintenance_demo", "EU"))
    assert result["summary"]["observations"] == 10000
    assert client.query.call_args.kwargs["job_config"].maximum_bytes_billed == MAX_QUERY_BYTES


def test_setup_is_explicit_and_idempotent(monkeypatch):
    client = MagicMock()
    monkeypatch.setattr("cloud.bigquery_setup.bigquery.Client", lambda **kwargs: client)
    setup(CloudConfig("demo-project-123", "maintenance_demo", "EU"))
    assert client.create_dataset.call_args.kwargs["exists_ok"]
    assert client.create_table.call_args_list[0].kwargs["exists_ok"]
