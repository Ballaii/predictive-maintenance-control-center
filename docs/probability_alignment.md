# Assignment alignment: calibrated failure probabilities

## A. Completed work

The dashboard now displays **estimated failure probabilities from Calibrated Random Forest**,
including manual inference, historical exploration and CSV results. It retains the original
six predictors and classifies operating conditions without claiming a future failure horizon.
The original experiment's uncalibrated winner remains preserved for comparison.

The sidebar offers two policies using exactly the same calibrated probabilities:

| Policy | Threshold | Validation precision | Validation recall | Reused test precision | Reused test recall | Test TP / FP / FN |
|---|---:|---:|---:|---:|---:|---:|
| High precision (default) | 0.8493 | 90.00% | 26.47% | 88.89% | 23.53% | 16 / 2 / 52 |
| Balanced F1 | 0.4217 | 74.55% | 60.29% | 72.73% | 58.82% | 40 / 15 / 28 |

The default preserves the expanded brief's preference for high validation precision. The
professor's assignment row specifies no 90% precision target. Balanced F1 is therefore an
explicit alternative, exposing its greater failure coverage and additional false alarms.
Neither policy is an industrial safety standard. Lower does not imply no failure risk.

## B. Files created or modified

- src/probability_profile.py: validation-only profile plan, deterministic reconstruction,
  evidence-preservation checks and separate artifact export.
- models/probability_model.joblib and probability_metadata.json: trusted calibrated pipeline,
  feature contract, training ranges/defaults, calibration method and both thresholds.
- artifacts/probability_profile_plan.json: model/threshold decisions and original hashes.
- artifacts/probability_evaluation.json and probability_policy_metrics.csv: measured policy comparison.
- artifacts/historical_probabilities.csv: genuine observations and calibrated estimates, with partition labels.
- src/inference.py: default probability loader, original-classifier loader and explicit policy use.
- app.py, src/ui.py, views/: global policy control, probability labels and classification tradeoff.
- tests/test_probability_profile.py and updated inference/dashboard/cloud tests.
- cloud/ utilities and queries: prepared local export schema now carries failure_probability,
  classification_policy, threshold and model version. No cloud command has been executed.
- cloud/vertex_training.ipynb and its generator: same locally tested probability preparation.
- README, methodology, evaluation, limitations, architecture, deployment guide and demo outline.

The following original experiment files are unchanged, verified against their plan hashes:
evaluation.json, frozen_selection.json, split_membership.csv, historical_predictions.csv,
selected_model.joblib and metadata.json. The professor's reference checkout was not modified.

## C. Commands executed

From the application root in PowerShell:

```powershell
.\.venv\Scripts\python.exe -m src.probability_profile
.\.venv\Scripts\python.exe -m pytest -q --tb=short --junitxml=artifacts/test-results.xml
.\.venv\Scripts\ruff.exe check . --output-format concise
.\.venv\Scripts\python.exe -m compileall -q app.py src views cloud scripts tests
uv pip install --no-deps -e .
uv pip check
.\.venv\Scripts\python.exe scripts/export_reports.py
.\.venv\Scripts\python.exe scripts/create_workbench_notebook.py
.\.venv\Scripts\python.exe scripts/start_app.py
npx --yes --package @playwright/cli playwright-cli -s=probability open http://127.0.0.1:8080/risk_predictor --headed
```

The updated notebook was executed locally using nbclient, loading completed artifacts without
retraining. Its executed copy is artifacts/workbench-local-executed.ipynb. Browser automation
used actual form fills, policy clicks, CSV upload/download, navigation and desktop/mobile captures.
Archive refresh: `python scripts/package_submission.py` with the project Python environment.

## D. Verification results

- **71 tests passed, 0 failed, 0 skipped.** Existing 14 upstream warnings remain documented.
- Ruff, Python compilation and installed dependency compatibility checks passed.
- Reconstructed calibrated validation/test AP, ROC, Brier, log loss, precision, recall and full
  PR curves match the original recorded candidate to absolute tolerance 1e-12.
- Its original validation Brier is 0.0175787; reused test Brier 0.0165206 and log loss 0.0644874.
  Brier assesses both discrimination and calibration; reliability curves supplement these scores.
- Serialization/reloading, six-feature schema, actual sigmoid calibrators, probability bounds,
  policy application, unknown-policy rejection and original-evidence hashes are tested.
- Actual browser manual input for training observation UDI 78 (Type L; 298.8 K air, 308.9 K
  process; 1455 rpm; 41.3 Nm torque; 208 min wear) displays **64.38%** under both policies.
  Its category changes from Lower to Elevated when switching High precision to Balanced F1.
- A real three-row CSV uploaded and downloaded under both policies. Downloaded probabilities
  match direct inference within 1e-15 and are identical between policies. Elevated counts
  are 0 for High precision and 1 for Balanced F1. Exports include the chosen policy and threshold.
- The overview's elevated count is checked against calibrated history and the selected threshold.
  Actual browser navigation retained Balanced F1 across pages; its test filter displayed
  2,000 observations, 68 recorded failures and 55 elevated classifications (40 TP + 15 FP).
- Updated model analytics presents both validation/test policy results, active confusion matrix,
  reliability diagnostics, original comparison and an explicit test-reuse disclosure.
- Mobile analytics at 390x844 has a 390-pixel document/body width. Desktop and mobile captures
  are under output/playwright/probability-*-final.png.

## E. Known limitations and scientific scope

This is an **assignment-alignment extension after original test results were already available**.
The model is chosen among existing calibrated candidates using lowest saved validation Brier,
then log loss. The High precision threshold is the already recorded validation operating point;
Balanced F1 comes from maximum F1 on the saved validation PR curve, excluding its synthetic
terminal point. The complete plan is written before reconstructing the model. Test labels
are never used for threshold search or model fitting.

However, the held-out partition has already been inspected. These additional policy results
reuse that partition; **no new untouched test experiment or external validation is claimed**.
The probability profile is not presented as uniformly outperforming the original winner.
For example, the original uncalibrated winner caught 25 failures with 2 false alarms, whereas
the calibrated High precision policy catches 16 with 2 false alarms. Balanced F1 exchanges
more false alarms for higher recall.

Calibration uses three folds inside the original training partition, including preprocessing
inside each fold. Sigmoid calibration on synthetic data does not guarantee reliable industrial
probabilities. No maintenance schedule, future failure date, causal explanation or safety claim
is inferred. The calibration method follows the installed scikit-learn 1.4.2 API:
https://scikit-learn.org/1.4/modules/calibration.html.

Docker/WSL were unavailable at the initial probability checkpoint. The revised image was
subsequently built and verified locally on November 5; see docs/container_verification.md.
All BigQuery operations remain locally prepared/mocked. No cloud authentication, API
enablement, billable resource, public endpoint or Looker Studio report was created.

## F. Next step

The local assignment-alignment work is complete. Cloud configuration, authentication,
deployment, BigQuery initialization, Looker setup and any Workbench cloud demonstration are
reserved for the **final supervised session with the user**. Local Docker verification also
remains pending its required runtime setup. No cloud credits have been used by this change.
