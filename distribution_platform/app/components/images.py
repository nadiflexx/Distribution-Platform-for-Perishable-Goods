"""
Image handling component.
"""

import base64
import os

import streamlit as st

from distribution_platform.app.config import constants
from distribution_platform.config.settings import Paths


class ImageLoader:
    """Handles image loading with fallbacks, and base64 encoding."""

    @staticmethod
    def render(img_input, width=None):
        try:
            if hasattr(img_input, "type"):
                # Uploaded file
                st.image(img_input, width="stretch")
            elif os.path.exists(str(img_input)):
                # File path
                st.image(str(img_input), width="stretch")
            else:
                ImageLoader._placeholder()
        except Exception:
            st.error("Image Error")

    @staticmethod
    def _placeholder():
        st.markdown(
            """
            <div class="no-image">
                <span>📷</span>
                <p>NO VISUAL</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    @staticmethod
    def _get_logo_img() -> str:
        """Reads the local logo file and returns a base64 HTML image tag source."""
        try:
            logo_path = Paths.MEDIA / constants.LOGO
            if logo_path.exists():
                with open(logo_path, "rb") as f:
                    data = f.read()
                    encoded = base64.b64encode(data).decode()
                return f"data:image/png;base64,{encoded}"
        except Exception:
            return ""
        return ""
