from unittest.mock import patch

import pytest

from distribution_platform.app.components.loaders import LoaderOverlay


@pytest.fixture
def mock_st():
    with patch("distribution_platform.app.components.loaders.st") as mock:
        yield mock


@pytest.fixture
def mock_components():
    with patch("distribution_platform.app.components.loaders.components") as mock:
        yield mock


def test_inject_transition_shield(mock_st):
    LoaderOverlay.inject_transition_shield()
    mock_st.markdown.assert_called_once()
    args = mock_st.markdown.call_args
    assert "Global transition shield" in args[0][0]
    assert args[1]["unsafe_allow_html"] is True


def test_static_loader(mock_st):
    LoaderOverlay.static(title="TEST", subtitle="SUBTEST")
    mock_st.markdown.assert_called_once()
    html = mock_st.markdown.call_args[0][0]
    assert "TEST" in html
    assert "SUBTEST" in html
    assert "static-loader-overlay" in html


def test_persistent_map_loader(mock_st):
    LoaderOverlay.persistent_map_loader()
    mock_st.markdown.assert_called_once()
    html = mock_st.markdown.call_args[0][0]
    assert "persistentMapLoader" in html
    assert "opacity: 1" in html


def test_inject_map_detector(mock_components):
    LoaderOverlay.inject_map_detector()
    mock_components.html.assert_called_once()
    script = mock_components.html.call_args[0][0]
    assert "<script>" in script
    assert "checkMapLoaded" in script
