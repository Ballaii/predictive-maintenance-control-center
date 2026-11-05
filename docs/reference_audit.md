# Reference audit and independent reproduction

Source: https://github.com/Edirin-Ako/predictive-maintenance-ai4i
Commit: ef563b06272bb6ad583e1719fa416174409f359f. MIT license retained as LICENSE.reference.
Inspected README, requirements, all notebook code cells, and exported metrics/importance files.

## Organization and execution

One notebook, manually supplied data directory, and static assets. No application modules,
saved model, cloud integration, input contract, automated tests, or Docker configuration.
Notebook uses relative data/ and assets/ paths: run from its project root, not notebook/.
Requirements pin the numerical stack but also install optional SHAP although it is unused.

The flow loads CSV, checks dimensions/missing values/imbalance/flag consistency, extracts the
first Product ID character, removes identifiers and failure-mode flags, splits 75/25 using
stratification and seed 42, trains calibrated LR and RF, evaluates AP/ROC, selects a threshold,
and exports curves, metrics and RF impurity importance.

## What is sound

Training pipelines fit numerical scaling/OHE within training data. LR calibration wraps the
complete pipeline with three-fold sigmoid calibration, avoiding preprocessing leakage across
calibration folds. Both classifiers use class weighting. Failure flags are removed before
fitting. AP and precision–recall analysis are appropriate for rare failures. Seed is explicit.

## Methodological limitations

1. recall_at_precision receives y_test, selects a threshold using its labels, and reports
   recall from the same data. This is an exploratory test-curve summary, not independent
   evaluation of a threshold selected on validation data. Model fitting itself does not use test labels.
2. Type and Product_Category are identical. Duplicating the same category complicates feature
   interpretation and changes the random feature subsets seen by the forest.
3. Exported PR-AUC is sklearn average_precision_score, not trapezoidal PR area. Name it AP.
4. Probability calibration is applied to LR but not evaluated; RF scores are uncalibrated.
5. No separate validation split; no confidence intervals or external validation. README plans
   mention temporal sensitivity and stratified CV, but these are not implemented as a general
   validation study. The LR calibration CV is not a separate model-selection evaluation.
6. The README's seven-day framing is unsupported by this CSV. No reliable future horizon is
   established. Business claims about reduced downtime or scheduling are not measured outcomes.
7. RF impurity importance is global association, can be biased, and is affected by correlated
   and duplicate features. It is not a causal result or an individual explanation.
8. Majority baseline, confusion matrices, default-threshold metrics, ROC plots, calibration
   diagnostics, model persistence, input validation, API/dashboard and deployment are missing.
9. There are 27 label/subtype inconsistencies. Treating them as negligible is a judgment;
   our report retains and counts them without silently rewriting labels.

## Executed reproduction

Command: `.\.venv\Scripts\python.exe scripts/reproduce_reference.py`

Original notebook cells executed unchanged in a temporary cwd containing the official CSV.
Python 3.11; pandas 2.2.2, NumPy 1.26.4, scipy 1.12.0, scikit-learn 1.4.2, matplotlib 3.8.4.
The numerical core matches the reference requirements. SHAP was not needed. A Windows Jupyter
event-loop warning was emitted but execution completed successfully.

| Model | Published AP | Reproduced AP | Published ROC-AUC | Reproduced ROC-AUC | Reproduced recall @ test-selected 90% P |
|---|---:|---:|---:|---:|---:|
| Calibrated Logistic | 0.3793 | 0.3793 | 0.8833 | 0.8833 | 0.1294 |
| Random Forest | 0.7609 | 0.7609 | 0.9664 | 0.9664 | 0.3529 |

All match to four decimals. Reference thresholds are 0.6475 and 0.58. Executed notebook,
metrics and figures are under artifacts/reference_reproduction/. These are independently
reproduced reference results, not our revised experiment's independent test performance.

## Our improvements

Six-column allowlist, strict data/input contracts, deterministic 60/20/20 split, calibrated
and uncalibrated RF candidates, training-internal calibration, validation-only selection,
frozen selection record before test inspection, independent final metrics, serialized
pipeline/schema/metadata, test permutation importance, calibration diagnostics, UI,
batch inference, meaningful tests, cloud preparation and honest integration status.
