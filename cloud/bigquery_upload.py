import io
import json

import pandas as pd
from google.cloud import bigquery

from cloud.bigquery_setup import COLUMN_TYPES
from cloud.config import CloudConfig
from src.config import ARTIFACTS, MODELS

RENAME = {
    "UDI": "udi", "Product ID": "product_id", "Type": "machine_type",
    "Air temperature [K]": "air_temperature_k", "Process temperature [K]": "process_temperature_k",
    "Rotational speed [rpm]": "rotational_speed_rpm", "Torque [Nm]": "torque_nm",
    "Tool wear [min]": "tool_wear_min", "Machine failure": "machine_failure",
}


def cloud_rows() -> pd.DataFrame:
    frame = pd.read_csv(ARTIFACTS / "historical_probabilities.csv").rename(columns=RENAME)
    metadata = json.loads((MODELS / "probability_metadata.json").read_text(encoding="utf-8"))
    frame["model_version"] = metadata["version"]
    frame["model_name"] = metadata["selected_model"]
    frame["threshold"] = metadata["threshold"]
    frame["score_kind"] = metadata["score_kind"]
    frame["classification_policy"] = metadata["default_policy"]
    frame["elevated_risk"] = frame.failure_probability >= metadata["threshold"]
    return frame[[column for column, _ in COLUMN_TYPES]]


def upload(config: CloudConfig) -> None:
    client = bigquery.Client(project=config.project)
    content = cloud_rows().to_csv(index=False).encode("utf-8")
    job_config = bigquery.LoadJobConfig(
        schema=[bigquery.SchemaField(*field) for field in COLUMN_TYPES],
        source_format=bigquery.SourceFormat.CSV, skip_leading_rows=1,
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
    )
    client.load_table_from_file(
        io.BytesIO(content), f"{config.dataset_id}.observations",
        job_config=job_config, location=config.location,
    ).result()
    print("Replaced the dedicated demo table with 10,000 scored observations; no duplicate append.")


if __name__ == "__main__":
    config = CloudConfig.from_environment()
    if config is None:
        raise SystemExit("Set GOOGLE_CLOUD_PROJECT first. This explicit command replaces the demo table.")
    upload(config)
