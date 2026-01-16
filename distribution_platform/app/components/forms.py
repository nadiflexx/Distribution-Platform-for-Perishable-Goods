"""
Form input components.
"""

import streamlit as st

from distribution_platform.app.config.constants import UploadConfig


class FileUploadSection:
    """Multi-file upload section."""

    @staticmethod
    def render() -> dict:
        """Render file uploaders and return uploaded files dict."""
        st.markdown(
            """
            <div class="upload-section-header">
                <span>📂</span> REQUIRED DATASETS
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.caption("Supported formats: CSV, TXT, XLSX")

        files = {}
        for key, (icon, label) in UploadConfig.REQUIRED_FILES.items():
            files[key] = st.file_uploader(
                f"{icon} {label}",
                type=UploadConfig.SUPPORTED_FILE_TYPES,
                key=f"upload_{key}",
            )
        return files

    @staticmethod
    def validate(files: dict) -> tuple[bool, list]:
        """Check if all required files are present."""
        missing = [k for k in UploadConfig.REQUIRED_FILES if not files.get(k)]
        return len(missing) == 0, missing
