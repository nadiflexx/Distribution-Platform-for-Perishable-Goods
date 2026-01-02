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

        is_valid, parsed = parse_truck_data(truck_data)

        if not is_valid:
            error_msg = cast(dict[str, Any], parsed).get("error", "Unknown error")
            st.error(f"❌ {error_msg}")
            return False

        truck_obj = cast(Truck, parsed)

        # Run inference
        engine = InferenceMotor(rules.obtain_rules())
        result = engine.evaluate(truck_obj)

        SessionManager.set("validation_result", result)
        if result.is_valid:
            SessionManager.set("truck_validated", True)
            return True
        else:
            SessionManager.set("truck_validated", False)
            return False
