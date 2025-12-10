import os
import random

import pandas as pd
import streamlit as st

from distribution_platform.config.paths import TRUCK_IMAGES
from distribution_platform.config.settings import ROUTE_COLORS
from distribution_platform.core.inference_engine.engine import InferenceMotor
from distribution_platform.core.knowledge_base import rules
from distribution_platform.core.knowledge_base.rules import (
    obtain_format_validation_rules,
    parse_truck_data,
)
from distribution_platform.infrastructure.etl.etl_pipeline import run_etl
from distribution_platform.infrastructure.maps.maps import SpainMapRoutes
from distribution_platform.infrastructure.repositories.truck_repository import (
    CAMIONES_GRANDES,
    CAMIONES_MEDIANOS,
    add_camion_personalizado,
    get_camiones_personalizados,
    save_custom_truck_image,
)

# ======================================================================
#   HELPER: STYLING WRAPPERS
# ======================================================================


def start_card(title, icon="🔹"):
    """Inicia un contenedor visual estilo tarjeta."""
    st.markdown(
        f"""
    <div class="modern-card">
        <div class="card-header">
            <span class="card-icon">{icon}</span>
            <h3 class="card-title">{title}</h3>
        </div>
    """,
        unsafe_allow_html=True,
    )


def end_card():
    """Cierra el contenedor de tarjeta."""
    st.markdown("</div>", unsafe_allow_html=True)


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
        """
        <div class="main-header">
            <h1>🚚 AI Delivery Planner</h1>
            <p>Planificación inteligente de rutas para productos perecederos.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ======================================================================
#   DATA SOURCE SELECTOR
# ======================================================================


def render_connection_selector():
    start_card("Fuente de Datos", icon="📂")

    col1, col2 = st.columns([1, 3])

    with col1:
        st.info("Selecciona el origen de tus datos para comenzar el análisis.")

    with col2:
        connection = st.radio(
            "¿Cómo deseas cargar los datos?",
            ["Database", "Files"],
            key="connection_type",
            horizontal=True,
            help="Elige 'Database' para conexión directa o 'Files' para subir CSV/XLSX/TXT.",
        )

    file_inputs = {}

    if connection == "Files":
        st.markdown("---")
        st.write("#### 📄 Subida de Archivos CSV")

        # Grid layout for file uploaders
        c1, c2 = st.columns(2)
        with c1:
            file_inputs["clientes"] = st.file_uploader("👤 Clientes (dboClientes)")
            file_inputs["lineas_pedido"] = st.file_uploader(
                "📝 Líneas Pedido (dboLineasPedido)"
            )
            file_inputs["pedidos"] = st.file_uploader("📦 Pedidos (dboPedidos)")
        with c2:
            file_inputs["productos"] = st.file_uploader("🍎 Productos (dboProductos)")
            file_inputs["provincias"] = st.file_uploader(
                "📍 Provincias (dboProvincias)"
            )
            file_inputs["destinos"] = st.file_uploader("🏁 Destinos (dboDestinos)")

    end_card()
    return connection, file_inputs


# ======================================================================
#   DATA LOADING
# ======================================================================


def load_data(connection_type, file_inputs):
    """Load data from database or CSV files."""

    if connection_type == "Database":
        with st.spinner("🔌 Conectando a la base de datos..."):
            try:
                orders = run_etl(use_database=False)
            except Exception as e:
                st.error(f"❌ Error conectando a BD:\n{e}")
                st.session_state.load_success = False
                return None
    else:
        missing = [k for k, f in file_inputs.items() if f is None]
        if missing:
            st.error("❌ Faltan archivos:\n- " + "\n- ".join(missing))
            return None

        try:
            with st.spinner("🔄 Procesando archivos ETL..."):
                orders = run_etl(uploaded_files=file_inputs)
        except Exception as e:
            st.error(f"❌ Error ejecutando ETL con archivos:\n{e}")
            st.session_state.load_success = False
            return None

    # Validate result
    if orders is None or (hasattr(orders, "empty") and orders.empty):
        st.error("❌ El proceso ETL no retornó datos válidos.")
        return None

    st.toast(f"✅ Datos cargados correctamente ({len(orders)} registros).", icon="🎉")
    st.session_state.df = orders
    st.session_state.load_success = True


# ======================================================================
#   TRUCK SELECTOR
# ======================================================================


def render_truck_selector():
    start_card("Configuración de Flota", icon="🚛")

    if not st.session_state.load_success:
        st.warning(
            "⚠️ Por favor, carga los datos en la sección anterior para continuar."
        )
        end_card()
        return

    st.success("📦 Datos listos. Selecciona el vehículo para la ruta.")
    st.markdown("---")

    show_trucks_selection()

    disabled = (
        st.session_state.truck_creation_in_progress
        and not st.session_state.truck_created_successfully
    )

    st.markdown("<br>", unsafe_allow_html=True)

    # Centered button
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button(
            "✔️ Confirmar Vehículo",
            disabled=disabled,
            type="primary",
            use_container_width=True,
        ):
            truck = validate_and_confirm_truck()
            if truck is not None:
                st.session_state.selected_truck = truck

    end_card()


def validate_and_confirm_truck():
    truck_data = st.session_state.selected_truck_data

    if not truck_data:
        st.error("❌ No se ha seleccionado ningún camión.")
        return

    is_valid, result = parse_truck_data(truck_data)

    if not is_valid:
        st.error(f"❌ Error convirtiendo datos: {result.get('error')}")
        return

    with st.spinner("🔍 El motor de IA está validando el vehículo..."):
        motor = InferenceMotor(rules.obtain_rules())
        validation_result = motor.evaluate(result)

    if validation_result.is_valid:
        st.success("✅ El camión seleccionado es VÁLIDO")
        st.session_state.truck_validated = True
        return result
    else:
        st.error("❌ El camión NO cumple los requisitos")
        st.session_state.truck_validated = False

    return None


def show_trucks_selection():
    col_opt, col_disp = st.columns([1, 2])

    with col_opt:
        st.write("**Tipo de Vehículo**")
        truck_type = st.radio(
            "Selecciona categoría:",
            ["Camión Grande", "Camión Mediano", "Camión Personalizado"],
            key="truck_type",
            label_visibility="collapsed",
        )

    if truck_type != "Camión Personalizado":
        st.session_state.truck_creation_in_progress = False
        st.session_state.truck_created_successfully = False

    with col_disp:
        if truck_type == "Camión Grande":
            _show_standard_truck(CAMIONES_GRANDES, TRUCK_IMAGES["large"])
        elif truck_type == "Camión Mediano":
            _show_standard_truck(CAMIONES_MEDIANOS, TRUCK_IMAGES["medium"])
        else:
            _show_custom_truck_selection()


# ======================================================================
#   STANDARD TRUCK SELECTION
# ======================================================================


def _show_standard_truck(trucks_dict, folder_path):
    selected_truck = st.selectbox(
        "Elige un modelo:",
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
    camiones_personalizados = get_camiones_personalizados()

    if camiones_personalizados:
        option = st.radio(
            "Acción:",
            ["Usar existente", "Crear nuevo"],
            horizontal=True,
            key="custom_option",
        )

        if option == "Usar existente":
            _show_existing_custom_truck(camiones_personalizados)
        else:
            _show_custom_truck_form()
    else:
        st.info("No hay camiones personalizados. ¡Crea el primero!")
        _show_custom_truck_form()


def _show_existing_custom_truck(camiones):
    custom_truck = st.selectbox(
        "Mis camiones personalizados:",
        list(camiones.keys()),
    )

    if custom_truck:
        data = camiones[custom_truck]
        img_path = os.path.join(TRUCK_IMAGES["custom"], data["imagen"])
        _display_truck_details(custom_truck, data, img_path)
        st.session_state.selected_truck_data = data | {"nombre": custom_truck}


# ======================================================================
#   DISPLAY TRUCK DETAILS (Beautiful HTML Card)
# ======================================================================


def _display_truck_details(name, data, img_path):
    # Determine image source
    if os.path.exists(img_path):
        # We need to render the image via streamlit to get the correct path if local,
        # but for HTML embedding in 'truck-display', simple paths are tricky in Streamlit.
        # So we use a hybrid approach: Columns inside the parent container.
        pass

    st.markdown(f"#### 📋 Ficha Técnica: {name}")

    c1, c2 = st.columns([1, 1.5])

    with c1:
        if os.path.exists(img_path):
            st.image(img_path, use_container_width=True)
        else:
            st.warning("⚠️ Imagen no encontrada")

    with c2:
        st.markdown(
            f"""
        <div class="truck-details" style="background:white; padding:10px; border-radius:8px;">
            <div class="detail-row"><strong>📦 Capacidad:</strong> <span>{data["capacidad"]} productos</span></div>
            <div class="detail-row"><strong>⛽ Consumo:</strong> <span>{data["consumo"]} L/100km</span></div>
            <div class="detail-row"><strong>🚀 Velocidad:</strong> <span>{data["velocidad_constante"]} km/h</span></div>
            <div class="detail-row"><strong>👨‍✈️ Coste Conductor:</strong> <span>{data["precio_conductor_hora"]} €/h</span></div>
        </div>
        """,
            unsafe_allow_html=True,
        )


# ======================================================================
#   CUSTOM TRUCK FORM
# ======================================================================


def _show_custom_truck_form():
    st.markdown("##### 🛠️ Especificaciones del Nuevo Camión")

    with st.form("custom_truck_form"):
        col1, col2 = st.columns(2)

        with col1:
            name = st.text_input("🏷️ Nombre del Modelo")
            capacity = st.text_input("📦 Capacidad (prod)")
            image_file = st.file_uploader(
                "🖼 Imagen (PNG/JPG)", type=["png", "jpg", "jpeg"]
            )

        with col2:
            consumption = st.text_input("⛽ Consumo (L/100km)")
            speed = st.text_input("🚀 Velocidad (km/h)")
            price_driver = st.text_input("👨‍✈️ Coste Hora (€)")

        submitted = st.form_submit_button(
            "Guardar Vehículo", type="primary", use_container_width=True
        )

        if not submitted:
            return

        # Validation Logic
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
            if not v.startswith("✔"):
                st.error(v)
                all_valid = False

        if not all_valid:
            return

        is_valid, transformed = parse_truck_data(truck_data)
        if not is_valid:
            st.error(f"Error de conversión: {transformed.get('error')}")
            return

        # Save image
        image_name = save_custom_truck_image(image_file, name)

        # Save truck
        ok = add_camion_personalizado(
            nombre=name,
            capacidad=capacity,
            consumo=consumption,
            velocidad_constante=speed,
            precio_conductor_hora=price_driver,
            imagen=image_name,
        )

        if ok:
            st.success("🎉 ¡Camión creado exitosamente!")
            preview_data = truck_data | {"imagen": image_name}
            img_path = os.path.join(TRUCK_IMAGES["custom"], image_name)

            # Update Session
            st.session_state.selected_truck_data = preview_data
            st.session_state.truck_created_successfully = True

            # Force rerun to update list or show details
            st.rerun()
        else:
            st.error("❌ Error guardando el camión.")


# ======================================================================
#   AI SIMULATION
# ======================================================================


def simulate_ia(df, truck_data):
    # Dummy logic preserved from original
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

    # 1. Data Connection
    connection_type, file_inputs = render_connection_selector()

    col_load, _ = st.columns([1, 3])
    with col_load:
        if st.button("📥 Cargar Datos", type="secondary"):
            load_data(connection_type, file_inputs)

    # 2. Truck Selection
    render_truck_selector()

    # 3. Generate Action
    if st.session_state.truck_validated:
        st.markdown("---")
        c1, c2, c3 = st.columns([1, 2, 1])
        with c2:
            if st.button(
                "🚀 GENERAR RUTA ÓPTIMA", type="primary", use_container_width=True
            ):
                with st.spinner("🤖 La IA está calculando la ruta óptima..."):
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
    st.markdown(
        '<div class="main-header"><h1>🗺️ Resultados de la Ruta</h1></div>',
        unsafe_allow_html=True,
    )

    ia = st.session_state.get("ia_result")

    if ia is None:
        st.warning("⚠️ No hay rutas generadas. Vuelve al formulario.")
        if st.button("🔙 Volver"):
            st.session_state.page = "form"
            st.rerun()
        return

    # Metrics Row
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Camiones Necesarios", ia["num_trucks"])
    with c2:
        st.metric("Distancia Total", "N/A")  # Placeholder as logic was mock
    with c3:
        st.metric("Eficiencia", "98%")

    st.markdown("---")

    # Map Card
    start_card("Visualización Geográfica", icon="📍")
    SpainMapRoutes().render(ia["routes"])
    end_card()

    # Data Card
    start_card("Detalle de Asignaciones", icon="📊")
    st.dataframe(ia["assignments"], use_container_width=True)
    end_card()

    if st.button("🔄 Nueva Simulación"):
        st.session_state.page = "form"
        st.rerun()
