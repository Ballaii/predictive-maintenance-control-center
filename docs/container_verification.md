# Local Linux container verification

Verified November 5, 2026, Europe/Bucharest. This completes local container verification;
no cloud authentication, API enablement, billing change, resource creation or deployment occurred.

## A. Completed work

Built the existing Dockerfile successfully against requirements-linux.lock. Ran the image as
the non-root appuser with **1 CPU and 1 GiB**. Verified runtime PORT binding, Docker health,
the saved model, all historical inference, five application/page smoke checks, browser flows,
CSV download contents and resource use. No application or model correction was needed.

The validation container remains running locally at **http://localhost:8081**. Its internal
PORT is **8090**, deliberately different from the default 8080 to test runtime configuration.
The host binding is 127.0.0.1. No externally accessible cloud endpoint exists.

## B. Files and evidence

- scripts/inference_snapshot.py: record genuine model predictions from either platform.
- scripts/compare_inference_snapshots.py: validate schema/model identity and numerical/classification parity.
- artifacts/windows_inference_snapshot.json and linux_inference_snapshot.json: 10,000 observations under both policies.
- artifacts/container_inference_parity.json: bounded comparison result.
- artifacts/container_pages.json: five passed Linux page checks, zero failed.
- artifacts/container_runtime.json: actual image ID, limits, user, health, memory and URL.
- output/playwright/container-*.yml and container-*-final.png: browser evidence.
- output/playwright/container-predictions.csv: actual downloaded three-row results.

Image tag: maintenance-control-center:1.1.0. Docker-reported local image identifier:
`sha256:c307ee39eab2db3aba49b8b044f049b7f8cbd480efef0fe23906ce28cee6310b`.
Platform: linux/amd64. Local image size: 1,479,016,307 bytes. This is not a pushed registry digest.
Container: maintenance-verify-20261105. Docker Desktop 4.98.0, Engine 29.9.2.

## C. Commands executed

From the application directory in PowerShell:

```powershell
docker version
docker build --progress=plain -t maintenance-control-center:1.1.0 .
docker run -d --name maintenance-verify-20261105 --memory=1g --cpus=1 -p 127.0.0.1:8081:8090 -e PORT=8090 maintenance-control-center:1.1.0
.\.venv\Scripts\python.exe scripts/inference_snapshot.py --output artifacts/windows_inference_snapshot.json
docker cp scripts/inference_snapshot.py maintenance-verify-20261105:/tmp/inference_snapshot.py
docker exec -e PYTHONPATH=/app maintenance-verify-20261105 python /tmp/inference_snapshot.py --output /tmp/linux_inference_snapshot.json
docker cp maintenance-verify-20261105:/tmp/linux_inference_snapshot.json artifacts/linux_inference_snapshot.json
.\.venv\Scripts\python.exe scripts/compare_inference_snapshots.py --host artifacts/windows_inference_snapshot.json --container artifacts/linux_inference_snapshot.json --output artifacts/container_inference_parity.json
docker exec maintenance-verify-20261105 python -m pip check
Invoke-WebRequest http://127.0.0.1:8081/_stcore/health
docker inspect maintenance-verify-20261105 --format '{{json .State.Health}}'
docker stats --no-stream maintenance-verify-20261105
docker exec maintenance-verify-20261105 id
npx --yes --package @playwright/cli playwright-cli -s=container open http://127.0.0.1:8081/risk_predictor --headed
```

Additional browser clicks/fills/uploads/downloads and captures exercised all four destinations.
Five Linux smoke checks used Streamlit AppTest, each with a 60-second timeout and an assertion
that app.exception was empty. Files checked: app.py and each of the four views/*.py pages.
The results were written inside the container and copied to artifacts/container_pages.json.

## D. Verification results

- Build completed successfully; Linux dependencies passed pip check.
- Runtime identity: uid/gid 1000, appuser; non-root.
- Custom PORT=8090 bound successfully; host health request returned **HTTP 200 / ok**.
- Docker reported **healthy**, zero failing streak, zero restarts and OOMKilled=false.
- Model version 1.1.0, Calibrated Random Forest. Identical stored model hash on both platforms.
- Host Python 3.11.16; container Python 3.11.18; scikit-learn 1.4.2 on both.
- Across **10,000 observations and both policies**, classifications were identical. Maximum
  absolute probability difference was **1.1102230246251565e-16**, below tolerance 1e-12.
- Whole-dataset elevated counts matched: High precision 132, Balanced F1 315. These include
  training observations and are parity checks, not independent test performance claims.
- **Five Linux page smoke checks passed, zero failed.** This is separate from the previously
  completed 71-test Windows suite; no claim that all 71 tests were executed inside this image.
- Real browser manual input UDI 78 displayed 64.38% under both policies, changing Lower to
  Elevated as expected. A three-row CSV uploaded and downloaded successfully. Downloaded
  probabilities matched host inference within 1e-12, classifications matched exactly, and
  exported policy was balanced with one elevated observation.
- Model Analytics rendered original comparisons and the active policy. Cloud Analytics
  truthfully displayed not configured / no cloud request. Overview displayed real 10,000-row
  historical data and retained the chosen policy across navigation.
- After browsing and smoke checks, docker stats showed approximately **334 MiB / 1 GiB**.
  The cgroup peak was **757,682,176 bytes (approximately 723 MiB)**, including transient page
  test activity and cgroup-accounted memory. Keep initial Cloud Run memory at 1 GiB.

## E. Known limitations

This is local Docker Desktop/WSL verification, not an actual Cloud Run deployment or a
production concurrency test. Existing Streamlit use_container_width deprecation notices and
the Google client Python 3.11 future-support warning were emitted without application failure.
Direct Streamlit subpage startup emitted two transient subpath probe 404s before successful
rendering, as previously observed locally. No new model-quality or external-validation claims
follow from container parity. Existing synthetic-data and reused-holdout limitations remain.

The image is available locally; it has not been pushed to Artifact Registry. IAM, region,
Cloud Run behavior, BigQuery access, Looker report sharing and Workbench cloud execution all
remain to be verified under the user's supervision. No cloud credits were used for these checks.

## F. Next supervised step and local cleanup

Review the real Google Cloud project, account/trial status, remaining credits and expiry date.
Then follow docs/cloud_deployment.md one approved stage at a time. No billable operation or
public access change has been performed.

When finished with the local demonstration, stop this dedicated validation container:

```powershell
docker stop maintenance-verify-20261105
# Optional, after stopping and preserving evidence:
docker rm maintenance-verify-20261105
```

The built image remains available for deployment. Do not delete unrelated containers or images.
