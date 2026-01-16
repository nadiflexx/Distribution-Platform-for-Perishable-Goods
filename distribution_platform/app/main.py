"""
Application Entry Point
Handles page configuration, CSS injection, and view routing.
"""

import streamlit as st

from distribution_platform.app.config import constants
from distribution_platform.app.state.session_manager import SessionManager
from distribution_platform.app.views import (
    FormView,
    ProcessingView,
    ResultsView,
    SplashView,
)
from distribution_platform.config.settings import Paths


class Application:
    """Main application controller."""

    def __init__(self):
        self._configure_page()
        self._inject_transition_shield()  # Prevent flash during transitions
        self._load_styles()
        SessionManager.initialize()

    def _configure_page(self):
        st.set_page_config(
            page_title="SmartCargo",
            page_icon=Paths.MEDIA / constants.LOGO,
            layout="wide",
            initial_sidebar_state="collapsed",
        )

    def _inject_transition_shield(self):
        """Inject CSS to prevent white flash during page transitions."""
        st.markdown(
            """
            <style>
                /* Immediate dark background - prevents flash */
                html, body {
                    background: #030305 !important;
                    margin: 0;
                    padding: 0;
                }

                .stApp {
                    background: #030305 !important;
                }

                /* Hide Streamlit branding during load */
                #MainMenu, footer, header {
                    visibility: hidden;
                }
            </style>
            """,
            unsafe_allow_html=True,
        )

    def _load_styles(self):
        css_path = Paths.CSS_FILE
        if css_path.exists():
            st.markdown(
                f"<style>{css_path.read_text()}</style>",
                unsafe_allow_html=True,
            )

    def run(self):
        """Route to the appropriate view based on app phase."""
        phase = st.session_state.get("app_phase", "SPLASH")

        views = {
            "SPLASH": SplashView,
            "FORM": FormView,
            "PROCESSING": ProcessingView,
            "RESULTS": ResultsView,
        }

        view_class = views.get(phase)
        if view_class:
            view_class().render()
        else:
            st.error(f"Unknown App State: {phase}")


def main():
    Application().run()


if __name__ == "__main__":
    main()
