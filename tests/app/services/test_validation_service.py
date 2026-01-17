from unittest.mock import MagicMock, patch

import pytest

from distribution_platform.app.services.validation_service import ValidationService


@pytest.fixture
def mock_deps():
    with (
        patch(
            "distribution_platform.app.services.validation_service.SessionManager"
        ) as sm,
        patch(
            "distribution_platform.app.services.validation_service.InferenceMotor"
        ) as im,
        patch(
            "distribution_platform.app.services.validation_service.parse_truck_data"
        ) as ptd,
        patch("distribution_platform.app.services.validation_service.rules") as rules,
        patch("streamlit.warning") as warn,
        patch("streamlit.error") as err,
        patch("streamlit.toast") as toast,
    ):
        yield sm, im, ptd, rules, warn, err, toast


def test_validate_truck_no_data(mock_deps):
    sm, _, _, _, warn, _, _ = mock_deps
    sm.get.return_value = None

    assert ValidationService.validate_truck() is False
    warn.assert_called_once()


def test_validate_truck_parse_error(mock_deps):
    sm, _, ptd, _, _, err, _ = mock_deps
    sm.get.return_value = {"some": "data"}
    ptd.return_value = (False, {"error": "Invalid format"})

    assert ValidationService.validate_truck() is False
    err.assert_called_once()
    assert "Invalid format" in err.call_args[0][0]


def test_validate_truck_inference_invalid(mock_deps):
    sm, im_class, ptd, _, _, err, _ = mock_deps

    sm.get.return_value = {"some": "data"}
    ptd.return_value = (True, MagicMock())

    mock_engine = MagicMock()
    mock_result = MagicMock()
    mock_result.is_valid = False
    mock_result.reasoning = ["[ERROR] Test fail"]

    mock_engine.evaluate.return_value = mock_result
    im_class.return_value = mock_engine

    assert ValidationService.validate_truck() is False

    err.assert_not_called()

    calls = sm.set.call_args_list
    assert any(c[0][0] == "validation_result" and c[0][1] == mock_result for c in calls)

    assert any(c[0][0] == "truck_validated" and c[0][1] is False for c in calls)


def test_validate_truck_success(mock_deps):
    sm, im_class, ptd, _, _, _, toast = mock_deps

    # Setup
    sm.get.return_value = {"some": "data"}
    ptd.return_value = (True, MagicMock())

    mock_engine = MagicMock()
    mock_result = MagicMock()
    mock_result.is_valid = True

    mock_engine.evaluate.return_value = mock_result
    im_class.return_value = mock_engine

    assert ValidationService.validate_truck() is True

    calls = sm.set.call_args_list
    assert any(c[0][0] == "truck_validated" and c[0][1] is True for c in calls)
