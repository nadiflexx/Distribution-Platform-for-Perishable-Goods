"""
Main Configuration Form View
"""

import streamlit as st

from distribution_platform.app.components.cards import Card, TruckHero
from distribution_platform.app.components.displays import (
    LaunchSection,
    PageHeader,
    ValidationBadge,
)
from distribution_platform.app.components.forms import FileUploadSection
from distribution_platform.app.config.constants import AppPhase, VehicleCategory
from distribution_platform.app.services.data_service import DataService
from distribution_platform.app.services.validation_service import ValidationService
from distribution_platform.app.state.session_manager import SessionManager
from distribution_platform.config.settings import Paths
from distribution_platform.infrastructure.persistence.truck_repository import (
    TruckRepository,
)


class FormView:
    """Main configuration form."""

    def __init__(self):
        self.repository = TruckRepository()

    def render(self):
        PageHeader.render("🎯", "MISSION CONTROL", "Fleet & Cargo Configuration Center")

        col_data, col_fleet = st.columns([1, 1.8], gap="large")

        with col_data:
            Card.render("DATA INGESTION", "💾", self._render_data_section)

        with col_fleet:
            Card.render("FLEET CONFIGURATION", "🚛", self._render_fleet_section)

        # Launch section
        if SessionManager.is_ready_to_launch():
            self._render_launch_section()

    def _render_data_section(self):
        source = st.radio(
            "SOURCE",
            ["Database", "Files"],
            horizontal=True,
            label_visibility="collapsed",
        )

        files = {}
        if source == "Files":
            files = FileUploadSection.render()

        st.markdown("<div style='height: 20px'></div>", unsafe_allow_html=True)

        if st.button("⚡ SYNC DATA STREAM", type="secondary", width="stretch"):
            if source == "Database":
                if DataService.load_from_database():
                    st.rerun()
            else:
                if DataService.load_from_files(files):
                    st.rerun()

    def _render_fleet_section(self):
        if not SessionManager.get("load_success"):
            ValidationBadge.awaiting()
            return

        # Category selection
        category = st.selectbox(
            "VEHICLE CLASS",
            VehicleCategory.all(),
            index=VehicleCategory.all().index(SessionManager.get("sel_cat")),
            key="cat_selector",
        )
        SessionManager.set("sel_cat", category)

        # Render based on category
        if category == VehicleCategory.CUSTOM:
            self._render_custom_prototype()
        else:
            self._render_standard_fleet(category)

        st.markdown("<div style='height: 20px'></div>", unsafe_allow_html=True)

        # Validation button/badge
        if SessionManager.get("truck_validated"):
            ValidationBadge.success()
        else:
            if (
                st.button(
                    "🔒 VERIFY VEHICLE INTEGRITY", type="primary", width="stretch"
                )
                and ValidationService.validate_truck()
            ):
                st.rerun()

    def _render_standard_fleet(self, category: str):
        cat_key = VehicleCategory.to_key(category)
        trucks = self.repository.get_trucks(cat_key)

        # Model selection
        current_model = SessionManager.get("sel_model")
        idx = list(trucks.keys()).index(current_model) if current_model in trucks else 0

        model = st.selectbox(
            "MODEL SELECTION",
            list(trucks.keys()),
            index=idx,
            key="model_selector",
        )
        SessionManager.set("sel_model", model)

        if model:
            data = trucks[model]
            img_path = Paths.TRUCK_IMAGES[cat_key] / data["imagen"]
            current_truck = data | {"nombre": model, "imagen": str(img_path)}

            if SessionManager.get("selected_truck_data") != current_truck:
                SessionManager.set("selected_truck_data", current_truck)
                SessionManager.reset_validation()

            TruckHero.render(img_path, data)

    def _render_custom_prototype(self):
        custom_trucks = self.repository.get_trucks("custom")
        options = ["+ CREATE NEW PROTOTYPE"] + list(custom_trucks.keys())

        current = SessionManager.get("sel_custom_db")
        idx = options.index(current) if current in options else 0

        selection = st.selectbox(
            "PROTOTYPE DATABASE", options, index=idx, key="custom_selector"
        )
        SessionManager.set("sel_custom_db", selection)

        if selection == "+ CREATE NEW PROTOTYPE":
            self._render_new_prototype_form()
        else:
            data = custom_trucks[selection]
            img_path = Paths.TRUCK_IMAGES["custom"] / data.get("imagen", "default.png")
            current_truck = data | {"nombre": selection, "imagen": str(img_path)}

            if SessionManager.get("selected_truck_data") != current_truck:
                SessionManager.set("selected_truck_data", current_truck)
                SessionManager.reset_validation()

            TruckHero.render(img_path, data)

    def _render_new_prototype_form(self):
        st.markdown("<div class='new-prototype-form'>", unsafe_allow_html=True)

        col1, col2 = st.columns([1, 1.5])
        with col1:
            uploaded_img = st.file_uploader(
                "Upload Schematic",
                type=["png", "jpg"],
                label_visibility="collapsed",
            )
            if uploaded_img:
                st.image(uploaded_img, width=180)

        with col2:
            name = st.text_input("Prototype ID", value="X-1")
            cap = st.number_input("Capacity (kg)", value=1000, min_value=100)
            fuel = st.number_input(
                "Fuel Consumption (L/100km)", value=25.0, min_value=1.0
            )
            spd = st.number_input("Cruise Speed (km/h)", value=90.0, min_value=20.0)
            cost = st.number_input("Driver Cost (€/h)", value=20.0, min_value=5.0)

        st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("<div style='height: 15px'></div>", unsafe_allow_html=True)

        if st.button("💾 SAVE TO DATABASE", type="secondary", width="stretch"):
            img_filename = self.repository.save_image(uploaded_img, name)
            truck_data = {
                "capacidad": cap,
                "consumo": fuel,
                "velocidad_constante": spd,
                "precio_conductor_hora": cost,
                "imagen": img_filename,
            }
            self.repository.save_custom_truck(name, truck_data)

            full_img_path = Paths.TRUCK_IMAGES["custom"] / img_filename
            SessionManager.set(
                "selected_truck_data",
                truck_data | {"nombre": name, "imagen": str(full_img_path)},
            )
            SessionManager.set("sel_custom_db", name)
            SessionManager.reset_validation()

            st.toast("Prototype Saved Successfully", icon="✅")
            st.rerun()

    def _render_launch_section(self):
        LaunchSection.render()

        _, col_center, _ = st.columns([1, 2, 1])
        with col_center:
            st.selectbox(
                "ALGORITHM",
                ["Genetic Evolutionary", "Google OR-Tools"],
                key="algo_select",
                label_visibility="collapsed",
            )

            if st.button("🚀 INITIATE SEQUENCE", type="primary", width="stretch"):
                SessionManager.set_phase(AppPhase.PROCESSING)
