from unittest.mock import patch

import pytest

from distribution_platform.app.components.displays import (
    LaunchSection,
    PageHeader,
    SectionHeader,
    Timeline,
    ValidationBadge,
)


@pytest.fixture
def mock_st():
    with patch("distribution_platform.app.components.displays.st") as mock:
        yield mock


def test_section_header(mock_st):
    SectionHeader.render("icon", "Title")
    mock_st.markdown.assert_called_once()
    html = mock_st.markdown.call_args[0][0]
    assert "section-header" in html
    assert "Title" in html


def test_page_header(mock_st):
    PageHeader.render("icon", "Title", "Subtitle")
    mock_st.markdown.assert_called_once()
    html = mock_st.markdown.call_args[0][0]
    assert "page-header" in html
    assert "Title" in html
    assert "Subtitle" in html


def test_timeline_empty(mock_st):
    Timeline.render([])
    mock_st.markdown.assert_not_called()


def test_timeline_render(mock_st):
    route = ["A", "B", "C"]
    Timeline.render(route)

    mock_st.markdown.assert_called_once()
    html = mock_st.markdown.call_args[0][0]

    # Check tags logic
    assert "ORIGIN" in html  # Start
    assert "STOP 1" in html  # Middle
    assert "RETURN" in html  # End
    assert "timeline-container" in html


def test_validation_badge_success(mock_st):
    ValidationBadge.success()
    mock_st.markdown.assert_called_once()
    assert "validation-success" in mock_st.markdown.call_args[0][0]


def test_validation_badge_awaiting(mock_st):
    ValidationBadge.awaiting()
    mock_st.markdown.assert_called_once()
    assert "awaiting-data" in mock_st.markdown.call_args[0][0]


def test_launch_section(mock_st):
    LaunchSection.render()
    assert mock_st.markdown.call_count == 2
    assert "launch-ready-badge" in mock_st.markdown.call_args_list[1][0][0]
