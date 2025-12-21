import streamlit as st

# Importamos las funciones de UI
from distribution_platform.app.user_interface.ui_components import (
    init_state,
    render_form_page,
    render_routes_page,
)
from distribution_platform.config.settings import Paths


def load_styles():
    # Asegúrate de que la ruta coincida con donde guardaste components.css
    if Paths.CSS_FILE.exists():
        st.markdown(
            f"<style>{Paths.CSS_FILE.read_text()}</style>", unsafe_allow_html=True
        )
    else:
        # Fallback simple por si la ruta falla
        st.warning("Estilos no encontrados, usando estilos por defecto.")


def main():
    st.set_page_config(
        page_title="IA Delivery – Route Planner",
        page_icon="🚚",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    load_styles()
    init_state()

    with st.sidebar:
        st.image(
            "https://cdn-icons-png.flaticon.com/512/3063/3063823.png", width=50
        )  # Icono opcional
        st.title("Navegación")

        # Estilo para el radio button en sidebar
        choice = st.radio(
            "Ir a:",
            ["Formulario", "Rutas"],
            index=0 if st.session_state.page == "form" else 1,
        )

        st.markdown("---")
        st.info("💡 **Tip:** Asegúrate de validar el camión antes de generar la ruta.")

    # Lógica de navegación
    # Si el usuario hace click en el sidebar, actualizamos el estado
    if choice == "Formulario":
        st.session_state.page = "form"
    else:
        # Solo permitimos ir a rutas si hay resultados, sino vuelta al form
        if st.session_state.get("ia_result"):
            st.session_state.page = "routes"
        else:
            st.session_state.page = "form"
            # Opcional: Avisar que no hay rutas
            # st.sidebar.warning("Genera una ruta primero.")

    if st.session_state.page == "form":
        render_form_page()
    else:
        render_routes_page()


if __name__ == "__main__":
    main()
