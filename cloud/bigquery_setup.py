from google.cloud import bigquery

from cloud.config import CloudConfig

COLUMN_TYPES = [
    ("udi", "INTEGER"), ("product_id", "STRING"), ("machine_type", "STRING"),
    ("air_temperature_k", "FLOAT"), ("process_temperature_k", "FLOAT"),
    ("rotational_speed_rpm", "INTEGER"), ("torque_nm", "FLOAT"), ("tool_wear_min", "INTEGER"),
    ("machine_failure", "INTEGER"), ("split", "STRING"), ("failure_probability", "FLOAT"),
    ("elevated_risk", "BOOLEAN"), ("model_version", "STRING"), ("model_name", "STRING"),
    ("threshold", "FLOAT"), ("score_kind", "STRING"), ("classification_policy", "STRING"),
]


def setup(config: CloudConfig) -> None:
    client = bigquery.Client(project=config.project)
    dataset = bigquery.Dataset(config.dataset_id)
    dataset.location = config.location
    client.create_dataset(dataset, exists_ok=True)
    table = bigquery.Table(
        f"{config.dataset_id}.observations", schema=[bigquery.SchemaField(*field) for field in COLUMN_TYPES],
    )
    client.create_table(table, exists_ok=True)
    view = bigquery.Table(f"{config.dataset_id}.type_summary")
    view.view_query = f"""
        SELECT machine_type, COUNT(*) AS observations,
               SUM(machine_failure) AS observed_failures,
               AVG(machine_failure) AS observed_failure_rate,
               COUNTIF(elevated_risk) AS elevated_risk_observations,
               AVG(failure_probability) AS mean_failure_probability
        FROM `{config.dataset_id}.observations`
        GROUP BY machine_type
    """
    client.create_table(view, exists_ok=True)
    client.update_table(view, ["view_query"])
    print(f"Dataset, table and view ready: {config.dataset_id}")


if __name__ == "__main__":
    config = CloudConfig.from_environment()
    if config is None:
        raise SystemExit("Set GOOGLE_CLOUD_PROJECT, BQ_DATASET and BQ_LOCATION first.")
    setup(config)
