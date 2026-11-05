from google.cloud import bigquery

from cloud.config import CloudConfig

MAX_QUERY_BYTES = 10 * 1024 * 1024


def fetch_summary(config: CloudConfig) -> dict:
    client = bigquery.Client(project=config.project)
    client.get_dataset(config.dataset_id)
    table = client.get_table(f"{config.dataset_id}.observations")
    sql = f"""
        SELECT COUNT(*) AS observations, SUM(machine_failure) AS failures,
               AVG(machine_failure) AS failure_rate,
               COUNTIF(elevated_risk) AS elevated_risk
        FROM `{config.dataset_id}.observations`
    """
    job = client.query(sql, location=config.location, job_config=bigquery.QueryJobConfig(
        maximum_bytes_billed=MAX_QUERY_BYTES, use_query_cache=True,
    ))
    summary = dict(next(iter(job.result())))
    return {"table_rows": table.num_rows, "summary": summary, "query_bytes_billed": job.total_bytes_billed}
