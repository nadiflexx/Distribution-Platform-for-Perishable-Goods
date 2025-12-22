"""
Data loading and ETL service.
"""

import streamlit as st

from distribution_platform.app.components.forms import FileUploadSection
from distribution_platform.app.state.session_manager import SessionManager
from distribution_platform.core.services.etl_service import run_etl


class DataService:
    """Handles data loading operations."""

    @staticmethod
    def load_from_database() -> bool:
        """Load data from database."""
        try:
            with st.spinner("Synchronizing data streams..."):
                data = run_etl(use_database=False)
                SessionManager.set("df", data)
                SessionManager.set("load_success", True)
                SessionManager.reset_validation()
            return True
        except Exception as e:
            st.error(f"❌ ETL Failure: {e}")
            return False

    @staticmethod
    def load_from_files(files: dict) -> bool:
        """Load data from uploaded files."""
        is_valid, missing = FileUploadSection.validate(files)

        if not is_valid:
            st.error(f"❌ Missing required files: {', '.join(missing)}")
            return False

        try:
            with st.spinner("Synchronizing data streams..."):
                data = run_etl(uploaded_files=files)
                SessionManager.set("df", data)
                SessionManager.set("load_success", True)
                SessionManager.reset_validation()
            return True
        except Exception as e:
            st.error(f"❌ ETL Failure: {e}")
            return False
