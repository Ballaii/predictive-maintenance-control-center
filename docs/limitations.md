# Limitations and deployment status

- Educational condition classifier trained on synthetic data, not an industrial prognostics system.
- No failure date, seven-day forecast, reliable machine identity or real-time telemetry.
- 339 positive labels and 27 overall/subtype disagreements; labels retained as supplied.
- Stratified random splits do not establish independence across real machines, sites or time.
- Validation selects thresholds; target precision can fail to generalize. Test has only 68 failures.
- The original experiment's winner is uncalibrated RF. The dashboard now uses a separately
  persisted calibrated RF candidate; calibration does not establish real-world reliability.
- The calibrated High precision policy misses 52/68 held-out failures (2 false alarms);
  Balanced F1 misses 28/68 (15 false alarms). The original winner missed 43/68 (2 false alarms).
  Lower risk is not a safety assurance.
- The probability profile is a post-initial-analysis extension. Its model and thresholds use
  saved validation evidence, but reported test results reuse the previously inspected partition.
  No new untouched test set or improvement on a fresh external dataset is claimed.
- Calibration diagnostics on synthetic observations do not replace external validation.
- Feature importance is global association and does not establish causation or explain individual rows.
- Overview includes probability estimates on training observations, labeled and filterable by partition.
- No authentication layer is built into Streamlit. Cloud Run IAM/public access must be chosen manually.
- Uploads are in-memory and bounded; the app does not execute code or load uploaded model files.
- Cloud tests use mocks. Successful mock calls do not prove real IAM, API, regional or billing setup.
- Linux Docker execution passed locally with 1 CPU / 1 GiB; Windows/Linux prediction parity,
  five page smoke checks and actual browser flows were verified. This is not a production load test.
- No cloud resource, public URL or Looker report has been created. Actual cloud integration is pending.
- Workbench-compatible notebook can run locally; an actual paid Workbench session is not verified.
- Requirements target Python 3.11 for assignment reproducibility. Plan a dependency/runtime review
  before longer-term use; the installed Google client warns about Python 3.11 support ending in 2027.

Real operational data, trustworthy temporal/machine grouping, external probability assessment,
cost-sensitive threshold selection, and qualified engineering review are necessary before
production maintenance decisions.
