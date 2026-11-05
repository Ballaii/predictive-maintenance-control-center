# Checkpoint reports and requirement compliance

**Supervised deployment update:** private Cloud Run revision maintenance-control-center-00001-7rg
is deployed. Actual browser checks through an authenticated proxy verified manual prediction,
policy switching, CSV upload/download and analytics; direct unauthenticated access returns 403.
See docs/cloud_progress.md. BigQuery access from Cloud Run, the Looker dashboard and its deployed-app link are now verified. Workbench cloud execution remains unperformed.

**November 5 container update:** Linux image built and verified under 1 CPU / 1 GiB, including
healthy startup on a custom PORT, 10,000-row Windows/Linux inference parity under both policies,
five Linux page smoke checks and real browser prediction/upload/download/navigation checks.
The earlier Docker blocker below is historical and resolved. See docs/container_verification.md.
Cloud authentication, resource setup and deployment remain pending the supervised session.

**Current update: probability profile 1.1.0.** The dashboard now uses calibrated failure
probabilities and offers High precision / Balanced F1 policies. The original experiment below
is preserved as historical evidence. Current verification: 71 passed, 0 failed, 0 skipped.
See docs/probability_alignment.md for commands, measured policy results, browser verification
and the explicit reused-holdout limitation. Cloud work remains the final user-supervised step.

Local development completed on November 4, 2026. Cloud resources were not created.
Workspace: YOUR_PROJECT_DIRECTORY.

## Checkpoint 1: repository research and ML foundation

**A. Completed work:** audited all reference code cells and artifacts; executed the original
notebook unchanged; validated the official dataset; implemented deterministic preprocessing,
60/20/20 splits, baseline/LR/RF models, training-internal calibration candidates, validation-only
threshold/model selection, independent evaluation, persistence and shared inference.

**B. Important files:** src/{config,data_loader,preprocessing,train,evaluate,inference}.py;
models/{selected_model.joblib,metadata.json,input_schema.json}; artifacts/{dataset_report.json,
split_membership.csv,frozen_selection.json,evaluation.json,test_metrics.csv,feature_importance.json};
docs/{reference_audit,methodology,evaluation_report}.md. Original reference checkout remains separate.

**C. Commands executed** (application root, PowerShell):

```powershell
uv python install 3.11
uv venv --python 3.11 .venv
uv pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m src.data_loader
.\.venv\Scripts\python.exe -m src.train
.\.venv\Scripts\python.exe scripts/reproduce_reference.py
.\.venv\Scripts\python.exe scripts/export_reports.py
.\.venv\Scripts\python.exe -m pytest -q --tb=short
```

**D. Verification:** initial ML suite 41 passed, 0 failed, 0 skipped. Original published
four-decimal metrics reproduced exactly. Revised experiment selected RF at 0.51; test AP
0.7426, ROC-AUC 0.9608, precision 0.9259, recall 0.3676, F1 0.5263. TN=1930, FP=2, FN=43,
TP=25. Pipeline save/reload predictions matched exactly. Training/validation/test failures
203/68/68, with disjoint UDI membership.

**E. Limitations:** synthetic data, small failure support, 27 label/subtype disagreements,
uncalibrated selected score, no external validation. No future failure horizon. Original
reference threshold contamination retained only for separate reproduction.

**F. Next:** working dashboard and real browser verification, covered below.

## Checkpoint 2: dashboard implementation

**A. Completed work:** four pages, actual historical observations/scores, partition/type/label
filters, UDI search, sorting, charts, manual inference with range warnings, bounded strict
CSV upload/download, evaluation/calibration/importance, optional honest cloud status.

**B. Important files:** app.py, src/ui.py, views/*.py, .streamlit/config.toml,
tests/test_dashboard_smoke.py, output/playwright/ screenshots and state snapshots.
The suggested pages/ layout was changed to views/ after a real cold-navigation failure.

**C. Commands executed:**

```powershell
.\.venv\Scripts\python.exe scripts/start_app.py
Invoke-WebRequest http://127.0.0.1:8080/_stcore/health
.\.venv\Scripts\python.exe -m pytest -q --tb=short --junitxml=artifacts/test-results.xml
npx --yes --package @playwright/cli playwright-cli -s=maintenance open http://127.0.0.1:8080/risk_predictor --headed
npx --yes --package @playwright/cli playwright-cli -s=maintenance snapshot --filename=output/playwright/cold-deep-link-ready.yml
# Subsequent CLI clicks, fills, uploads, downloads, desktop/mobile resizing and screenshots
# are retained as resulting snapshots and files in output/playwright/.
```

**D. Verification:** final automated suite 58 passed, 0 failed, 0 skipped. Health returned
HTTP 200 and `ok`. Real Chromium manual prediction returned a score/category and inputs;
wear=500 triggered a training-range warning. A three-row CSV uploaded and downloaded; its
three scores exactly matched direct inference. Target-containing CSV rejected with missing/
extra column error. Test filter displayed 2000 records/68 failures. Invalid UDI search displayed
an empty state and N/A rate. Analytics and no-credentials Cloud Analytics rendered. Desktop
1440x1000 and mobile 390x844 captured; mobile overview/cloud document width equaled 390.

**Failures investigated and resolved:** initial dashboard suite 3 failed/54 passed because
PyArrow 26 required NumPy 2. Pinned PyArrow 17 with reference-compatible NumPy 1.26.4; full
suite then passed. Cold direct links in Streamlit 1.40 could bypass the shared shell or show
a page-not-found modal. Moved page modules to views/, updated to Streamlit 1.50, restarted
the server, and verified a cold direct link with correct app title, navigation and predictor.

The finish reviewer identified caption opacity reducing essential caveat contrast. Setting
caption opacity to 1 retained the specified #b3c2d4 text color; desktop/mobile recaptures and
computed styles confirmed the correction. The reviewer scored that single finding resolved.

**E. Limitations:** no real Google Cloud integration tested. During direct subpage loading,
Streamlit emitted two transient 404s for subpath health/host-config probes before successfully
using the app root and rendering. No resulting application exception was observed. Browser
checks are documented manual automation evidence, not an added end-to-end regression suite.

**F. Next:** container execution on a machine with Docker, followed by manual cloud setup.

## Checkpoint 3: cloud preparation (initial report; local container verification subsequently completed)

**A. Completed work:** Dockerfile, non-root runtime, port-aware startup, healthcheck, narrow
build context, Windows/Linux dependency locks; ADC-based BigQuery dataset/table/view creation,
explicit replacement upload, bounded summary query, SQL examples, Looker setup and cleanup
guide. Workbench notebook reuses the local methodology and was executed locally.

**B. Important files:** Dockerfile, .dockerignore, requirements-{windows,linux}.lock,
scripts/start_app.py, cloud/{config,analytics,bigquery_setup,bigquery_upload}.py,
cloud/queries/*.sql, cloud/vertex_training.ipynb, docs/cloud_deployment.md.

**C. Commands executed:**

```powershell
uv pip compile requirements.txt --python-version 3.11 --python-platform x86_64-unknown-linux-gnu --output-file requirements-linux.lock --quiet
uv pip freeze --exclude-editable | Set-Content -Encoding utf8 requirements-windows.lock
uv pip install --no-deps -e .
.\.venv\Scripts\python.exe scripts/create_workbench_notebook.py
.\.venv\Scripts\python.exe -c "import nbformat; from nbclient import NotebookClient; from pathlib import Path; p=Path('cloud/vertex_training.ipynb'); n=nbformat.read(p,as_version=4); NotebookClient(n,timeout=300,kernel_name='python3',resources={'metadata':{'path':str(Path.cwd())}}).execute(); nbformat.write(n,'artifacts/workbench-local-executed.ipynb'); print('Workbench-compatible notebook executed locally successfully')"
.\.venv\Scripts\ruff.exe check . --output-format concise
```

**D. Verification:** entrypoint binds 0.0.0.0:8080 and health responds. Local notebook executed
all cells, loading the completed model without retraining and exporting results. BigQuery mock
tests verify schema, WRITE_TRUNCATE, explicit result waiting, optional configuration and query
byte limit. Editable package installation and Ruff checks passed. Initial coverage run measured
75% source/cloud statement coverage (57-test run); full offline training was also executed
outside that coverage session. Warnings: Google client Python 3.11 future support notice and
upstream matplotlib/pyparsing deprecations; notebook emitted a Windows event-loop fallback warning.

The runtime PORT contract was also exercised with `$env:PORT = '8097'` and the same entrypoint.
Its /_stcore/health returned HTTP 200/ok. Only that temporary validation server was stopped;
the dashboard remains on port 8080. Final `uv pip check` passed after reinstalling editable
package metadata for the Streamlit version change. Python compileall and Ruff checks passed.

**E. Limitations:** Docker and Podman were not found. `wsl --list --quiet` reported WSL is not
installed. Actual Linux image build/run and memory profiling are unverified. No Docker build,
image digest, container health result or container success is claimed.

**F. Next:** install/start Docker with its required Windows virtualization support and run
the documented local container checks. Only then proceed to the guided deployment.

## Checkpoint 4: initial pre-deployment record (historical; superseded by cloud_progress.md)

**A. Completed:** concrete commands and account, IAM, cost, verification and cleanup procedures prepared.

**B. Files:** docs/cloud_deployment.md and cloud utilities above.

**C. Commands executed:** none against Google Cloud. No API enablement, authentication,
billing changes, resource creation, public access or deployment has been performed.

**D. Verification:** no real URL, project, BigQuery dataset or Looker report exists for this project yet.

**E. Limitations:** user's actual project/region/permissions/trial balance are not yet verified.
The brief and user's manual-deployment preference require a guided session at this boundary.

**F. Next:** review trial/project/region together, then approve each concrete resource operation.

## Checkpoint 5: final submission (partial)

**A. Completed:** local deliverable, measured evaluation, automated checks, browser evidence,
documentation, source attribution, AI disclosure and demo outline.

**B. Files:** README.md, NOTICE, LICENSE.reference, docs/*.md, artifacts/test-results.xml,
artifacts/reference_reproduction/, artifacts/figures/, models/, tests/.

**C. Verification commands:** pytest and Ruff above, browser downloaded-score comparison,
dependency locks, model/source inspection. Local Git initialization preserves the new application
separately from the reference repository; no remote publication is required.

**D. Result:** local project is demonstrable. Cloud submission evidence remains pending.

Submission packaging command: `.\.venv\Scripts\python.exe scripts/package_submission.py`.
The explicit allowlist packages source, official CSV, model, reports, notebook evidence and
reference sources without .venv, .git, credentials or browser caches. ZIP CRC and SHA256
checks are recorded in the adjacent submission/ directory. Repackage after changing files.

**E. Limitations:** no claim of full assignment completion until actual container and required
cloud demonstrations have passed. Institutional AI disclosure details have not been supplied.

**F. Next:** Docker verification, guided cloud deployment, actual cloud/Looker checks, then
rerun final checks and update this report with real deployment evidence.

## Requirement compliance

| Requirement | Status | Evidence / remaining work |
|---|---|---|
| Reference audit and attribution | Completed | reference_audit.md, LICENSE.reference, NOTICE |
| Independent reference reproduction | Completed | executed notebook and matching metrics |
| Official data acquisition and quality report | Completed | checksum, dataset_report.json |
| Six allowed predictors; no failure-mode leakage | Completed | allowlist and tests |
| Stratified train/validation/test | Completed | 6000/2000/2000, UDI membership and tests |
| LR, RF, majority baseline | Completed | executed training and measured metrics |
| Validation-only threshold/model selection | Completed | frozen_selection.json before test evaluation |
| Probability/calibration assessment | Completed locally | calibrated RF probability artifact, Brier/log loss/reliability; original score model preserved |
| Required metrics and curves | Completed | evaluation.json, test_metrics.csv, figures and UI |
| Feature importance and limitations | Completed | impurity, test permutation and explanation |
| Saved complete model/schema/metadata | Completed | models/ and serialization tests |
| Four functional dashboard pages | Completed locally | AppTest and browser evidence |
| Manual inference and invalid/range handling | Completed | tests and browser checks |
| CSV upload and prediction download | Completed | bounded parser; actual downloaded scores verified |
| Responsive technical interface | Completed locally | desktop/mobile captures, no mobile document overflow |
| Honest no-credentials behavior | Completed | no cloud calls at startup; mocked unavailable-credentials check |
| Automated tests | Completed | 71 passed, 0 failed, 0 skipped |
| Windows setup and reproducibility | Completed | Python 3.11, pins/locks, README |
| Docker configuration and local execution | Completed locally | Linux image, custom PORT, health, parity, browser checks and 1 CPU / 1 GiB verification |
| BigQuery integration | Verified in cloud | 10,000 rows; deployed runtime query confirms 339 failures and 132 High precision flags |
| Looker Studio report | Verified by user | dashboard values, type filter, probability formatting and deployed-app link |
| Workbench notebook | Completed locally | all cells executed; actual cloud session unverified |
| Cloud Run deployment and prediction check | Verified in cloud | private service, authenticated proxy browser checks, predictions and CSV parity |
| Cloud cost controls and cleanup | Controls configured; cleanup pending | user configured budget alerts; private Cloud Run min 0 / max 1; cleanup after assessment |
| Documentation and demo outline | Completed locally | docs/, README, source and AI disclosures |
| Secret/source/package checks | Local review | no credentials intentionally created or bundled; deployment review remains |
| SHAP / live IoT / neural networks | Optional / intentionally omitted | unnecessary for requested first release |
| Final cloud-backed submission | Partial | requires container and real cloud verification |


