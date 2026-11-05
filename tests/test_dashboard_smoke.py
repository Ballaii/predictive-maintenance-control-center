import pytest
from streamlit.testing.v1 import AppTest

from src.config import ROOT


@pytest.mark.parametrize("page", [
    "app.py", "views/equipment_overview.py", "views/risk_predictor.py",
    "views/model_analytics.py", "views/cloud_analytics.py",
])
def test_pages_start_without_credentials(page, monkeypatch):
    monkeypatch.delenv("GOOGLE_CLOUD_PROJECT", raising=False)
    app = AppTest.from_file(str(ROOT / page), default_timeout=30).run()
    assert not app.exception


def test_manual_prediction():
    app = AppTest.from_file(str(ROOT / "views/risk_predictor.py"), default_timeout=30).run()
    app.button[0].click().run()
    assert not app.exception
    assert any(metric.label == "Risk category" for metric in app.metric)
    assert any(metric.label == "Estimated failure probability" for metric in app.metric)


def test_policy_control_updates_overview():
    from src.ui import get_history, get_predictor

    app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=30).run()
    history = get_history()
    predictor = get_predictor()
    expected = int((history.failure_probability >= predictor.policy("balanced")["threshold"]).sum())
    app.sidebar.radio[0].set_value("balanced").run()
    assert not app.exception
    assert any("Balanced F1 policy" in caption.value for caption in app.caption)
    displayed = next(metric.value for metric in app.metric if metric.label == "Classified elevated risk")
    assert displayed == f"{expected:,}"


def test_manual_result_uses_current_policy():
    app = AppTest.from_file(str(ROOT / "views/risk_predictor.py"), default_timeout=30).run()
    app.number_input[2].set_value(220)
    app.button[0].click().run()
    probability = next(metric.value for metric in app.metric if metric.label == "Estimated failure probability")
    app.session_state["operating_policy"] = "balanced"
    app.run()
    assert not app.exception
    assert next(metric.value for metric in app.metric if metric.label == "Estimated failure probability") == probability
    assert any("Balanced F1" in caption.value for caption in app.caption)


def test_empty_overview_filter():
    app = AppTest.from_file(str(ROOT / "views/equipment_overview.py"), default_timeout=30).run()
    app.text_input[0].set_value("does-not-exist").run()
    assert not app.exception
    assert any("No observations match" in message.value for message in app.info)


def test_cloud_configuration_status(monkeypatch):
    monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", "demo-project-123")
    app = AppTest.from_file(str(ROOT / "views/cloud_analytics.py"), default_timeout=30).run()
    assert not app.exception
    assert len(app.button) == 1
    assert not app.success


def test_cloud_authentication_failure_is_recoverable(monkeypatch):
    from google.auth.exceptions import DefaultCredentialsError

    def unavailable(_config):
        raise DefaultCredentialsError("No credentials in test")

    monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", "demo-project-123")
    monkeypatch.setattr("cloud.analytics.fetch_summary", unavailable)
    app = AppTest.from_file(str(ROOT / "views/cloud_analytics.py"), default_timeout=30).run()
    app.button[0].click().run()
    assert not app.exception
    assert any("BigQuery unavailable" in message.value for message in app.error)
