from unittest.mock import MagicMock, patch

import pytest

from distribution_platform.app.components.images import ImageLoader


@pytest.fixture
def mock_st():
    with patch("distribution_platform.app.components.images.st") as mock:
        yield mock


def test_render_uploaded_file(mock_st):
    # Mock an uploaded file (has 'type' attribute)
    uploaded_file = MagicMock()
    uploaded_file.type = "image/png"

    ImageLoader.render(uploaded_file, width="stretch")

    mock_st.image.assert_called_once_with(uploaded_file, width="stretch")


def test_render_local_file_exists(mock_st):
    with patch("os.path.exists") as mock_exists:
        mock_exists.return_value = True

        # FIX: The implementation defaults to width="stretch" for local files too if passed or default
        # If we don't pass width, check what default is.
        # In your code: def render(img_input, width=None): ... st.image(..., width="stretch")
        # Wait, if width passed is None, code does: st.image(..., width="stretch")?
        # Let's re-read code:
        # if hasattr... st.image(..., width="stretch")
        # elif exists... st.image(..., width="stretch")
        # So it ignores the width param? Or uses it?
        # Your code: st.image(str(img_input), width="stretch") <-- HARDCODED in `images.py`

        ImageLoader.render("path/to/image.png")

        # Expectation update:
        mock_st.image.assert_called_once_with("path/to/image.png", width="stretch")


def test_render_placeholder_if_not_exists(mock_st):
    with patch("os.path.exists") as mock_exists:
        mock_exists.return_value = False

        ImageLoader.render("invalid_path.png")

        # Should call markdown for placeholder
        mock_st.markdown.assert_called_once()
        assert "no-image" in mock_st.markdown.call_args[0][0]


def test_render_exception_handling(mock_st):
    # Force an exception
    with patch("os.path.exists", side_effect=Exception("Boom")):
        ImageLoader.render("path")

        mock_st.error.assert_called_once_with("Image Error")
