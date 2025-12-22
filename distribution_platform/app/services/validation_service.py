"""
Vehicle validation service.
"""

import streamlit as st

from distribution_platform.app.state.session_manager import SessionManager
from distribution_platform.core.inference_engine.engine import InferenceMotor
from distribution_platform.core.knowledge_base import rules
from distribution_platform.core.knowledge_base.rules import parse_truck_data


class ValidationService:
    """Handles vehicle validation logic."""

    @staticmethod
    def validate_truck() -> bool:
        """Validate the selected truck using inference engine."""
        truck_data = SessionManager.get("selected_truck_data")

        if not truck_data:
            st.warning("⚠️ Select a vehicle first")
            return False

        # Parse truck data
        is_valid, parsed = parse_truck_data(truck_data)
        if not is_valid:
            st.error(f"❌ {parsed['error']}")
            return False

        # Run inference
        engine = InferenceMotor(rules.obtain_rules())
        result = engine.evaluate(parsed)

        if result.is_valid:
            SessionManager.set("truck_validated", True)
            st.toast("Vehicle Validated Successfully", icon="🛡️")
            return True
        else:
            st.error("❌ Validation Failed - Vehicle does not meet requirements")
            return False
