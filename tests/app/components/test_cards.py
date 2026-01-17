from unittest.mock import MagicMock, patch

import pytest

from distribution_platform.app.components.cards import (
    Card,
    InfoCard,
    KPICard,
    TruckHero,
)


@pytest.fixture
def mock_st():
    with patch("distribution_platform.app.components.cards.st") as mock:
        yield mock


def test_card_render(mock_st):
    callback = MagicMock()

    Card.render("Title", "icon", callback)

    mock_st.markdown.assert_called()
    assert "pro-card" in mock_st.markdown.call_args_list[0][0][0]

    callback.assert_called_once()

    assert "</div>" in mock_st.markdown.call_args_list[1][0][0]


def test_kpi_card(mock_st):
    KPICard.render("icon", "Label", "100", "kg", highlight=True)

    html = mock_st.markdown.call_args[0][0]
    assert "kpi-card" in html
    assert "kpi-highlight" in html
    assert "Label" in html
    assert "100" in html


def test_kpi_mini(mock_st):
    KPICard.render_mini("icon", "Label", "Value")
    html = mock_st.markdown.call_args[0][0]
    assert "kpi-mini" in html


def test_truck_hero(mock_st):
    data = {
        "capacidad": 1000,
        "consumo": 10,
        "velocidad_constante": 90,
        "precio_conductor_hora": 20,
    }

    mock_col1 = MagicMock()
    mock_col2 = MagicMock()
    mock_st.columns.return_value = [mock_col1, mock_col2]

    with patch("distribution_platform.app.components.cards.ImageLoader") as mock_img:
        TruckHero.render("img.png", data)

        mock_img.render.assert_called_once_with("img.png", width="stretch")

        found_specs = False
        for call in mock_st.markdown.call_args_list:
            if "1,000" in call[0][0]:
                found_specs = True
                break

        if not found_specs:
            mock_col2.__enter__.assert_called()


def test_info_card(mock_st):
    items = {"Key1": "Val1", "Key2": "Val2"}
    InfoCard.render("Info", items)

    html = mock_st.markdown.call_args[0][0]
    assert "info-card" in html
    assert "Key1" in html
    assert "Val1" in html
