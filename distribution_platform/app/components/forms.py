"""
Form input components.
"""

import streamlit as st

from distribution_platform.app.config.constants import SUPPORTED_FILE_TYPES


class FileUploadSection:
    """Multi-file upload section."""

    REQUIRED_FILES = {
        "pedidos": ("📦", "Orders (Pedidos)"),
        "clientes": ("👥", "Clients (Clientes)"),
        "lineas_pedido": ("📋", "Order Lines (Líneas de Pedido)"),
        "productos": ("🏷️", "Products (Productos)"),
        "destinos": ("📍", "Destinations (Destinos)"),
        "provincias": ("🗺️", "Provinces (Provincias)"),
    }

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
        for key, (icon, label) in FileUploadSection.REQUIRED_FILES.items():
            files[key] = st.file_uploader(
                f"{icon} {label}",
                type=SUPPORTED_FILE_TYPES,
                key=f"upload_{key}",
            )
        return files

    @staticmethod
    def validate(files: dict) -> tuple[bool, list]:
        """Check if all required files are present."""
        missing = [k for k in FileUploadSection.REQUIRED_FILES if not files.get(k)]
        return len(missing) == 0, missing
