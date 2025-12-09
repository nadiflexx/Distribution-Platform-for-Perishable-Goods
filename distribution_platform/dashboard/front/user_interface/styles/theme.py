import os
from pathlib import Path

import streamlit as st


def apply_theme() -> None:
    """Inyecta el CSS de componentes.css en la app de Streamlit."""
    css_path = Path(__file__).with_name("components.css")
    if css_path.exists():
        css = css_path.read_text(encoding="utf-8")
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
