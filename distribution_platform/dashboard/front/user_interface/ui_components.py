import os
import random

import pandas as pd
import streamlit as st

from distribution_platform.config.paths import TRUCK_IMAGES
from distribution_platform.config.settings import ROUTE_COLORS
from distribution_platform.dashboard.front.inference_engine.engine import InferenceMotor
from distribution_platform.dashboard.front.knowledge_base import rules
from distribution_platform.dashboard.front.knowledge_base.rules import (
    obtain_format_validation_rules,
    parse_truck_data,
)
from distribution_platform.dashboard.front.repositories.truck_repository import (
    CAMIONES_GRANDES,
    CAMIONES_MEDIANOS,
    add_camion_personalizado,
    get_camiones_personalizados,
    save_custom_truck_image,
)
from distribution_platform.dashboard.front.user_interface.maps import SpainMapRoutes
from distribution_platform.pipelines.etl_pipeline import run_etl

# ======================================================================
#   INITIAL STATE
# ======================================================================


def init_state():
    defaults = {
        "page": "form",
        "connection_type": None,
        "df": None,
        "selected_truck_data": None,
        "ia_result": None,
        "load_success": False,
        "truck_validated": False,
        "truck_creation_in_progress": False,
        "truck_created_successfully": False,
        "selected_truck": None,
        "orders_df": None,
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


# ======================================================================
#   TITLE
# ======================================================================


def render_title():
    st.markdown(
        "<h1 class='main-title'>🚚 AI Delivery – Route Planner</h1>",
        unsafe_allow_html=True,
    )
    st.caption("Intelligent route planning for perishable products.")


# ======================================================================
#   DATA SOURCE SELECTOR
# ======================================================================


def render_connection_selector():
    st.markdown("<div class='section-card'>", unsafe_allow_html=True)
    st.subheader("1️⃣ Select Data Source")

    connection = st.radio(
        "How would you like to load the data?",
        ["Database", "Files"],
        key="connection_type",
        horizontal=True,
    )

    file_inputs = {}

    if connection == "Files":
        st.info("📄 Upload the necessary files:")
        file_inputs = {
            "clientes": st.file_uploader("dboClientes"),
            "lineas_pedido": st.file_uploader("dboLineasPedido"),
            "pedidos": st.file_uploader("dboPedidos"),
            "productos": st.file_uploader("dboProductos"),
            "provincias": st.file_uploader("dboProvincias"),
            "destinos": st.file_uploader("dboDestinos"),
        }

    st.markdown("</div>", unsafe_allow_html=True)
    return connection, file_inputs


# ======================================================================
#   DATA LOADING
# ======================================================================


def load_data(connection_type, file_inputs):
    """Load data from database or CSV files."""

    if connection_type == "Database":
        st.info("🔌 Attempting to connect to the database...")
        try:
            orders = run_etl(use_database=False)
        except Exception as e:
            st.error(f"❌ Error connecting to database:\n{e}")
            st.session_state.load_success = False
            return None
    else:
        missing = [k for k, f in file_inputs.items() if f is None]
        if missing:
            st.error("❌ Missing CSV files:\n- " + "\n- ".join(missing))
            return None

        try:
            orders = run_etl(uploaded_files=file_inputs)
        except Exception as e:
            st.error(f"❌ Error executing ETL with files:\n{e}")
            st.session_state.load_success = False
            return None

    # Validate result
    if orders is None or (hasattr(orders, "empty") and orders.empty):
        st.error("❌ ETL returned no valid data.")
        return None

    st.success(f"✅ Data loaded successfully ({len(orders)} records).")
    st.session_state.df = orders
    st.session_state.load_success = True


# ======================================================================
#   TRUCK SELECTOR
# ======================================================================


def render_truck_selector():
    st.markdown("<div class='section-card'>", unsafe_allow_html=True)
    st.subheader("2️⃣ Truck Selection")

    if not st.session_state.load_success:
        st.info("⏳ Load the data before selecting trucks.")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    st.success("📦 Data loaded. Select your truck.")
    show_trucks_selection()

    disabled = (
        st.session_state.truck_creation_in_progress
        and not st.session_state.truck_created_successfully
    )

    if st.button("✔️ Confirm Selection", disabled=disabled, type="primary"):
        # Return truck data if valid not None
        truck = validate_and_confirm_truck()
        if truck is not None:
            print("✅ Truck selected:", st.session_state.selected_truck_data)
            st.session_state.selected_truck = truck

    st.markdown("</div>", unsafe_allow_html=True)


def validate_and_confirm_truck():
    """Validate selected truck using expert system."""
    truck_data = st.session_state.selected_truck_data

    if not truck_data:
        st.error("❌ No truck has been selected.")
        return

    is_valid, result = parse_truck_data(truck_data)

    if not is_valid:
        st.error(f"❌ Error converting truck data: {result.get('error')}")
        return

    with st.spinner("🔍 Validating truck..."):
        motor = InferenceMotor(rules.obtain_rules())
        validation_result = motor.evaluate(result)

    if validation_result.is_valid:
        st.success("✅ Selected truck is VALID")
        st.session_state.truck_validated = True
        return result
    else:
        st.error("❌ Selected truck does NOT meet requirements")
        st.session_state.truck_validated = False

    return None


def show_trucks_selection():
    truck_type = st.radio(
        "What type of truck do you have?",
        ["Large Truck", "Medium Truck", "Custom Truck"],
        horizontal=True,
        key="truck_type",
    )

    if truck_type != "Custom Truck":
        st.session_state.truck_creation_in_progress = False
        st.session_state.truck_created_successfully = False

    if truck_type == "Large Truck":
        _show_standard_truck(CAMIONES_GRANDES, TRUCK_IMAGES["large"])
    elif truck_type == "Medium Truck":
        _show_standard_truck(CAMIONES_MEDIANOS, TRUCK_IMAGES["medium"])
    else:
        _show_custom_truck_selection()


# ======================================================================
#   STANDARD TRUCK SELECTION
# ======================================================================


def _show_standard_truck(trucks_dict, folder_path):
    selected_truck = st.selectbox(
        "Choose a truck:",
        list(trucks_dict.keys()),
    )

    if selected_truck:
        data = trucks_dict[selected_truck]
        img_path = os.path.join(folder_path, data["imagen"])

        _display_truck_details(selected_truck, data, img_path)

        st.session_state.selected_truck_data = {
            "nombre": selected_truck,
            "capacidad": data["capacidad"],
            "consumo": data["consumo"],
            "velocidad_constante": data["velocidad_constante"],
            "precio_conductor_hora": data["precio_conductor_hora"],
            "imagen": data["imagen"],
        }


# ======================================================================
#   CUSTOM TRUCKS
# ======================================================================


def _show_custom_truck_selection():
    st.subheader("🔧 Create Your Custom Truck")

    camiones_personalizados = get_camiones_personalizados()

    if camiones_personalizados:
        option = st.radio(
            "What would you like to do?",
            ["Use an existing custom truck", "Create a new one"],
            key="custom_option",
        )

        if option == "Use an existing custom truck":
            _show_existing_custom_truck(camiones_personalizados)
        else:
            _show_custom_truck_form()
    else:
        _show_custom_truck_form()


def _show_existing_custom_truck(camiones):
    custom_truck = st.selectbox(
        "Choose a custom truck:",
        list(camiones.keys()),
    )

    if custom_truck:
        data = camiones[custom_truck]
        img_path = os.path.join(TRUCK_IMAGES["custom"], data["imagen"])

        _display_truck_details(custom_truck, data, img_path)

        st.session_state.selected_truck_data = data | {"nombre": custom_truck}


# ======================================================================
#   DISPLAY TRUCK DETAILS
# ======================================================================


def _display_truck_details(name, data, img_path):
    st.markdown("<div class='truck-card'>", unsafe_allow_html=True)
    col1, col2 = st.columns([1, 2])

    with col1:
        if os.path.exists(img_path):
            st.image(img_path, width="stretch")
        else:
            st.warning(f"⚠️ Image not found: {img_path}")

    with col2:
        st.markdown(f"#### 📋 {name}")
        st.write(f"**Capacity:** {data['capacidad']} products")
        st.write(f"**Consumption:** {data['consumo']} L/100km")
        st.write(f"**Speed:** {data['velocidad_constante']} km/h")
        st.write(f"**Driver Cost:** €{data['precio_conductor_hora']}/h")

    st.markdown("</div>", unsafe_allow_html=True)


# ======================================================================
#   CUSTOM TRUCK FORM
# ======================================================================


def _show_custom_truck_form():
    with st.form("custom_truck_form"):
        st.markdown("##### Enter truck specifications:")

        col1, col2 = st.columns(2)

        with col1:
            name = st.text_input("🏷️ Truck Name")
            capacity = st.text_input("📦 Capacity (products)")

        with col2:
            consumption = st.text_input("⛽ Consumption (L/100km)")
            speed = st.text_input("🚀 Constant Speed (km/h)")
            price_driver = st.text_input("👨‍✈️ Driver price per hour (€)")

        image_file = st.file_uploader(
            "🖼 Upload truck image", type=["png", "jpg", "jpeg"]
        )

        submitted = st.form_submit_button("🚀 Create Truck")

        if not submitted:
            return

        # Validation
        truck_data = {
            "nombre": name,
            "capacidad": capacity,
            "consumo": consumption,
            "velocidad_constante": speed,
            "precio_conductor_hora": price_driver,
        }

        validations = [rule(truck_data) for rule in obtain_format_validation_rules()]
        all_valid = True
        for v in validations:
            if v.startswith("✔"):
                st.success(v)
            else:
                st.error(v)
                all_valid = False

        if not all_valid:
            return

        is_valid, transformed = parse_truck_data(truck_data)
        if not is_valid:
            st.error(f"Conversion error: {transformed.get('error')}")
            return

        # Save image
        image_name = save_custom_truck_image(image_file, name)

        # Save truck JSON entry
        ok = add_camion_personalizado(
            nombre=name,
            capacidad=capacity,
            consumo=consumption,
            velocidad_constante=speed,
            precio_conductor_hora=price_driver,
            imagen=image_name,
        )

        if ok:
            st.success("🎉 Custom truck created successfully!")
            preview_data = truck_data | {"imagen": image_name}
            img_path = os.path.join(TRUCK_IMAGES["custom"], image_name)
            _display_truck_details(name, preview_data, img_path)

            st.session_state.selected_truck_data = preview_data
            st.session_state.truck_created_successfully = True
        else:
            st.error("❌ Error saving custom truck.")


# ======================================================================
#   AI SIMULATION
# ======================================================================


def simulate_ia(df, truck_data):
    routes = [
        {
            "path": [
                [40.4168, -3.7038],
                [41.6497, -0.8877],
                [41.3874, 2.1686],
            ],
            "color": random.choice(ROUTE_COLORS),
        }
    ]

    return {
        "num_trucks": 1,
        "routes": routes,
        "assignments": pd.DataFrame(),
    }


# ======================================================================
#   FORM PAGE
# ======================================================================


def render_form_page():
    render_title()

    connection_type, file_inputs = render_connection_selector()
    st.markdown("---")

    if st.button("📥 Load Data", type="secondary"):
        load_data(connection_type, file_inputs)

    st.markdown("---")
    render_truck_selector()

    if st.session_state.truck_validated:
        st.markdown("---")
        if st.button("🚀 Generate Routes", type="primary"):
            with st.spinner("Generating routes..."):
                st.session_state.ia_result = simulate_ia(
                    st.session_state.df,
                    st.session_state.selected_truck_data,
                )
                st.session_state.page = "routes"
                st.rerun()


# ======================================================================
#   ROUTES PAGE
# ======================================================================


def render_routes_page():
    render_title()
    ia = st.session_state.get("ia_result")

    if ia is None:
        st.warning("⚠️ No routes generated yet.")
        return

    st.metric("Required Trucks", ia["num_trucks"])

    SpainMapRoutes().render(ia["routes"])

    st.dataframe(ia["assignments"])
