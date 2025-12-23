from unittest.mock import patch

import pytest

from distribution_platform.app.services.data_service import DataService


@pytest.fixture
def mock_session_manager():
    with patch(
        "distribution_platform.app.services.data_service.SessionManager"
    ) as mock:
        yield mock


def test_load_from_database_success(mock_session_manager):
    with (
        patch("distribution_platform.app.services.data_service.run_etl") as mock_etl,
        patch("streamlit.spinner"),
    ):
        mock_etl.return_value = ["order1", "order2"]

        result = DataService.load_from_database()

        assert result is True
        mock_etl.assert_called_once_with(use_database=False)
        mock_session_manager.set.assert_any_call("df", ["order1", "order2"])
        mock_session_manager.set.assert_any_call("load_success", True)
        mock_session_manager.reset_validation.assert_called_once()


def test_load_from_database_failure(mock_session_manager):
    with (
        patch("distribution_platform.app.services.data_service.run_etl") as mock_etl,
        patch("streamlit.error") as mock_error,
    ):
        mock_etl.side_effect = Exception("DB Error")

        result = DataService.load_from_database()

        assert result is False
        mock_error.assert_called_once()
        assert "DB Error" in str(mock_error.call_args[0][0])


def test_load_from_files_validation_error():
    files = {}  # Empty

    with (
        patch(
            "distribution_platform.app.components.forms.FileUploadSection.validate"
        ) as mock_validate,
        patch("streamlit.error") as mock_error,
    ):
        mock_validate.return_value = (False, ["file1"])

        result = DataService.load_from_files(files)

        assert result is False
        mock_error.assert_called_once()


def test_load_from_files_success(mock_session_manager):
    files = {"file1": "data"}

    with (
        patch(
            "distribution_platform.app.components.forms.FileUploadSection.validate"
        ) as mock_validate,
        patch("distribution_platform.app.services.data_service.run_etl") as mock_etl,
        patch("streamlit.spinner"),
    ):
        mock_validate.return_value = (True, [])
        mock_etl.return_value = ["data"]

        result = DataService.load_from_files(files)

        assert result is True
        mock_etl.assert_called_once_with(uploaded_files=files)
        mock_session_manager.set.assert_any_call("df", ["data"])


def test_load_from_files_etl_failure():
    files = {"file1": "data"}

    with (
        patch(
            "distribution_platform.app.components.forms.FileUploadSection.validate"
        ) as mock_validate,
        patch("distribution_platform.app.services.data_service.run_etl") as mock_etl,
        patch("streamlit.error") as mock_error,
    ):
        mock_validate.return_value = (True, [])
        mock_etl.side_effect = Exception("ETL Error")

        result = DataService.load_from_files(files)

        assert result is False
        mock_error.assert_called_once()
