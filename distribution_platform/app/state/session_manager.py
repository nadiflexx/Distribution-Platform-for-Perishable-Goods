"""
Centralized session state management.
"""

from typing import Any

import streamlit as st

from distribution_platform.app.config.constants import AppPhase, VehicleCategory


class SessionManager:
    """Manages all session state operations."""

    _DEFAULTS = {
        "app_phase": AppPhase.SPLASH,
        "load_success": False,
        "truck_validated": False,
        "df": None,
        "selected_truck_data": None,
        "ia_result": None,
        # UI selector persistence
        "sel_cat": VehicleCategory.HEAVY,
        "sel_model": None,
        "sel_custom_db": None,
    }

    @classmethod
    def initialize(cls):
        """Initialize session state with defaults if not present."""
        for key, default in cls._DEFAULTS.items():
            if key not in st.session_state:
                st.session_state[key] = default

    @classmethod
    def get(cls, key: str, default: Any = None) -> Any:
        """Get a session state value."""
        return st.session_state.get(key, default)

    @classmethod
    def set(cls, key: str, value: Any):
        """Set a session state value."""
        st.session_state[key] = value

    @classmethod
    def set_phase(cls, phase: str):
        """Set the application phase and trigger rerun."""
        cls.set("app_phase", phase)
        st.rerun()

    @classmethod
    def reset_validation(cls):
        """Reset truck validation state."""
        cls.set("truck_validated", False)

    @classmethod
    def is_ready_to_launch(cls) -> bool:
        """Check if all conditions are met to launch optimization."""
        return cls.get("truck_validated") and cls.get("load_success")

    @classmethod
    def get_selected_truck(cls) -> dict | None:
        """Get the currently selected truck data."""
        return cls.get("selected_truck_data")

    @classmethod
    def get_optimization_result(cls) -> dict | None:
        """Get the AI optimization result."""
        return cls.get("ia_result")
