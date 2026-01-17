from unittest.mock import MagicMock, patch

import pytest

from distribution_platform.app.components.images import ImageLoader


@pytest.fixture
def mock_st():
    with patch("distribution_platform.app.components.images.st") as mock:
        yield mock


def test_render_uploaded_file(mock_st):
    uploaded_file = MagicMock()
    uploaded_file.type = "image/png"

    ImageLoader.render(uploaded_file, width="stretch")

    mock_st.image.assert_called_once_with(uploaded_file, width="stretch")


def test_render_local_file_exists(mock_st):
    with patch("os.path.exists") as mock_exists:
        mock_exists.return_value = True

        ImageLoader.render("path/to/image.png")

        mock_st.image.assert_called_once_with("path/to/image.png", width="stretch")


def test_render_placeholder_if_not_exists(mock_st):
    with patch("os.path.exists") as mock_exists:
        mock_exists.return_value = False

        ImageLoader.render("invalid_path.png")

        mock_st.markdown.assert_called_once()
        assert "no-image" in mock_st.markdown.call_args[0][0]


def test_render_exception_handling(mock_st):
    with patch("os.path.exists", side_effect=Exception("Boom")):
        ImageLoader.render("path")

        mock_st.error.assert_called_once_with("Image Error")
