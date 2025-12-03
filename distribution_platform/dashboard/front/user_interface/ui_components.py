import os

import streamlit as st

from data_models.trucks import CAMIONES_GRANDES, CAMIONES_MEDIANOS
import pandas as pd
import time
from distribution_platform.dashboard.front.user_interface.maps import SpainMapRoutes
from distribution_platform.pipelines.etl_pipeline import run_etl


def show_initial_title():
    """Muestra el título inicial de la aplicación."""
    st.title("Generate your route - IA Delivery")


def show_trucks_selection():
    """Muestra dos desplegables con camiones grandes y medianos.

    Mostrar imágenes e información de capacidad y consumo de los camiones.
    """
    # Obtener la ruta base del directorio media
    media_path = os.path.dirname(__file__) + "/media"

    st.header("Select your Trucks")

    col1, col2 = st.columns(2)

    # Desplegable para camiones grandes
    with col1:
        st.subheader("Large Trucks")
        camion_grande_seleccionado = st.selectbox(
            "Choose a large truck:",
            list(CAMIONES_GRANDES.keys()),
            key="camion_grande",
        )

        if camion_grande_seleccionado:
            datos = CAMIONES_GRANDES[camion_grande_seleccionado]
            img_path = os.path.join(media_path, "camiones_grandes", datos["imagen"])

            if os.path.exists(img_path):
                st.image(img_path, use_column_width=True)

            st.write(f"**Capacity:** {datos['capacidad']}")
            st.write(f"**Consumption:** {datos['consumo']}")

    # Desplegable para camiones medianos
    with col2:
        st.subheader("Medium Trucks")
        camion_mediano_seleccionado = st.selectbox(
            "Choose a medium truck:",
            list(CAMIONES_MEDIANOS.keys()),
            key="camion_mediano",
        )

        if camion_mediano_seleccionado:
            datos = CAMIONES_MEDIANOS[camion_mediano_seleccionado]
            img_path = os.path.join(media_path, "camiones_medianos", datos["imagen"])

            if os.path.exists(img_path):
                st.image(img_path, use_column_width=True)

            st.write(f"**Capacity:** {datos['capacidad']}")
            st.write(f"**Consumption:** {datos['consumo']}")


def initialize_components():
    show_initial_title()
    # Inicializar clave en session_state si no existe
    if "df" not in st.session_state:
        st.session_state.df = None

    # Mostrar uploader mientras df sea None
    if st.session_state.df is None:
        st.session_state.df = upload()
        if st.session_state.df is None:
            show_rules()
            return None, False

    # Si df ya está cargado -> mostrar resto de componentes
    show_trucks_selection()

    send_request = select_button()
    truck_selected = None  # futuro: seleccionar camión

    return truck_selected, send_request


def upload():
    # Default radio should be not selected
    st.subheader("CSV File Upload")
    option = st.radio(
        "Select the data loading method:",
        ("Upload CSV files", "Connect to database"),
        index=None,
    )

    if option == "Connect to database":
        st.info("Database connection functionality not yet implemented.")
        return None
    elif option == "Upload CSV files":
        files_clientes = st.file_uploader("dboClientes")
        files_lineas = st.file_uploader("dboLineasPedido")
        files_pedidos = st.file_uploader("dboPedidos")
        files_productos = st.file_uploader("dboProductos")
        files_provincias = st.file_uploader("dboProvincias")
        files_destinos = st.file_uploader("dboDestinos")

        if st.button("Process"):
            files_dict = {
                "clientes": files_clientes,
                "lineas_pedido": files_lineas,
                "pedidos": files_pedidos,
                "productos": files_productos,
                "provincias": files_provincias,
                "destinos": files_destinos,
            }

            df_final = run_etl(uploaded_files=files_dict)

            st.success("ETL completed with uploaded files.")

            return df_final
    else:
        st.warning("Please select a data loading method.")
        return None


def select_box(invoices):
    options = invoices["Número de factura"].unique().tolist()
    choice = st.selectbox("Select an option:", options)
    st.write(f"You selected: {choice}")
    return invoices[invoices["Número de factura"] == choice].iloc[0]


def select_button():
    return st.button("Send request")


def show_waiting_message():
    with st.spinner("Procesando, por favor espere..."):
        time.sleep(3)


def show_confirmation(message):
    st.success(message)


def show_errors(errors):
    for error in errors:
        st.error(error)


def clean_messages(message):
    time.sleep(3)
    message.empty()


def show_rules():
    st.subheader("Routes Validation Rules")

    st.markdown("""
    - The csv file must contain all required fields.
    - The truck selected must have enough capacity for the delivery.
    - The truck selected must have an acceptable fuel consumption rate.
    - The truck selected must have a constant velocity during the route.
    """)


def show_routes_map():
    st.header("Mapa de rutas")

    map_component = SpainMapRoutes()

    routes = [
        {
            "path": [
                [40.4168, -3.7038],  # Madrid
                [41.3874, 2.1686],  # Barcelona
            ],
            "color": "red",
        },
        {
            "path": [
                [40.4168, -3.7038],  # Madrid
                [39.4699, -0.3763],  # Valencia
            ],
            "color": "blue",
        },
    ]

    map_component.render(routes)
