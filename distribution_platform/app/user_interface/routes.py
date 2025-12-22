import streamlit as st

from distribution_platform.app.user_interface.ui_components import (
    init_state,
    view_form_page,
    view_processing_screen,
    view_results_page,
    view_splash_screen,
)
from distribution_platform.config.settings import Paths


def load_css():
    if Paths.CSS_FILE.exists():
        st.markdown(
            f"<style>{Paths.CSS_FILE.read_text()}</style>", unsafe_allow_html=True
        )


def main():
    # 1. Configuración de Ventana
    st.set_page_config(
        page_title="BrainCore AI",
        page_icon="🚚",
        layout="wide",
        initial_sidebar_state="collapsed",  # Sidebar colapsado para look "App nativa"
    )

    # 2. Inyecciones Globales
    load_css()
    init_state()

    # 3. Máquina de Estados (Router)
    # Inicializar fase si no existe
    if "app_phase" not in st.session_state:
        st.session_state.app_phase = "SPLASH"

    phase = st.session_state.app_phase

    if phase == "SPLASH":
        view_splash_screen()

    elif phase == "FORM":
        view_form_page()

    elif phase == "PROCESSING":
        view_processing_screen()

    elif phase == "RESULTS":
        view_results_page()

    else:
        st.error(f"Unknown App State: {phase}")


if __name__ == "__main__":
    main()
