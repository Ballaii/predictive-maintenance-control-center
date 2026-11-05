# Cloud demonstration status

The application was deployed to Cloud Run and verified through an authenticated proxy.
Browser checks covered predictions, policy switching, CSV download and analytics.
BigQuery contains 10,000 scored observations; the deployed runtime query returned 339
recorded failures and 132 elevated-risk observations under the High precision policy.
The Looker Studio report, machine-type filter, percentage formatting and report link from
the deployed application were confirmed during the supervised walkthrough.

Actual cloud Workbench execution has not been performed. Its compatible notebook was
executed locally. The cloud demonstration is temporary; service availability and access
can change after assessment. No permanent public endpoint is promised by this repository.

Account-specific project IDs, runtime identities, report links, billing details, raw browser
captures and local account paths are intentionally omitted from this public copy.
Use your own cloud settings from .env.example and follow cloud_deployment.md. Environment
variables must be exported explicitly; .env files are not loaded automatically.