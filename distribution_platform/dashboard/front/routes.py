from distribution_platform.dashboard.front.user_interface import ui_components as ui
from distribution_platform.dashboard.front.knowledge_base import rules
from distribution_platform.dashboard.front.inference_engine.engine import InferenceMotor
import streamlit as st


def run_dashboard():
    selected_truck, send_request = ui.initialize_components()

    if send_request:
        ui.show_waiting_message()
        motor = InferenceMotor(rules.obtain_rules())
        result = motor.evaluate(selected_truck)

        if result.is_valid:
            st.success(
                "✅ The truck selected is **VALID** according to the defined rules."
            )
        else:
            st.error(
                "❌ The truck selected is **NOT VALID** according to the defined rules."
            )

        if "passed all validation rules" in result:
            ui.show_confirmation(result)
        else:
            ui.show_errors(result)


if __name__ == "__main__":
    run_dashboard()
