import logging

import streamlit as st

from src.config import DEFAULT_POLICY, POLICY_LABELS
from src.ui import get_predictor, install_style

logging.basicConfig(level=logging.INFO)
st.set_page_config(page_title="Predictive Maintenance Control Center", layout="wide")
install_style()
with st.sidebar:
    st.header("Maintenance\nControl Center")
    st.caption("AI4I 2020 · Educational demonstration")
    try:
        predictor = get_predictor()
    except (FileNotFoundError, ValueError) as error:
        st.error(str(error))
        st.stop()
    st.caption(f"Model: {predictor.metadata['selected_model']}")
    st.caption(f"Version {predictor.metadata['version']} · Local artifact loaded")
    st.radio("Classification policy", list(POLICY_LABELS), format_func=POLICY_LABELS.get,
             key="operating_policy", index=list(POLICY_LABELS).index(DEFAULT_POLICY),
             help="Thresholds were selected on validation data. Probability estimates stay the same.")
    st.caption("Calibration is assessed on synthetic data. Real-world reliability is unverified.")

page = st.navigation([
    st.Page("views/equipment_overview.py", title="Equipment Overview", default=True),
    st.Page("views/risk_predictor.py", title="Failure Risk Predictor"),
    st.Page("views/model_analytics.py", title="Model Analytics"),
    st.Page("views/cloud_analytics.py", title="Cloud Analytics"),
])
with st.sidebar:
    st.divider()
    st.caption("Synthetic historical observations. No live sensors or future failure horizon.")
page.run()
