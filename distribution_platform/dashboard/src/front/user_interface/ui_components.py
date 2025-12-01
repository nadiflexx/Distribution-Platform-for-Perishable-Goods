import os

import streamlit as st

from data_models.trucks import CAMIONES_GRANDES, CAMIONES_MEDIANOS


def show_initial_title():
    """Muestra el título inicial de la aplicación."""
    st.title("Genera tu ruta - IA Delivery")


def show_trucks_selection():
    """Muestra dos desplegables con camiones grandes y medianos.

    Mostrar imágenes e información de capacidad y consumo de los camiones.
    """
    # Obtener la ruta base del directorio media
    media_path = os.path.dirname(__file__) + "/media"

    st.header("Selecciona tus Camiones")

    col1, col2 = st.columns(2)

    # Desplegable para camiones grandes
    with col1:
        st.subheader("Camiones Grandes")
        camion_grande_seleccionado = st.selectbox(
            "Elige un camión grande:",
            list(CAMIONES_GRANDES.keys()),
            key="camion_grande"
        )

        if camion_grande_seleccionado:
            datos = CAMIONES_GRANDES[camion_grande_seleccionado]
            img_path = os.path.join(
                media_path, "camiones_grandes", datos["imagen"]
            )

            if os.path.exists(img_path):
                st.image(img_path, use_column_width=True)

            st.write(f"**Capacidad:** {datos['capacidad']}")
            st.write(f"**Consumo:** {datos['consumo']}")

    # Desplegable para camiones medianos
    with col2:
        st.subheader("Camiones Medianos")
        camion_mediano_seleccionado = st.selectbox(
            "Elige un camión mediano:",
            list(CAMIONES_MEDIANOS.keys()),
            key="camion_mediano"
        )

        if camion_mediano_seleccionado:
            datos = CAMIONES_MEDIANOS[camion_mediano_seleccionado]
            img_path = os.path.join(
                media_path, "camiones_medianos", datos["imagen"]
            )

            if os.path.exists(img_path):
                st.image(img_path, use_column_width=True)

            st.write(f"**Capacidad:** {datos['capacidad']}")
            st.write(f"**Consumo:** {datos['consumo']}")


