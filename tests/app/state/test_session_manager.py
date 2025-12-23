from unittest.mock import patch

import pytest

from distribution_platform.app.config.constants import AppPhase, VehicleCategory
from distribution_platform.app.state.session_manager import SessionManager


# Fixture local para este archivo
@pytest.fixture
def mock_streamlit():
    with patch("distribution_platform.app.state.session_manager.st") as mock_st:
        mock_st.session_state = {}
        yield mock_st


def test_initialize_sets_defaults(mock_streamlit):
    # Asegurar estado vacío
    mock_streamlit.session_state = {}

    SessionManager.initialize()

    assert "app_phase" in mock_streamlit.session_state
    assert mock_streamlit.session_state["app_phase"] == AppPhase.SPLASH
    assert mock_streamlit.session_state["sel_cat"] == VehicleCategory.HEAVY


def test_initialize_preserves_existing(mock_streamlit):
    # Pre-setear un valor
    mock_streamlit.session_state = {"app_phase": "CUSTOM_PHASE"}

    SessionManager.initialize()

    assert mock_streamlit.session_state["app_phase"] == "CUSTOM_PHASE"
    assert "load_success" in mock_streamlit.session_state  # Los otros sí se crean


def test_get_and_set(mock_streamlit):
    mock_streamlit.session_state = {}

    SessionManager.set("test_key", "test_value")
    assert mock_streamlit.session_state["test_key"] == "test_value"

    val = SessionManager.get("test_key")
    assert val == "test_value"

    # Test default
    assert SessionManager.get("non_existent", "default") == "default"


def test_set_phase(mock_streamlit):
    mock_streamlit.session_state = {}

    SessionManager.set_phase(AppPhase.RESULTS)

    assert mock_streamlit.session_state["app_phase"] == AppPhase.RESULTS
    mock_streamlit.rerun.assert_called_once()


def test_reset_validation(mock_streamlit):
    mock_streamlit.session_state = {"truck_validated": True}
    SessionManager.reset_validation()
    assert mock_streamlit.session_state["truck_validated"] is False


def test_is_ready_to_launch(mock_streamlit):
    mock_streamlit.session_state = {"truck_validated": True, "load_success": True}
    assert SessionManager.is_ready_to_launch() is True

    mock_streamlit.session_state = {"truck_validated": False, "load_success": True}
    assert SessionManager.is_ready_to_launch() is False


def test_convenience_getters(mock_streamlit):
    data = {"id": 1}
    result = {"res": 2}
    mock_streamlit.session_state = {"selected_truck_data": data, "ia_result": result}

    assert SessionManager.get_selected_truck() == data
    assert SessionManager.get_optimization_result() == result
