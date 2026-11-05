import pandas as pd
import streamlit as st

from src.config import FEATURES, NUMERIC, PHYSICAL_BOUNDS, POLICY_LABELS
from src.inference import parse_batch_csv
from src.ui import get_history, get_predictor, page_heading, selected_policy

page_heading("Failure risk predictor", "Classify an operating condition using the saved model.")
predictor = get_predictor()
metadata = predictor.metadata
policy = selected_policy()
threshold = predictor.policy(policy)["threshold"]
st.caption(
    f"{metadata['selected_model']} · {metadata['score_kind']} · "
    f"{POLICY_LABELS[policy]} classification threshold {threshold:.2%}"
)
st.write("Estimated failure probability describes this operating condition, not a future failure date.")
manual, batch = st.tabs(["Single observation", "CSV batch"])
with manual:
    with st.form("prediction"):
        equipment_type = st.selectbox("Machine type", ["L", "M", "H"])
        first, second = st.columns(2)
        values = {"Type": equipment_type}
        for index, column in enumerate(NUMERIC):
            low, high = PHYSICAL_BOUNDS[column]
            container = first if index % 2 == 0 else second
            integer = column in ["Rotational speed [rpm]", "Tool wear [min]"]
            convert = int if integer else float
            values[column] = container.number_input(
                column, min_value=convert(low), max_value=convert(high),
                value=convert(metadata["defaults"][column]), step=1 if integer else 0.1,
                help=f"Training range: {metadata['training_ranges'][column]}",
            )
        submitted = st.form_submit_button("Estimate failure risk", type="primary")
    if submitted:
        st.session_state["last_prediction_inputs"] = values
    if "last_prediction_inputs" in st.session_state:
        try:
            result = predictor.predict(pd.DataFrame([st.session_state["last_prediction_inputs"]]), policy)
            row = result.iloc[0]
            st.subheader("Last submitted observation")
            score, category = st.columns(2)
            score.metric("Estimated failure probability", f"{row.failure_probability:.2%}")
            category.metric("Risk category", row.risk_category)
            if row.elevated_risk:
                st.warning("Elevated: estimated probability meets the chosen policy threshold.")
            else:
                st.info("Lower: estimated probability is below the chosen threshold. Failures can still be missed.")
            if row.outside_training_range:
                st.warning("At least one measurement is outside the training range. Reliability is uncertain.")
            st.dataframe(result[FEATURES], hide_index=True, use_container_width=True)
        except ValueError as error:
            st.error(str(error))
    st.caption(
        "Lower and Elevated are application categories, not industrial safety standards. "
        "This model classifies an observed condition; it does not predict a failure date. "
        "Calibration on synthetic data does not establish real-world probability accuracy."
    )
with batch:
    st.write("Upload exactly the six predictor columns, without identifiers, labels, or failure-mode flags.")
    st.caption("UTF-8 CSV · maximum 5 MiB · maximum 10,000 rows · all rows must be valid")
    template = get_history()[FEATURES].head(3).to_csv(index=False)
    st.download_button("Download example CSV", template, "prediction_template.csv", "text/csv")
    upload = st.file_uploader("Predictor CSV", type=["csv"])
    if upload:
        try:
            frame = parse_batch_csv(upload.getvalue())
            results = predictor.predict(frame, policy)
            total, elevated = st.columns(2)
            total.metric("Processed observations", len(results))
            elevated.metric("Elevated risk", int(results.elevated_risk.sum()))
            if results.outside_training_range.any():
                st.warning("Some rows exceed training ranges; see outside_training_range in the results.")
            st.dataframe(results, use_container_width=True, hide_index=True,
                         column_config={"failure_probability": st.column_config.NumberColumn(
                             "Estimated failure probability (0–1)", format="%.4f")})
            st.download_button("Download predictions", results.to_csv(index=False), "predictions.csv", "text/csv")
        except ValueError as error:
            st.error(str(error))
