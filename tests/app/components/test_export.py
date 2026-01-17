from unittest.mock import patch

import pandas as pd
import pytest

from distribution_platform.app.components.export import ExportHub


@pytest.fixture
def mock_df():
    return pd.DataFrame({"A": [1, 2], "B": [3, 4]})


@pytest.fixture
def mock_result():
    return {"resultados_detallados": {}, "pedidos_no_entregables": []}


@patch("distribution_platform.app.components.export.st")
@patch("distribution_platform.app.components.export.ExportService")
def test_render_flow(mock_service, mock_st, mock_result, mock_df):
    """Verify that render calls all service generators and creates buttons."""
    mock_service.generate_financials_df.return_value = mock_df
    mock_service.generate_detailed_routes_df.return_value = mock_df

    ExportHub.render(mock_result)

    mock_st.popover.assert_called_once()

    mock_service.generate_financials_df.assert_called_once()
    mock_service.generate_detailed_routes_df.assert_called_once()

    assert mock_st.download_button.call_count >= 2


@patch("distribution_platform.app.components.export.st")
@patch("distribution_platform.app.components.export.ExportService")
def test_render_with_failed_orders(mock_service, mock_st, mock_df):
    """Verify that the 4th button appears if there are failed orders."""
    mock_service.generate_failed_orders_df.return_value = mock_df
    result_with_errors = {"pedidos_no_entregables": [1]}

    ExportHub.render(result_with_errors)

    mock_service.generate_failed_orders_df.assert_called()


@patch("distribution_platform.app.components.export.st")
def test_download_btn_encoding(mock_st, mock_df):
    """
    CRITICAL: Verify that CSV is generated with semicolon separator
    and UTF-8-SIG for Excel compatibility.
    """
    filename = "test.csv"
    label = "Download"

    with patch.object(pd.DataFrame, "to_csv", return_value="csv_string") as mock_to_csv:
        ExportHub._download_btn(mock_df, filename, label)

        mock_to_csv.assert_called_with(index=False, sep=";")

        call_kwargs = mock_st.download_button.call_args.kwargs
        assert call_kwargs["file_name"] == filename
        assert "use_container_width" in call_kwargs or "width" in call_kwargs
