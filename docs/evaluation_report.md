# Evaluation report

Generated from the measured artifacts/evaluation.json.

## Independent test metrics

| Model | Accuracy | Precision | Recall | F1 | AP | ROC-AUC | Brier | Threshold |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Majority baseline | 0.9660 | 0.0000 | 0.0000 | 0.0000 | 0.0340 | 0.5000 | 0.0340 | 0.5000 |
| Calibrated Logistic Regression | 0.9685 | 0.8571 | 0.0882 | 0.1600 | 0.3929 | 0.9034 | 0.0256 | 0.6891 |
| Random Forest | 0.9775 | 0.9259 | 0.3676 | 0.5263 | 0.7426 | 0.9608 | 0.0168 | 0.5100 |
| Calibrated Random Forest | 0.9730 | 0.8889 | 0.2353 | 0.3721 | 0.7200 | 0.9579 | 0.0165 | 0.8493 |

## Interpretation

Selected on validation data: **Random Forest**. Frozen threshold: **0.51**. The selection file was written before test evaluation. No model was refitted after evaluation.

The selected Random Forest attained validation precision 0.9167 and recall 0.3235. The calibrated alternative had a slightly lower validation Brier score but lower recall at the required precision operating point. The pre-specified ranking selected the uncalibrated forest. This original winner and its artifacts remain preserved. The dashboard now uses the separately persisted calibrated probability profile described below.

On the independent test set: TN=1930, FP=2, FN=43, TP=25. Of 68 failures, 43 were missed. High precision does not imply high failure coverage or industrial safety.

Majority-class accuracy is 0.9660 with zero failure recall. Accuracy alone is misleading. Average Precision (AP) is used throughout; it differs from trapezoidal PR area.

Only 68 failures are available in each held-out partition. Metrics and reliability bins are uncertain and no external validation has been performed. Results differ from the reference because of the separate 60/20/20 split, single category, calibration candidates, and validation-only threshold selection.

Figures: artifacts/figures/. Complete curves, calibration bins and confusion matrices: artifacts/evaluation.json. This is a synthetic condition classifier with no seven-day horizon.

## Assignment-aligned calibrated probability profile

The dashboard now uses **Calibrated Random Forest**, reconstructed from the original training split/settings. Validation and original test results matched the already recorded calibrated candidate to tolerance 1e-12. Original experiment hashes are unchanged.

The model was chosen among existing calibrated candidates using lowest validation Brier score, then log loss. Reliability diagrams supplement these proper scores; lower Brier alone does not prove better calibration. Sigmoid calibration uses three training-only folds.

| Policy / partition | Threshold | Precision | Recall | F1 | Brier | FP | FN |
|---|---:|---:|---:|---:|---:|---:|---:|
| high_precision/validation | 0.8493 | 0.9000 | 0.2647 | 0.4091 | 0.0176 | 2 | 50 |
| high_precision/test | 0.8493 | 0.8889 | 0.2353 | 0.3721 | 0.0165 | 2 | 52 |
| balanced/validation | 0.4217 | 0.7455 | 0.6029 | 0.6667 | 0.0176 | 14 | 27 |
| balanced/test | 0.4217 | 0.7273 | 0.5882 | 0.6504 | 0.0165 | 15 | 28 |

Default policy remains **High precision**, honoring the expanded brief. Its validation precision target is not guaranteed on test. **Balanced F1** is an explicit alternative, selected from the saved validation PR curve. Switching policy changes the threshold and classification, never the estimated probability.

The calibrated high-precision policy catches 16/68 test failures with 2 false alarms (52 missed). Balanced F1 catches 40/68 with 15 false alarms (28 missed). The original uncalibrated winner catches 25/68 with 2 false alarms. These are different model/policy combinations, not an across-the-board improvement.

Assignment-alignment extension after original test results were already inspected. Model and both thresholds use saved validation evidence only. Test results reuse the original held-out partition; this is not a new untouched test experiment.

The probability estimate concerns a synthetic observed operating condition; it is not a future forecast, industrial safety assurance or externally validated risk. See docs/probability_alignment.md for the full change record.
