import os
import pandas as pd
import streamlit as st
import random

from data_models.trucks import CAMIONES_GRANDES, CAMIONES_MEDIANOS
from distribution_platform.dashboard.front.user_interface.maps import SpainMapRoutes
from distribution_platform.pipelines.etl_pipeline import run_etl
from distribution_platform.config.settings import ROUTE_COLORS


# =====================================================================================
#   ESTADO INICIAL
# =====================================================================================
def init_state():
    defaults = {
        "page": "form",
        "connection_type": None,
        "df": None,
        "selected_trucks": {},
        "ia_result": None,
        "load_success": False,
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


# =====================================================================================
#   TÍTULO
# =====================================================================================
def render_title():
    st.markdown(
        "<h1 class='main-title'>IA Delivery – Route Planner</h1>",
        unsafe_allow_html=True,
    )
    st.caption("Planificación inteligente de rutas para productos perecederos.")


# =====================================================================================
#   SELECTOR DE FUENTE DE DATOS (BD o CSV) — VERSIÓN CORRECTA
# =====================================================================================
def render_connection_selector():
    st.subheader("1. Seleccionar fuente de datos")

    connection = st.radio(
        "¿Cómo quieres cargar los datos?",
        ["Base de datos", "Archivos"],
        key="connection_type",
        horizontal=True,
    )

    file_inputs = {}

    if connection == "Archivos":
        st.info("📄 Sube los archivos necesarios (igual que en tu versión original):")

        file_inputs = {
            "clientes": st.file_uploader("dboClientes.csv", type=["csv"]),
            "lineas_pedido": st.file_uploader("dboLineasPedido.csv", type=["csv"]),
            "pedidos": st.file_uploader("dboPedidos.csv", type=["csv"]),
            "productos": st.file_uploader("dboProductos.csv", type=["csv"]),
            "provincias": st.file_uploader("dboProvincias.csv", type=["csv"]),
            "destinos": st.file_uploader("dboDestinos.csv", type=["csv"]),
        }

    return connection, file_inputs


# =====================================================================================
#   CARGA DE DATOS (BD o ARCHIVOS) — VERSIÓN FINAL
# =====================================================================================
def load_data(connection_type, file_inputs):
    """
    Mantiene:
    - La conexión a base de datos EXACTAMENTE como antes.
    - El uploader original EXACTAMENTE como antes.
    - No se leen CSV en el front.
    - Se pasan los UploadedFile directamente al ETL.
    """

    # -------------------------------------------------------------------------
    #   BASE DE DATOS
    # -------------------------------------------------------------------------
    if connection_type == "Base de datos":
        st.info("Intentando conectar con la base de datos...")

        try:
            df = run_etl(use_database=False)
        except Exception as e:
            st.error(f"❌ Error conectando a la base de datos:\n{e}")
            st.session_state.load_success = False
            return None

        if df is None:
            st.error("❌ ETL no devolvió datos.")
            return None

        # Si es lista → es correcto (transform_to_orders)
        if isinstance(df, list):
            if len(df) == 0:
                st.error("❌ ETL devolvió una lista vacía.")
                return None
        else:
            # Si es DataFrame → como antes
            if hasattr(df, "empty") and df.empty:
                st.error("❌ ETL ejecutado pero sin datos válidos.")
                return None

        st.success(f"✔ BD conectada correctamente ({len(df)} registros).")
        st.session_state.df = df
        st.session_state.load_success = True
        return df

    # -------------------------------------------------------------------------
    #   ARCHIVOS CSV (VERSIÓN ORIGINAL RESTAURADA)
    # -------------------------------------------------------------------------
    missing = [k for k, f in file_inputs.items() if f is None]

    if missing:
        st.error("❌ Faltan CSV por subir:\n- " + "\n- ".join(missing))
        return None

    try:
        df = run_etl(uploaded_files=file_inputs)

    except Exception as e:
        st.error(f"❌ Error ejecutando el ETL con los archivos:\n{e}")
        st.session_state.load_success = False
        return None

    if df is None:
        st.error("❌ ETL no devolvió datos.")
        return None

    # Si es lista → es correcto (transform_to_orders)
    if isinstance(df, list):
        if len(df) == 0:
            st.error("❌ ETL devolvió una lista vacía.")
            return None
    else:
        # Si es DataFrame → como antes
        if hasattr(df, "empty") and df.empty:
            st.error("❌ ETL ejecutado pero sin datos válidos.")
            return None

    st.success(f"✔ Archivos procesados correctamente ({len(df)} registros).")
    st.session_state.df = df
    st.session_state.load_success = True
    return df


# =====================================================================================
#   SELECTOR DE CAMIONES
# =====================================================================================
def truck_card(nombre, datos, tipo, base_path):
    img_path = os.path.join(base_path, datos.get("imagen", ""))

    st.markdown(f"<div class='truck-card-title'>{nombre}</div>", unsafe_allow_html=True)
    col1, col2 = st.columns([2, 3])

    with col1:
        if os.path.exists(img_path):
            st.image(img_path, use_container_width=True)

    with col2:
        st.write(f"**Capacidad:** {datos['capacidad']}")
        st.write(f"**Consumo:** {datos['consumo']}")

    selected = st.checkbox("Seleccionar", key=f"{tipo}_{nombre}")
    st.markdown("<hr class='truck-divider'>", unsafe_allow_html=True)

    return selected


def render_truck_selector():
    st.subheader("2. Selección de camiones")

    if not st.session_state.load_success:
        st.info("Carga los datos antes de elegir camiones.")
        return {}

    df = st.session_state.df
    st.success(f"📦 Datos cargados ({len(df)} registros). Selecciona los camiones.")

    base_large = os.path.join(os.path.dirname(__file__), "media", "camiones_grandes")
    base_medium = os.path.join(os.path.dirname(__file__), "media", "camiones_medianos")

    col1, col2 = st.columns(2)
    selected = {}

    with col1:
        st.markdown("### 🚛 Grandes")
        for name, data in CAMIONES_GRANDES.items():
            if truck_card(name, data, "grande", base_large):
                selected[name] = data

    with col2:
        st.markdown("### 🚚 Medianos")
        for name, data in CAMIONES_MEDIANOS.items():
            if truck_card(name, data, "mediano", base_medium):
                selected[name] = data

    return selected


# =====================================================================================
#   SIMULACIÓN DE IA (placeholder)
# =====================================================================================
# Random color from settings.py ROUTE_COLORS
def simulate_ia(df, trucks):
    # DEMO: rutas fijas solo para mostrar el mapa funcionando
    demo_routes = [
        {
            "path": [
                [40.416775, -3.703790],  # Madrid
                [41.649693, -0.887712],  # Zaragoza
                [41.387417, 2.168568],  # Barcelona
            ],
            "color": getRandomColor(),
        },
        {
            "path": [
                [40.416775, -3.703790],  # Madrid
                [39.469907, -0.376288],  # Valencia
            ],
            "color": getRandomColor(),
        },
    ]

    return {
        "num_trucks": len(trucks),
        "routes": demo_routes,  # <----- YA TIENE RUTAS
        "assignments": pd.DataFrame(),
    }


# Random color cannot be the same every time
def getRandomColor():
    return random.choice(ROUTE_COLORS)


def handle_submit(selected_trucks):
    df = st.session_state.df
    st.session_state.ia_result = simulate_ia(df, selected_trucks)
    st.session_state.page = "routes"
    st.rerun()


# =====================================================================================
#   FORM PAGE
# =====================================================================================
def render_form_page():
    render_title()

    connection_type, file_inputs = render_connection_selector()

    st.markdown("---")

    if st.button("📥 Cargar datos"):
        load_data(connection_type, file_inputs)

    st.markdown("---")

    selected_trucks = render_truck_selector()

    if st.session_state.load_success and selected_trucks:
        st.markdown("---")
        if st.button("Generar rutas ▶", type="primary"):
            handle_submit(selected_trucks)


# =====================================================================================
#   ROUTES PAGE
# =====================================================================================
def render_routes_page():
    render_title()

    ia = st.session_state.ia_result
    if ia is None:
        st.warning("Todavía no se han generado rutas.")
        return
    # Include truc emote 🚚
    st.metric("Número de camiones necesarios", f"{ia['num_trucks']} 🚚")

    st.markdown("### 🗺️ Mapa de rutas")

    # Renderizar SOLO las rutas generadas por la IA
    SpainMapRoutes().render(ia["routes"])

    st.markdown("### 📦 Asignación de productos")
    st.dataframe(ia["assignments"], use_container_width=True)
