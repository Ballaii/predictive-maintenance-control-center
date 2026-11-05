# Guided cloud deployment and cost controls

**Status: supervised setup in progress; private Cloud Run application deployed and verified.**
Billing/API setup, service-account/repository creation and image upload succeeded. Browser
verification through an authenticated proxy passed. BigQuery, Looker and Workbench cloud
steps remain pending. See docs/cloud_progress.md for the actual evidence.
The user requested a manual walkthrough to preserve their $300 trial credits. Run one stage
together, verify its result, and only then continue. Local application operation needs no cloud.
The assignment brief requires explicit approval before enabling services, creating paid
resources, changing billing or public deployment. These procedures are reviewable preparation.

## 1. Inspect the account before changing anything

In the Google Cloud Console verify the signed-in account, trial remaining balance and expiry,
whether the account is still a trial or has been upgraded, and the intended project. Do not
upgrade billing simply to proceed. Do not paste secrets into this repository or chat.

Create a small project-scoped budget and email alerts, for example a $5 demonstration budget
with notifications at 50%, 80% and 100%. This is a proposed target, not an estimated charge.
Alerts-only budgets are not spending caps. If a spend-cap option is available, inspect its
actual service coverage, enforcement delays and account eligibility; do not assume it covers
Cloud Run, storage, notebooks or BigQuery. Check billing after each demonstration session.

Choose one Cloud Run/Artifact Registry region supported by the account and keep them together.
Choose a BigQuery location deliberately (for example EU for an EU demonstration); it cannot
be casually changed after creation. Check current pricing and trial eligibility before accepting.
No guarantee of zero cost is made.

## 2. Verify the container locally first

Docker Desktop and WSL are now running. Image maintenance-control-center:1.1.0 passed local
Linux verification on November 5. The existing validation container is available at
http://localhost:8081 (internal PORT=8090). See docs/container_verification.md for the actual
image identifier, resource limits and results. To reproduce on a separate free host port,
run PowerShell from the application root:

```powershell
docker version
docker build -t maintenance-control-center:1.1.0 .
docker run --rm --name maintenance-demo -p 127.0.0.1:8080:8080 -e PORT=8080 --memory=1g --cpus=1 maintenance-control-center:1.1.0
# In another PowerShell window:
Invoke-WebRequest http://localhost:8080/_stcore/health
docker stats --no-stream maintenance-demo
```

Open http://localhost:8080. Verify all pages, manual prediction, CSV upload/download and no-cloud
status. Measure memory during analytics and upload, then select Cloud Run memory with headroom.
The initial deployment below retains 1 GiB. Local checks, including an additional page-test
process, reached a cgroup memory peak of approximately 723 MiB; this is not a concurrency load test.
The container listens on 0.0.0.0 and PORT (default 8080), runs as appuser and does not train.

## 3. Select the real project and enable only required APIs

Install/authenticate the Google Cloud CLI locally, or adapt commands in Cloud Shell. The
following examples are PowerShell. Replace placeholders with values reviewed together:

```powershell
$cloudProject = 'YOUR_REAL_PROJECT_ID'
$cloudRegion = 'YOUR_CHOSEN_REGION'
$cloudDataset = 'maintenance_demo'
$cloudLocation = 'EU'
$cloudService = 'maintenance-control-center'
$cloudRepository = 'maintenance-demo'
gcloud auth login
gcloud config set project $cloudProject
gcloud projects describe $cloudProject
# Only after reviewing account/project and approving API enablement:
gcloud services enable run.googleapis.com artifactregistry.googleapis.com bigquery.googleapis.com --project $cloudProject
```

The local-build route avoids Cloud Build. Cloud Shell/source builds are an alternative only
if local Docker cannot be made available; review build/storage charges before choosing that route.

## 4. Dedicated runtime identity and image registry

Create a runtime service account with no project-wide data-write permission. The deployment
operator needs authority to deploy Cloud Run, push images and act as this service account;
use scoped roles such as Cloud Run Admin, Artifact Registry Writer on the chosen repository,
and Service Account User on the chosen identity. Do not grant Owner/Editor to the app.

```powershell
gcloud iam service-accounts create maintenance-runtime --display-name 'Maintenance dashboard runtime' --project $cloudProject
$runtimeIdentity = "maintenance-runtime@${cloudProject}.iam.gserviceaccount.com"
gcloud artifacts repositories create $cloudRepository --repository-format=docker --location=$cloudRegion --project=$cloudProject
gcloud auth configure-docker "${cloudRegion}-docker.pkg.dev"
$cloudImage = "${cloudRegion}-docker.pkg.dev/${cloudProject}/${cloudRepository}/control-center:1.1.0"
docker tag maintenance-control-center:1.1.0 $cloudImage
docker push $cloudImage
```

Registry image storage can persist after Cloud Run is deleted. Retain only the required version.

## 5. Deploy privately and verify

Review configuration and billing estimate before running:

```powershell
gcloud run deploy $cloudService --image=$cloudImage --region=$cloudRegion --project=$cloudProject --service-account=$runtimeIdentity --port=8080 --cpu=1 --memory=1Gi --min-instances=0 --max-instances=1 --concurrency=10 --timeout=900 --cpu-throttling --no-allow-unauthenticated
gcloud run services describe $cloudService --region=$cloudRegion --project=$cloudProject --format='value(status.url)'
gcloud run services proxy $cloudService --region=$cloudRegion --project=$cloudProject --port=8090
```

Open http://localhost:8090 while the authenticated proxy is running. Verify navigation,
manual inference, CSV inference and analytics. Record the actual service URL, image digest,
region, memory and deployed revision. A service description alone is not a prediction test.
Inspect logs if startup fails; do not repeatedly rebuild without diagnosing the cause.

Streamlit uses WebSockets. Open sessions keep requests active and can keep instances billable;
minimum instances zero does not make an actively connected dashboard idle. Close demonstration
tabs when finished. The 900-second timeout can disconnect long sessions; refresh/reconnect as
needed. No cross-instance shared session state is required for this single-instance demo.
Maximum instances constrains scaling, not the total bill or all platform activity.

If the professor needs a public URL, approve that separately before granting public invocation:

```powershell
# Public access is optional; execute only after explicit approval:
gcloud run services add-iam-policy-binding $cloudService --region=$cloudRegion --project=$cloudProject --member=allUsers --role=roles/run.invoker
```

Organization policy may prohibit public access. Keep the service private and demonstrate
through an authenticated route if so. Never report a public deployment until verified.

## 6. Explicit BigQuery initialization and upload

Use a dedicated assignment dataset with no unrelated data. The setup operator needs BigQuery
dataset/table creation and data editing permissions; avoid giving these privileges to the UI.
The explicit upload command **replaces** observations in the dedicated dataset using
WRITE_TRUNCATE. It must not target an existing table containing user work.

```powershell
gcloud auth application-default login
$env:GOOGLE_CLOUD_PROJECT = $cloudProject
$env:BQ_DATASET = $cloudDataset
$env:BQ_LOCATION = $cloudLocation
.\.venv\Scripts\python.exe -m cloud.bigquery_setup
.\.venv\Scripts\python.exe -m cloud.bigquery_upload
```

Setup creates the dataset, observations table and type_summary view. Upload stores 10,000
rows with the six measurements, identifiers, target, partition, calibrated failure_probability,
classification, model version/name, threshold, classification_policy and score interpretation.
The prepared export uses the default High precision policy. No upload occurs at app startup.
Verify row count is 10,000 and udi is unique using the table preview or bounded queries.
Rerunning upload replaces the snapshot rather than duplicating it.

Grant runtime identity `roles/bigquery.dataViewer` **on this dataset only**, through the dataset
Sharing/Permissions panel. Grant `roles/bigquery.jobUser` on the query billing project:

```powershell
gcloud projects add-iam-policy-binding $cloudProject --member="serviceAccount:$runtimeIdentity" --role=roles/bigquery.jobUser
gcloud run services update $cloudService --region=$cloudRegion --project=$cloudProject --update-env-vars="GOOGLE_CLOUD_PROJECT=$cloudProject,BQ_DATASET=$cloudDataset,BQ_LOCATION=$cloudLocation"
```

No downloaded service-account key is required. Cloud Run uses its attached service identity;
local tools use ADC. On Cloud Analytics, click Check BigQuery and load summary. It checks actual
access and runs a summary query with maximum_bytes_billed=10 MiB and query cache enabled.
If the limit rejects the query, inspect the estimate before raising it. Configuration alone
must not be interpreted as successful access.

Review SQL in cloud/queries/, replace the project/dataset placeholders, inspect estimated
bytes or dry-run first, then use a maximum-bytes-billed limit. Avoid scheduled queries,
automatic refresh loops, streaming ingestion and unnecessary duplicate tables.

## 7. Looker Studio manual report

1. Open Looker Studio and create a blank report. Add a BigQuery data source using the real
   project, maintenance_demo dataset and observations table (or type_summary for aggregates).
2. Verify field types: udi and counts numeric; machine_type/split/model_name dimensions;
   machine_failure numeric binary; failure_probability numeric; elevated_risk Boolean;
   classification_policy a dimension. Format failure_probability as a percentage if desired.
3. Add scorecards: record count and AVG(machine_failure), formatted as a percentage. These
   count observations, not unique machines. Never SUM(failure_probability) as a recorded failure count.
4. Add observed failures by type, estimated probability distribution, and operating-condition plots.
5. Add a partition filter. For model-performance claims select split=test; full historical
   estimates include training records. Include model version, threshold, policy and synthetic-data note.
6. Avoid short automatic refresh intervals. Review BigQuery query costs and limits associated
   with the report identity; the Python query cap does not apply to Looker-generated queries.
7. Choose report-sharing and data-credential scope deliberately. Verify access as the evaluator.
8. Set LOOKER_REPORT_URL to the actual https://lookerstudio.google.com/... URL if desired.

No programmatic report creation is claimed. Include screenshots only after verifying the real report.

## 8. Workbench demonstration only when required

cloud/vertex_training.ipynb is compatible with a Python 3.11 Jupyter kernel and imports the
same project modules. First verify it locally. If the assessment requires a cloud execution,
review the current console's Workbench options, create a small supported CPU-only instance,
enable idle shutdown, and avoid GPUs or deployed Vertex endpoints. The notebook is not needed
to run the dashboard. Resource names in the current Google documentation may differ from
the assignment's Vertex AI Workbench label; verify the service in the actual console.

Upload the project source, data, requirements and notebook without .venv or credentials.
Install dependencies in a Python 3.11 kernel and restart it if needed. Set the notebook root
to the uploaded application directory. With no model metadata present, it runs the same
training command; otherwise it loads the completed experiment without retraining. Export
metrics, model and notebook evidence once. Delete the instance and review any retained disks,
snapshots or storage after the assessment. Stopping compute is not proof all storage is gone.

## 9. Cleanup and verify costs

Close dashboard tabs and proxy sessions. Preserve the local deliverable and assessment
evidence first. After explicit approval to remove the dedicated resources:

```powershell
gcloud run services delete $cloudService --region=$cloudRegion --project=$cloudProject
gcloud artifacts repositories delete $cloudRepository --location=$cloudRegion --project=$cloudProject
# Deletes this dedicated dataset and all contained tables/views; review target first:
bq --project_id=$cloudProject rm -r -d "${cloudProject}:${cloudDataset}"
```

Delete the dedicated Workbench instance and inspect associated disks/snapshots in the console.
Review remaining resources, IAM grants, billing reports and credits after reporting has caught
up. Remove unused runtime identity only when no deployed resource needs it. Do not delete an
entire shared university project or change billing for unrelated work.

## Official sources checked during preparation

- [Cloud Run container settings](https://docs.cloud.google.com/run/docs/configuring/services/containers)
- [Cloud Run WebSockets and billing behavior](https://docs.cloud.google.com/run/docs/triggering/websockets)
- [Cloud Run autoscaling](https://docs.cloud.google.com/run/docs/about-instance-autoscaling)
- [Budget alerts](https://docs.cloud.google.com/billing/docs/how-to/budgets)
- [Spend-cap scope and limits](https://docs.cloud.google.com/billing/docs/how-to/budgets-spend-caps)
- [BigQuery cost controls](https://docs.cloud.google.com/bigquery/docs/best-practices-costs)
- [Workbench setup](https://docs.cloud.google.com/vertex-ai/docs/workbench/instances/create)

Recheck pricing, trial eligibility, console options and account limits when deploying. No
specific final charge can be promised before configuration and actual usage are known.
