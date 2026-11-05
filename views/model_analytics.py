import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.config import POLICY_LABELS
from src.ui import COLORS, get_predictor, get_report, page_heading, selected_policy, show_chart

page_heading("Model analytics", "Calibrated probability estimates and validation-selected classification policies.")
report = get_report("evaluation.json")
metadata = get_predictor().metadata
profile = get_report("probability_evaluation.json")
policy = selected_policy()
operating_point = metadata["policies"][policy]
st.success(f"Probability model: {metadata['selected_model']}")
st.caption(
    f"{POLICY_LABELS[policy]} threshold {operating_point['threshold']:.2%} · {operating_point['method']}. "
    "The validation precision target is not a guarantee on unseen data."
)
st.write(
    "The calibrated forest is the existing calibrated candidate with the lowest validation Brier score. "
    "Its training-internal sigmoid calibration is assessed with reliability curves, Brier score and log loss. "
    "Lower Brier alone does not prove better calibration or real-world reliability."
)
st.subheader("Classification tradeoff: same probabilities, different thresholds")
policy_columns = ["threshold", "precision", "recall", "f1", "false_positives", "false_negatives"]
policy_rows = {
    f"{POLICY_LABELS[key]} / {partition}": {column: values[partition][column] for column in policy_columns}
    for key, values in profile["policies"].items() for partition in ["validation", "test"]
}
policy_table = pd.DataFrame(policy_rows).T
st.dataframe(policy_table.style.format("{:.4f}"), use_container_width=True)
st.download_button("Download policy comparison", policy_table.to_csv(), "classification_policies.csv", "text/csv")
st.caption(
    "High precision favors fewer false alarms; Balanced F1 maximizes validation F1. "
    "Both were frozen using validation evidence. The default remains High precision. "
    "The assignment specifies no 90% precision requirement."
)
st.warning(
    "This probability profile was added after the original test results were available. "
    "It reuses the original held-out partition; these are not results from a new untouched test set. "
    "The original winner and evaluation remain preserved."
)
partitions = get_report("split_distribution.json")
st.dataframe(pd.DataFrame(partitions).T, use_container_width=True)
st.write(
    "Calibration uses three folds inside training data. Validation determines model and threshold; "
    "the original test set was evaluated after its selection was frozen. The probability artifact "
    "reconstructs an already evaluated candidate with the same training split and settings."
)
st.subheader("Original frozen experiment comparison")
st.caption("These models retain their original validation-selected high-precision thresholds; the original winner was uncalibrated Random Forest.")
partition = st.radio("Evaluation partition", ["test", "validation"], horizontal=True)
metrics = {
    name: result["test"] if partition == "test" else result["validation"]["metrics"]
    for name, result in report.items()
}
columns = ["accuracy", "precision", "recall", "f1", "average_precision", "roc_auc", "brier_score", "log_loss", "threshold"]
comparison = pd.DataFrame({name: {key: values[key] for key in columns} for name, values in metrics.items()}).T
st.dataframe(comparison.style.format("{:.4f}"), use_container_width=True)
st.caption(
    "Average Precision summarizes the precision–recall curve; it is not trapezoidal PR area. "
    "A majority prediction is already about 96.6% accurate because failures are rare. "
    "Lower Brier score and log loss are better; they depend on both calibration and discrimination."
)
st.download_button("Download metric comparison", comparison.to_csv(), "model_comparison.csv", "text/csv")
left, right = st.columns(2)
with left:
    st.subheader("Precision–recall curves")
    figure = go.Figure()
    for index, (name, values) in enumerate(metrics.items()):
        curve = values["pr_curve"]
        figure.add_trace(go.Scatter(x=curve["recall"], y=curve["precision"], mode="lines", name=name,
                                    line=dict(color=COLORS[index])))
    figure.update_layout(xaxis_title="Recall", yaxis_title="Precision")
    show_chart(figure)
with right:
    st.subheader("ROC curves")
    figure = go.Figure()
    for index, (name, values) in enumerate(metrics.items()):
        curve = values["roc_curve"]
        figure.add_trace(go.Scatter(x=curve["fpr"], y=curve["tpr"], mode="lines", name=name,
                                    line=dict(color=COLORS[index])))
    figure.update_layout(xaxis_title="False positive rate", yaxis_title="True positive rate")
    show_chart(figure)
choice = st.selectbox("Inspect model", list(metrics), index=list(metrics).index(metadata["selected_model"]))
left, right = st.columns(2)
with left:
    st.subheader("Confusion matrix")
    values = metrics[choice]
    matrix = pd.DataFrame(values["confusion_matrix"], index=["Actual no failure", "Actual failure"],
                          columns=["Predicted no failure", "Predicted failure"])
    show_chart(px.imshow(matrix, text_auto=True, color_continuous_scale="Teal"))
    st.caption(f"False positives: {values['false_positives']} · False negatives: {values['false_negatives']}")
with right:
    st.subheader("Calibration reliability")
    calibration = values["calibration"]
    figure = go.Figure(go.Scatter(x=calibration["predicted"], y=calibration["observed"], mode="lines+markers", name=choice))
    figure.add_trace(go.Scatter(x=[0, 1], y=[0, 1], mode="lines", name="Ideal agreement", line=dict(dash="dash")))
    figure.update_layout(xaxis_title="Mean predicted probability / score", yaxis_title="Observed failure fraction")
    show_chart(figure)
    st.caption("Ten quantile bins, with fewer bins for tied scores. Sparse failures make estimates uncertain.")
st.subheader(f"Active dashboard policy: {POLICY_LABELS[policy]}")
active_metrics = profile["policies"][policy][partition]
st.dataframe(pd.DataFrame(active_metrics["confusion_matrix"],
                          index=["Actual no failure", "Actual failure"],
                          columns=["Predicted no failure", "Predicted failure"]), use_container_width=True)
st.caption(f"{partition.capitalize()} false positives: {active_metrics['false_positives']} · false negatives: {active_metrics['false_negatives']}")
importance = get_report("feature_importance.json")
left, right = st.columns(2)
for container, key, title in [
    (left, "impurity", "Random Forest impurity importance"),
    (right, "permutation_test_ap_decrease", "Held-out permutation importance"),
]:
    with container:
        st.subheader(title)
        data = pd.Series(importance[key]).sort_values()
        show_chart(px.bar(x=data.values, y=data.index, orientation="h",
                          labels={"x": "Importance" if key == "impurity" else "Mean decrease in test AP", "y": "Predictor"}))
st.caption(
    "Importance describes the uncalibrated Random Forest comparison model. Correlated predictors "
    "can share importance; impurity scores can be biased. Neither chart establishes causality "
    "or explains an individual prediction. Permutation analysis is descriptive, after model freeze."
)
st.write(
    "Torque and rotational speed have the largest measured importance in both analyses. "
    "They describe mechanical load and rotation in this synthetic process. Tool wear also "
    "contributes strongly to impurity importance; air temperature has a larger role in the "
    "permutation analysis. The difference illustrates why a single importance ranking is incomplete."
)
with st.expander("Reference results and limitations"):
    st.write(
        "The reference reports LR AP 0.3793 / ROC-AUC 0.8833 and RF AP 0.7609 / ROC-AUC 0.9664, "
        "using a different 75/25 split, duplicated categories, and test-selected thresholds. "
        "Those figures are not our independent test results. See docs/reference_audit.md for reproduction."
    )
    st.write(
        "Synthetic data, 339 recorded failures, 27 label/subtype disagreements, no external validation, "
        "no documented future horizon. Live operational data and external validation are required "
        "before maintenance decisions."
    )
