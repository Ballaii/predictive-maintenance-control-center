# Methodology

## Data and target

Official AI4I 2020 synthetic data, 10,000 rows. Binary Machine failure target. Six predictors:
Type plus five operating measurements. Exclude UDI, Product ID, target and all five failure
flags. No time-series forecast, future horizon, machine-identity claim or live telemetry.
CSV SHA256: dc6630cd9b1f0f853922fad78a1b6436570d3f1ec863f1dd5c4340ac56bc8a8e.

No missing values, duplicate full records, duplicate predictor rows or duplicate Product IDs
were found. Failure rate 3.39%, with 27 overall/subtype disagreements. Preserve official labels.
IQR outliers: rotational speed 418, torque 69, others zero. Retain valid extremes because
they can encode the failure mechanism. See artifacts/dataset_report.json for ranges and UDI list.

## Splits and fitting

Seed 42. First stratified split reserves 20% test; split the remaining 80% at 25% validation.
Training 6000/203 failures; validation 2000/68; test 2000/68. Save UDI membership for audit.
All preprocessing fits training records. LR uses StandardScaler and one-hot Type; RF uses
numeric passthrough and one-hot Type. No duplicate Product_Category or engineered failure flags.
Random row splits may share correlated synthetic operating regimes; independent real-machine
and temporal external validation would be necessary for deployment use.

LR uses liblinear, max_iter 5000, balanced class weights. RF uses 400 trees, balanced class
weights, seed 42, n_jobs=2; other settings are scikit-learn 1.4.2 defaults. Candidates are
majority-class DummyClassifier, sigmoid-calibrated LR, RF, and sigmoid-calibrated RF.
Calibration uses three folds inside training and includes preprocessing inside each fold's
pipeline. Quantile-binned reliability, Brier and log loss are evaluated on validation and test.
The calibrated-vs-uncalibrated RF comparison is confounded by CV ensemble training size;
it is a candidate comparison, not proof that sigmoid calibration alone changes performance.

## Pre-specified selection

For each non-dummy model use the validation PR curve to maximize recall subject to precision
>=0.90. Exclude the synthetic final PR point with no corresponding threshold. If no threshold
qualifies, select maximum validation F1. No minimum predicted-positive count is imposed;
small supports can be unstable, so operating-point support is saved and should be reviewed.
Ties follow the deterministic ascending PR threshold order.

Rank candidates by precision-target feasibility, then recall for qualifying models (F1 for
fallback models), then validation AP, then lower Brier. Save frozen_selection.json before
test predictions. Evaluate each model with its frozen validation threshold; do not choose
another threshold from test labels. No hyperparameter search or post-evaluation refit.
Baseline keeps majority-class predictions at a fixed threshold of 0.5.

## Metrics and interpretation

Accuracy, precision, recall, F1, ROC-AUC, AP, Brier, log loss, confusion matrix, FP/FN, PR/ROC
curves and calibration bins. Precision target is a validation goal, not a test guarantee.
The test recall is recall at the frozen validation-selected threshold, not a threshold
optimized to achieve 90% precision on test. AP is not trapezoidal PR area.
RF impurity and five-repeat held-out permutation importance (AP decrease) are descriptive
after model freeze, not used to tune models. Correlation can distribute importance.

## Inference contracts

Persist the entire selected estimator/pipeline, threshold, feature schema, training ranges,
defaults, seed, package versions, dataset hash and artifact hash. Only project-owned artifacts
are loaded; checksums detect accidental mismatch, not malicious replacement of both files.

Type must be L/M/H. All measurements finite; speed and wear must be integers. Application
input guardrails: air 200–500 K; process 200–600 K; speed 1–10000 rpm; torque 0.01–500 Nm;
wear 0–1000 min. These are broad educational input limits, not safety standards or validated
operating envelopes. Values outside training min/max produce warnings even within these bounds.
No missing-value imputation or silent column dropping. A CSV must have exactly six predictor
columns, unique headers, consistent row widths, UTF-8 encoding, <=5 MiB and <=10,000 rows.
No formula evaluation; strings must pass strict category/numeric checks before downloadable output.

UI risk categories: Elevated if estimated probability >= selected policy threshold, Lower
otherwise. The original RF winner remains uncalibrated and preserved as a comparison artifact.
No individual explanation or causal maintenance advice is fabricated.

## Assignment-aligned probability profile

The assignment explicitly asks for estimated failure probabilities. Among previously evaluated
calibrated candidates, choose lowest saved validation Brier score, then log loss; this selects
Calibrated Random Forest. Brier reflects calibration and discrimination, so this rule does not
prove improved calibration alone. Reliability curves are also retained and shown.

Before reconstructing the candidate, save probability_profile_plan.json containing this rule,
both thresholds, the original evidence hashes and the original-test-reuse disclosure. The
default High precision threshold is the candidate's original validation-selected threshold
(0.8493198346514657). Balanced F1 maximizes F1 on its saved validation PR curve, excluding the
synthetic terminal PR point (threshold 0.42169382344542883). Neither threshold uses test labels.

Reconstruct the existing candidate with identical seed, hyperparameters, three-fold calibration
and training UDI membership. Verify its original validation/test AP, ROC, Brier, log loss,
precision, recall and complete PR curve to tolerance 1e-12. Save probability_model.joblib,
probability_metadata.json, probability_evaluation.json and historical_probabilities.csv separately.
Verify original model, metadata, evaluation, selection, membership and historical score hashes
remain unchanged. Both policies use the same probabilities and differ only in classification.

This extension was requested after the original test outcomes were visible. All new choices
use saved validation evidence, but repeated holdout use limits confirmatory claims. Treat the
additional policy comparison as an assignment-alignment analysis on the existing holdout,
not a new pristine experiment or external validation. No test-driven threshold search is run.

Calibration API/methodology source: https://scikit-learn.org/1.4/modules/calibration.html.
