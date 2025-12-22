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
            use_container_width = width == "stretch"
            actual_width = None if use_container_width else width

            if hasattr(img_input, "type"):
                # Uploaded file
                st.image(
                    img_input,
                    use_container_width=use_container_width,
                    width=actual_width,
                )
            elif os.path.exists(str(img_input)):
                # File path
                st.image(
                    str(img_input),
                    use_container_width=use_container_width,
                    width=actual_width,
                )
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
