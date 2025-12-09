from pathlib import Path

import streamlit as st


def apply_theme() -> None:
    """Inject CSS from components.css into the Streamlit app."""
    css_path = Path(__file__).with_name("components.css")
    if css_path.exists():
        css = css_path.read_text(encoding="utf-8")
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
