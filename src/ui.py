import json

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.config import ARTIFACTS, DEFAULT_POLICY
from src.inference import Predictor

COLORS = ["#48d3bd", "#7cafff", "#f4bd6a", "#ed8393"]


@st.cache_resource
def get_predictor() -> Predictor:
    return Predictor.load()


@st.cache_data
def get_history() -> pd.DataFrame:
    return pd.read_csv(ARTIFACTS / "historical_probabilities.csv")


def selected_policy() -> str:
    return st.session_state.get("operating_policy", DEFAULT_POLICY)


@st.cache_data
def get_report(name: str) -> dict:
    return json.loads((ARTIFACTS / name).read_text(encoding="utf-8"))


def show_chart(figure: go.Figure) -> None:
    figure.update_layout(
        template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)", colorway=COLORS,
        margin=dict(l=16, r=16, t=35, b=25), height=340,
        font=dict(color="#cbd7e6", size=13),
        legend=dict(orientation="h", y=-0.25),
    )
    st.plotly_chart(figure, use_container_width=True)


def page_heading(title: str, description: str) -> None:
    st.title(title)
    st.write(description)


def install_style() -> None:
    st.markdown("""
    <style>
    .block-container {padding-top:2rem; padding-bottom:3rem; max-width:1500px;}
    h1 {font-size:2.15rem !important; letter-spacing:-.025em;}
    h2 {font-size:1.3rem !important; margin-top:1.3rem;}
    [data-testid="stMetric"] {padding:1rem 0; border-bottom:1px solid #344458;}
    [data-testid="stMetricValue"] {font-variant-numeric:tabular-nums;}
    [data-testid="stCaptionContainer"] {color:#b3c2d4; opacity:1;}
    ::selection {background:#23665e; color:#ffffff;}
    a {text-underline-offset:3px;}
    :focus-visible {outline:2px solid #48d3bd !important; outline-offset:3px;}
    @media(max-width:640px) {.block-container {padding-top:1rem;} h1 {font-size:1.7rem !important;}}
    </style>
    """, unsafe_allow_html=True)
