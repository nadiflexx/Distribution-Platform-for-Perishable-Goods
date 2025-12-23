from unittest.mock import MagicMock, patch

import pytest

from distribution_platform.app.config.constants import VehicleCategory
from distribution_platform.app.views.form_view import FormView


@pytest.fixture
def mock_deps():
    with (
        patch("distribution_platform.app.views.form_view.st") as st,
        patch("distribution_platform.app.views.form_view.SessionManager") as sm,
        patch("distribution_platform.app.views.form_view.TruckRepository") as repo,
        patch("distribution_platform.app.views.form_view.DataService") as ds,
        patch("distribution_platform.app.views.form_view.ValidationService") as vs,
        patch("distribution_platform.app.views.form_view.FileUploadSection") as forms,
        patch("distribution_platform.app.views.form_view.Card") as card,
        patch("distribution_platform.app.views.form_view.TruckHero") as hero,
        patch("distribution_platform.app.views.form_view.LaunchSection") as launch,
    ):
        # FIX: Dynamic columns
        def columns_side_effect(spec, **kwargs):
            n = spec if isinstance(spec, int) else len(spec)
            return [MagicMock() for _ in range(n)]

        st.columns.side_effect = columns_side_effect

        yield st, sm, repo, ds, vs, forms, card, hero, launch


# --- Structure Tests ---


def test_render_structure(mock_deps):
    st, sm, _, _, _, _, card, _, launch = mock_deps
    sm.is_ready_to_launch.return_value = True

    view = FormView()
    view.render()

    assert st.columns.call_count >= 1
    assert card.render.call_count == 2
    launch.render.assert_called_once()


# --- Data Section Tests ---


def test_render_data_section_files(mock_deps):
    st, _, _, ds, _, forms, _, _, _ = mock_deps
    st.radio.return_value = "Files"
    st.button.return_value = True
    forms.render.return_value = {"file": "obj"}
    ds.load_from_files.return_value = True

    view = FormView()
    view._render_data_section()

    forms.render.assert_called_once()
    ds.load_from_files.assert_called_once()
    st.rerun.assert_called_once()


def test_render_data_section_database(mock_deps):
    st, _, _, ds, _, _, _, _, _ = mock_deps
    st.radio.return_value = "Database"
    st.button.return_value = True
    ds.load_from_database.return_value = True

    view = FormView()
    view._render_data_section()

    ds.load_from_database.assert_called_once()


# --- Fleet Section Tests ---


def test_render_fleet_awaiting(mock_deps):
    _, sm, _, _, _, _, _, _, _ = mock_deps
    sm.get.return_value = False  # load_success = False

    with patch("distribution_platform.app.views.form_view.ValidationBadge") as badge:
        view = FormView()
        view._render_fleet_section()
        badge.awaiting.assert_called_once()


def test_render_fleet_standard(mock_deps):
    st, sm, repo, _, vs, _, _, hero, _ = mock_deps

    # Mock session state
    sm.get.side_effect = (
        lambda k: True
        if k == "load_success"
        else (
            VehicleCategory.HEAVY
            if k == "sel_cat"
            else ("Truck A" if k == "sel_model" else False)
        )
    )

    # Mock user input
    st.selectbox.side_effect = [VehicleCategory.HEAVY, "Truck A"]
    repo.return_value.get_trucks.return_value = {
        "Truck A": {"imagen": "img.png", "capacidad": 1000}
    }

    # Mock validation click
    st.button.return_value = True
    vs.validate_truck.return_value = True

    view = FormView()
    view._render_fleet_section()

    hero.render.assert_called_once()
    vs.validate_truck.assert_called_once()
    st.rerun.assert_called_once()


def test_render_fleet_custom_create(mock_deps):
    st, sm, repo, _, _, _, _, _, _ = mock_deps

    sm.get.side_effect = (
        lambda k: True
        if k == "load_success"
        else (VehicleCategory.CUSTOM if k == "sel_cat" else None)
    )
    st.selectbox.side_effect = [VehicleCategory.CUSTOM, "+ CREATE NEW PROTOTYPE"]
    repo.return_value.get_trucks.return_value = {}  # Empty customs

    # Mock form inputs
    st.text_input.return_value = "NewTruck"
    st.file_uploader.return_value = "file"
    st.button.return_value = True  # Save button
    repo.return_value.save_image.return_value = "img.png"

    view = FormView()
    view._render_fleet_section()

    # Verify save logic
    repo.return_value.save_custom_truck.assert_called_once()
    st.toast.assert_called_once()


def test_render_fleet_custom_existing(mock_deps):
    st, sm, repo, _, _, _, _, hero, _ = mock_deps

    sm.get.side_effect = (
        lambda k: True
        if k == "load_success"
        else (
            VehicleCategory.CUSTOM
            if k == "sel_cat"
            else ("ExistingTruck" if k == "sel_custom_db" else None)
        )
    )

    st.selectbox.side_effect = [VehicleCategory.CUSTOM, "ExistingTruck"]
    repo.return_value.get_trucks.return_value = {"ExistingTruck": {"imagen": "e.png"}}

    view = FormView()
    view._render_fleet_section()

    hero.render.assert_called_once()


# --- Launch Section Test ---


def test_render_launch(mock_deps):
    st, sm, _, _, _, _, _, _, launch = mock_deps
    st.button.return_value = True  # Launch clicked

    view = FormView()
    view._render_launch_section()

    launch.render.assert_called_once()
    sm.set_phase.assert_called_with("PROCESSING")
