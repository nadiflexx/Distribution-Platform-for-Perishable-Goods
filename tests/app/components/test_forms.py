from unittest.mock import patch

import pytest

from distribution_platform.app.components.forms import FileUploadSection


@pytest.fixture
def mock_st():
    with patch("distribution_platform.app.components.forms.st") as mock:
        yield mock


def test_render_form(mock_st):
    mock_st.file_uploader.return_value = "file_obj"

    files = FileUploadSection.render()

    assert len(files) == 6
    assert files["pedidos"] == "file_obj"

    mock_st.markdown.assert_called()
    mock_st.caption.assert_called()
    assert mock_st.file_uploader.call_count == 6


def test_validate_success():
    files = {
        "pedidos": "f",
        "clientes": "f",
        "lineas_pedido": "f",
        "productos": "f",
        "destinos": "f",
        "provincias": "f",
    }
    valid, missing = FileUploadSection.validate(files)
    assert valid is True
    assert len(missing) == 0


def test_validate_failure():
    files = {"pedidos": "f"}
    valid, missing = FileUploadSection.validate(files)

    assert valid is False
    assert "clientes" in missing
    assert len(missing) == 5
