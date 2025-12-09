from pathlib import Path

import streamlit as st

from distribution_platform.dashboard.front.user_interface.ui_components import (
    init_state,
    render_form_page,
    render_routes_page,
)


def load_styles():
    css_path = Path(__file__).parent / "styles" / "components.css"
    if css_path.exists():
        st.markdown(f"<style>{css_path.read_text()}</style>", unsafe_allow_html=True)


def main():
    st.set_page_config(
        page_title="IA Delivery – Route Planner", page_icon="🚚", layout="wide"
    )

    load_styles()
    init_state()

    with st.sidebar:
        choice = st.radio(
            "Navegación",
            ["Formulario", "Rutas"],
            index=0 if st.session_state.page == "form" else 1,
        )

    st.session_state.page = "form" if choice == "Formulario" else "routes"

    if st.session_state.page == "form":
        render_form_page()
    else:
        render_routes_page()


if __name__ == "__main__":
    main()
