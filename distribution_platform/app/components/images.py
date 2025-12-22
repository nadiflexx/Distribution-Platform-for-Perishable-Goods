"""
Image handling component.
"""

import os

import streamlit as st


class ImageLoader:
    """Handles image loading with fallbacks."""

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
