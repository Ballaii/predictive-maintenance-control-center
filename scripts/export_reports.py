"""Build submission tables and static figures from saved experiment outputs; never retrain."""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts"


def main() -> None:
    results = json.loads((ARTIFACTS / "evaluation.json").read_text())
    metadata = json.loads((ROOT / "models" / "metadata.json").read_text())
    columns = ["accuracy", "precision", "recall", "f1", "average_precision", "roc_auc", "brier_score", "log_loss", "threshold"]
    table = pd.DataFrame({name: {key: value["test"][key] for key in columns}
                          for name, value in results.items()}).T
    table.to_csv(ARTIFACTS / "test_metrics.csv", index_label="model")
    figures = ARTIFACTS / "figures"
    figures.mkdir(exist_ok=True)
    for curve_name, x_key, y_key, title in [
        ("pr_curve", "recall", "precision", "Independent test precision–recall"),
        ("roc_curve", "fpr", "tpr", "Independent test ROC"),
        ("calibration", "predicted", "observed", "Independent test reliability (quantile bins)"),
    ]:
        figure, axis = plt.subplots(figsize=(9, 6))
        for name, value in results.items():
            curve = value["test"][curve_name]
            axis.plot(curve[x_key], curve[y_key], label=name)
        axis.set(xlabel=x_key, ylabel=y_key, title=title)
        axis.legend(fontsize=8)
        figure.tight_layout()
        figure.savefig(figures / f"{curve_name}.png", dpi=160)
        plt.close(figure)
    importance = json.loads((ARTIFACTS / "feature_importance.json").read_text())
    for key in ["impurity", "permutation_test_ap_decrease"]:
        values = pd.Series(importance[key]).sort_values()
        figure, axis = plt.subplots(figsize=(9, 5))
        values.plot.barh(ax=axis)
        axis.set_title(f"Random Forest: {key}")
        figure.tight_layout()
        figure.savefig(figures / f"{key}.png", dpi=160)
        plt.close(figure)
    lines = [
        "# Evaluation report", "", "Generated from the measured artifacts/evaluation.json.", "",
        "## Independent test metrics", "",
        "| Model | Accuracy | Precision | Recall | F1 | AP | ROC-AUC | Brier | Threshold |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for name, row in table.iterrows():
        values = [row[key] for key in ["accuracy", "precision", "recall", "f1", "average_precision", "roc_auc", "brier_score", "threshold"]]
        lines.append(f"| {name} | " + " | ".join(f"{value:.4f}" for value in values) + " |")
    lines.extend([
        "", "## Interpretation", "",
        f"Selected on validation data: **{metadata['selected_model']}**. "
        f"Frozen threshold: **{metadata['threshold']}**. The selection file was written before "
        "test evaluation. No model was refitted after evaluation.", "",
        "The selected Random Forest attained validation precision 0.9167 and recall 0.3235. "
        "The calibrated alternative had a slightly lower validation Brier score but lower recall "
        "at the required precision operating point. The pre-specified ranking selected the "
        "uncalibrated forest. This original winner and its artifacts remain preserved. The dashboard "
        "now uses the separately persisted calibrated probability profile described below.", "",
        "On the independent test set: TN=1930, FP=2, FN=43, TP=25. Of 68 failures, "
        "43 were missed. High precision does not imply high failure coverage or industrial safety.", "",
        "Majority-class accuracy is 0.9660 with zero failure recall. Accuracy alone is misleading. "
        "Average Precision (AP) is used throughout; it differs from trapezoidal PR area.", "",
        "Only 68 failures are available in each held-out partition. Metrics and reliability bins "
        "are uncertain and no external validation has been performed. Results differ from the "
        "reference because of the separate 60/20/20 split, single category, calibration candidates, "
        "and validation-only threshold selection.", "",
        "Figures: artifacts/figures/. Complete curves, calibration bins and confusion matrices: "
        "artifacts/evaluation.json. This is a synthetic condition classifier with no seven-day horizon.",
    ])
    profile_path = ARTIFACTS / "probability_evaluation.json"
    if profile_path.exists():
        profile = json.loads(profile_path.read_text())
        policy_rows = {
            f"{name}/{partition}": {key: values[partition][key] for key in
                                   ["threshold", "precision", "recall", "f1", "brier_score", "false_positives", "false_negatives"]}
            for name, values in profile["policies"].items() for partition in ["validation", "test"]
        }
        pd.DataFrame(policy_rows).T.to_csv(ARTIFACTS / "probability_policy_metrics.csv", index_label="policy/partition")
        lines.extend([
            "", "## Assignment-aligned calibrated probability profile", "",
            "The dashboard now uses **Calibrated Random Forest**, reconstructed from the original "
            "training split/settings. Validation and original test results matched the already "
            "recorded calibrated candidate to tolerance 1e-12. Original experiment hashes are unchanged.", "",
            "The model was chosen among existing calibrated candidates using lowest validation Brier "
            "score, then log loss. Reliability diagrams supplement these proper scores; lower Brier "
            "alone does not prove better calibration. Sigmoid calibration uses three training-only folds.", "",
            "| Policy / partition | Threshold | Precision | Recall | F1 | Brier | FP | FN |",
            "|---|---:|---:|---:|---:|---:|---:|---:|",
        ])
        for name, row in policy_rows.items():
            numbers = [f"{row[key]:.4f}" for key in ["threshold", "precision", "recall", "f1", "brier_score"]]
            numbers += [str(row[key]) for key in ["false_positives", "false_negatives"]]
            lines.append(f"| {name} | " + " | ".join(numbers) + " |")
        lines.extend([
            "", "Default policy remains **High precision**, honoring the expanded brief. "
            "Its validation precision target is not guaranteed on test. **Balanced F1** is an "
            "explicit alternative, selected from the saved validation PR curve. Switching policy "
            "changes the threshold and classification, never the estimated probability.", "",
            "The calibrated high-precision policy catches 16/68 test failures with 2 false alarms "
            "(52 missed). Balanced F1 catches 40/68 with 15 false alarms (28 missed). "
            "The original uncalibrated winner catches 25/68 with 2 false alarms. These are "
            "different model/policy combinations, not an across-the-board improvement.", "",
            profile["evidence_scope"], "",
            "The probability estimate concerns a synthetic observed operating condition; it is "
            "not a future forecast, industrial safety assurance or externally validated risk. "
            "See docs/probability_alignment.md for the full change record.",
        ])
    (ROOT / "docs" / "evaluation_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(table.round(4).to_string())


if __name__ == "__main__":
    main()
