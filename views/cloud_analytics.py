import os

import streamlit as st
from google.api_core.exceptions import GoogleAPIError
from google.auth.exceptions import GoogleAuthError

from cloud.analytics import fetch_summary
from cloud.config import CloudConfig
from src.ui import page_heading

page_heading("Cloud analytics", "Optional BigQuery reporting. Local predictions need no cloud connection.")
try:
    config = CloudConfig.from_environment()
except ValueError as error:
    st.error(str(error))
    st.stop()
if config is None:
    st.info("BigQuery is not configured. The local dashboard is fully available.")
    st.write("Later, configure GOOGLE_CLOUD_PROJECT, BQ_DATASET and BQ_LOCATION, then use Application Default Credentials.")
    st.caption("Dataset availability: not checked. No cloud request has been made.")
else:
    st.write(f"Configured dataset: `{config.dataset_id}` · location `{config.location}`")
    st.caption("Configuration does not confirm credentials or dataset availability.")
    if st.button("Check BigQuery and load summary"):
        try:
            result = fetch_summary(config)
            st.success("Dataset and observations table are accessible.")
            st.json(result)
        except (GoogleAPIError, GoogleAuthError, OSError, ValueError) as error:
            st.error(f"BigQuery unavailable: {error}")
            st.caption("Check credentials, dataset creation, region, and read/query permissions.")
st.subheader("Representative analytical query")
dataset_id = config.dataset_id if config else "YOUR_PROJECT.maintenance_demo"
st.code(f"""SELECT machine_type, COUNT(*) AS observations,
       AVG(machine_failure) AS observed_failure_rate,
       AVG(failure_probability) AS mean_failure_probability,
       COUNTIF(elevated_risk) AS elevated_risk_observations
FROM `{dataset_id}.observations`
GROUP BY machine_type""", language="sql")
st.caption("Display only. The summary button uses a cached-query preference and a 10 MiB maximum bytes billed limit.")
st.subheader("Looker Studio report")
report_url = os.getenv("LOOKER_REPORT_URL", "")
if report_url.startswith("https://lookerstudio.google.com/"):
    st.link_button("Open configured Looker Studio report", report_url)
else:
    st.write("No report URL configured. Connect Looker Studio to observations or type_summary after the guided cloud setup.")
st.write("Setup and cleanup instructions: docs/cloud_deployment.md. This page never creates datasets or uploads rows.")
