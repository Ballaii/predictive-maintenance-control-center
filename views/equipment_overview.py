import plotly.express as px
import streamlit as st

from src.config import POLICY_LABELS, TARGET
from src.ui import get_history, get_predictor, page_heading, selected_policy, show_chart

page_heading("Equipment overview", "Explore operating conditions, recorded failures, and estimated risk.")
history = get_history().copy()
predictor = get_predictor()
policy = selected_policy()
threshold = predictor.policy(policy)["threshold"]
history["elevated_risk"] = history.failure_probability >= threshold
history["classification_policy"] = policy
history["decision_threshold"] = threshold
st.caption(
    "Historical synthetic data, not a live fleet. Each row is an observation, not a unique machine. "
    "All-record probability estimates include training observations; use the test filter for held-out records."
)
type_col, label_col, split_col, search_col = st.columns([1, 1.2, 1, 1.2])
types = type_col.multiselect("Equipment type", ["L", "M", "H"], default=["L", "M", "H"])
label = label_col.selectbox("Observed failure", ["All observations", "Recorded failure", "No recorded failure"])
split = split_col.selectbox("Data partition", ["All", "test", "validation", "train"])
search = search_col.text_input("Observation ID (UDI)", placeholder="e.g. 42")
filtered = history[history.Type.isin(types)]
if label != "All observations":
    filtered = filtered[filtered[TARGET].eq(int(label == "Recorded failure"))]
if split != "All":
    filtered = filtered[filtered.split.eq(split)]
if search.strip():
    filtered = filtered[filtered.UDI.astype(str).eq(search.strip())]

observations, failures, rate, elevated = st.columns(4)
observations.metric("Observations", f"{len(filtered):,}")
failures.metric("Recorded failures", f"{int(filtered[TARGET].sum()):,}")
rate.metric("Observed failure rate", f"{filtered[TARGET].mean():.2%}" if len(filtered) else "N/A")
elevated.metric("Classified elevated risk", f"{int(filtered.elevated_risk.sum()):,}")
st.caption(f"{POLICY_LABELS[policy]} policy: Elevated means estimated probability ≥ {threshold:.2%}. Counts reflect filters.")
if filtered.empty:
    st.info("No observations match. Clear the observation ID or broaden the filters.")
    st.stop()

left, right = st.columns(2)
with left:
    st.subheader("Recorded failure distribution")
    distribution = filtered[TARGET].map({0: "No recorded failure", 1: "Recorded failure"}).value_counts()
    show_chart(px.bar(x=distribution.index, y=distribution.values,
                      labels={"x": "Observed label", "y": "Observations"}))
with right:
    st.subheader("Estimated failure probability distribution")
    show_chart(px.histogram(filtered, x="failure_probability", nbins=35,
                            labels={"failure_probability": "Estimated failure probability (0–1)"}))
left, right = st.columns(2)
with left:
    st.subheader("Torque and rotational speed")
    plot_data = filtered.assign(recorded_label=filtered[TARGET].map({0: "No failure", 1: "Failure"}))
    show_chart(px.scatter(plot_data, x="Rotational speed [rpm]", y="Torque [Nm]",
                          color="recorded_label", color_discrete_map={"No failure": "#7cafff", "Failure": "#ed8393"},
                          opacity=0.55, hover_data=["UDI", "Type"], render_mode="webgl"))
with right:
    st.subheader("Tool wear and estimated failure probability")
    show_chart(px.scatter(filtered, x="Tool wear [min]", y="failure_probability", color="Type",
                          opacity=0.55, hover_data=["UDI"], render_mode="webgl",
                          labels={"failure_probability": "Estimated failure probability (0–1)"}))
st.subheader("Operating temperature distribution")
temperature = filtered[["Air temperature [K]", "Process temperature [K]"]].melt(
    var_name="Measurement", value_name="Temperature [K]",
)
show_chart(px.histogram(temperature, x="Temperature [K]", color="Measurement", barmode="overlay", opacity=0.7))
st.subheader("Observation register")
sort = st.selectbox("Sort observations", ["Highest estimated risk", "Lowest estimated risk", "Observation ID"])
column = "UDI" if sort == "Observation ID" else "failure_probability"
table = filtered.sort_values(column, ascending=sort != "Highest estimated risk")
st.dataframe(table, hide_index=True, use_container_width=True,
             column_config={"failure_probability": st.column_config.NumberColumn(
                 "Estimated failure probability (0–1)", format="%.4f")})
st.download_button("Download filtered observations", table.to_csv(index=False), "observations.csv", "text/csv")
