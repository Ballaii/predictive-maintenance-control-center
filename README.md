# Predictive Maintenance Control Center

A locally trained, condition-based failure classifier and four-page Streamlit dashboard
for a university Cloud Computing assignment. Uses the official **synthetic** AI4I 2020 data.
It classifies an observed operating condition, not a failure within a future time window.

## Current status

The dashboard now displays estimated failure probabilities from **Calibrated Random Forest**.
Calibration uses three training-only sigmoid-calibration folds. The sidebar offers High precision
(default threshold 0.8493) and Balanced F1 (0.4217), both selected from validation evidence.
Probability estimates stay unchanged when classification policy changes.

On the reused held-out partition, High precision catches 16/68 failures with 2 false alarms;
Balanced F1 catches 40/68 with 15 false alarms. These are not externally validated probabilities.
The probability profile was added after original test results were known; no fresh untouched
test experiment is claimed. See docs/probability_alignment.md and docs/evaluation_report.md.

The original experiment remains preserved: its uncalibrated RF winner at threshold 0.51 had
precision 0.9259 and recall 0.3676, missing 43/68 failures. The separately executed professor
reference notebook reproduced its published metrics exactly to four decimal places.

Cloud Run, BigQuery and Looker Studio are deployed and connected. The Linux Docker image was built and verified
locally on November 5 with a 1 CPU / 1 GiB limit, healthy startup, browser checks and Windows/Linux
prediction parity across all 10,000 observations. See docs/container_verification.md.
Supervised cloud setup has begun: the user reported successful API enablement, a dedicated
runtime service account, a private image repository and a successful image upload whose digest
matches the tested image. Private Cloud Run deployment is complete and actual browser checks
through an authenticated proxy verified predictions, policy switching, CSV download and analytics.
BigQuery storage and the deployed runtime's summary query are verified. The Looker Studio report and its link from the deployed app are verified by the user. Workbench has been executed locally only; an actual cloud Workbench session has not been performed. See docs/cloud_progress.md
for the real service URL and evidence scope.

## Sources and attribution

- [Official AI4I dataset](https://archive.ics.uci.edu/dataset/601/ai4i+2020+predictive+maintenance+dataset),
  DOI [10.24432/C5HS5C](https://doi.org/10.24432/C5HS5C), UCI, 2020, CC BY 4.0.
- [Professor-provided reference](https://github.com/Edirin-Ako/predictive-maintenance-ai4i),
  Edirin-Ako, MIT, commit ef563b06272bb6ad583e1719fa416174409f359f.
- Reference provenance, adaptation boundaries, and its license are retained in NOTICE and
  LICENSE.reference. See docs/reference_audit.md. Reference metrics are separate from ours.

## Windows setup (PowerShell)

```powershell
Set-Location "$env:USERPROFILE\Desktop\Cloud Project\predictive-maintenance-control-center"
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-windows.lock
.\.venv\Scripts\python.exe -m pip install --no-deps -e .
```

If Python 3.11 is not registered with `py`, install it first. On this machine it was installed
with `uv python install 3.11` and the environment created with `uv venv --python 3.11 .venv`.
For that uv environment, use `uv pip install -r requirements-windows.lock` instead of pip.
Portable direct pins are in requirements.txt; the Windows lock includes development tools,
while requirements-linux.lock pins container runtime dependencies. To install editable with
development dependencies in a standard Python 3.11 venv: `python -m pip install -e ".[dev]"`.

## Data and training

```powershell
.\.venv\Scripts\python.exe -m src.data_loader
# Only for a fresh experiment, before models/metadata.json exists:
.\.venv\Scripts\python.exe -m src.train
# Persist the existing calibrated candidate for probability inference (once):
.\.venv\Scripts\python.exe -m src.probability_profile
.\.venv\Scripts\python.exe scripts/export_reports.py
```

The downloader checks the official CSV checksum and schema, with recovery instructions on
failure. Original data is preserved. Existing measured artifacts are included, so training
is unnecessary to launch the dashboard. Training refuses to overwrite a completed experiment.
For a genuinely new pre-specified experiment, archive models/ and artifacts/ first. Repeated
test-driven tuning would invalidate the held-out interpretation.

## Run and test

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
# Open http://localhost:8501
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m ruff check .
# Reproduce the original notebook separately (requires adjacent reference checkout):
.\.venv\Scripts\python.exe scripts/reproduce_reference.py
```

The dashboard does not train at startup. It loads the trusted, checksummed probability artifact.
The original model remains available programmatically via Predictor.load_original_classifier().
Restart the application after replacing model files. Do not load arbitrary pickle/joblib files.
All local features work without Google credentials. `.env.example` documents optional variables;
the application reads actual environment variables and does not automatically load `.env` files.

## Dashboard

- Equipment Overview: filters, UDI search, sorting, charts and historical download. All-data
  probability estimates include training records; the partition filter exposes held-out observations.
- Failure Risk Predictor: calibrated probability estimates, manual inference, training-range
  warnings, CSV validation and download. Choose High precision or Balanced F1 in the sidebar.
- Model Analytics: measured validation/test comparison, curves, calibration, importance, limits.
- Cloud Analytics: honest optional status, explicit read/query button, SQL and report link.

Batch CSVs require exactly `Type`, `Air temperature [K]`, `Process temperature [K]`,
`Rotational speed [rpm]`, `Torque [Nm]`, `Tool wear [min]`. Download an example in the predictor.
Maximum 5 MiB and 10,000 rows; invalid input rejects the entire batch. UI categories Lower
and Elevated refer only to the selected policy threshold and are not safety standards.
Prediction CSVs include failure_probability (0–1), classification_policy, decision_threshold,
elevated_risk, risk_category and outside_training_range; probability is never relabeled from
the original uncalibrated model score.

## Container and Google Cloud

```powershell
docker build -t maintenance-control-center:1.1.0 .
docker run --rm -p 127.0.0.1:8080:8080 -e PORT=8080 --memory=1g --cpus=1 maintenance-control-center:1.1.0
Invoke-WebRequest http://localhost:8080/_stcore/health
```

The image runs as a non-root user, binds 0.0.0.0:$PORT and contains precomputed artifacts.
Linux execution and runtime-provided port binding were verified locally. The current validation
container is at http://localhost:8081, mapped to its internal PORT=8090. Cloud Run will serve
the UI; BigQuery will hold a dedicated historical/scored table and
reporting view; Looker Studio connects manually. Workbench reuses the same local training code.
There is no always-on training service, GPU, live ingestion, or endpoint dependency.

Follow **docs/cloud_deployment.md** together with the user before enabling services, creating
resources, or making anything public. Includes least-privilege identities, cost controls,
BigQuery replacement behavior, Workbench steps and cleanup. Trial credits are a ceiling, not a budget target.

## Documentation

- docs/reference_audit.md: original method, independent reproduction and weaknesses.
- docs/methodology.md: splits, calibration, thresholds, model selection and input policies.
- docs/architecture.md: data flow and component responsibilities.
- docs/evaluation_report.md: actual model results and interpretation.
- docs/probability_alignment.md: probability artifact, classification tradeoff and verification.
- docs/container_verification.md: Linux image, prediction parity, browser checks and memory evidence.
- docs/limitations.md: scientific and operational boundaries.
- docs/checkpoints.md: commands, evidence, failures, remaining work and compliance.
- docs/demo_outline.md: concise assessment demonstration.

## Submission archive

Run `.\.venv\Scripts\python.exe scripts/package_submission.py` to refresh the adjacent
submission/predictive-maintenance-control-center.zip. It includes source, data, model,
measured results and reference sources without environments, credentials or browser caches.
The archive is CRC checked and accompanied by a SHA256 digest and internal file manifest.

## Academic disclosure

This implementation and documentation were developed with Codex AI assistance. Experiments
and tests were executed locally; published and reproduced reference results are distinguished
from this project's experiment. Adapt this disclosure to the institution's specific policy,
which has not been provided. No real-world industrial validation or live telemetry is claimed.



## Public repository privacy

This public copy includes source, synthetic data, trained models and measured evaluation artifacts. Account-specific cloud records, browser captures and credentials are excluded. Cloud deployment uses your own settings; see .env.example. The private working project and submission evidence are maintained separately.
