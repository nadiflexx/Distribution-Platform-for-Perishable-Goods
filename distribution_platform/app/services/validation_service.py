"""
Vehicle validation service.
"""

from typing import Any, cast

import streamlit as st

from distribution_platform.app.state.session_manager import SessionManager
from distribution_platform.core.inference_engine.engine import InferenceMotor
from distribution_platform.core.knowledge_base import rules
from distribution_platform.core.knowledge_base.rules import parse_truck_data
from distribution_platform.core.models.truck import Truck


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
        # Mypy sees parsed as Union[Dict[str, Any], Truck]
        is_valid, parsed = parse_truck_data(truck_data)

        if not is_valid:
            # We know it's a dict here because is_valid is False
            error_msg = cast(dict[str, Any], parsed).get("error", "Unknown error")
            st.error(f"❌ {error_msg}")
            return False

        # We know it's a Truck object here because is_valid is True
        truck_obj = cast(Truck, parsed)

        # Run inference
        engine = InferenceMotor(rules.obtain_rules())
        result = engine.evaluate(truck_obj)

        if result.is_valid:
            SessionManager.set("truck_validated", True)
            st.toast("Vehicle Validated Successfully", icon="🛡️")
            return True
        else:
            st.error("❌ Validation Failed - Vehicle does not meet requirements")
            return False
