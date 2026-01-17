import streamlit as st

from distribution_platform.app.components.loaders import LoaderOverlay
from distribution_platform.app.config.constants import AppPhase, FileNames
from distribution_platform.app.services.data_service import DataService
from distribution_platform.app.services.optimization_service import OptimizationService
from distribution_platform.app.state.session_manager import SessionManager
from distribution_platform.config.settings import Paths


class ProcessingView:
    """Optimization processing screen."""

    def render(self):
        loader_placeholder = st.empty()

        with loader_placeholder.container():
            LoaderOverlay.static(
                "ENGINE OPTIMIZATION", "Solving VRP Matrix & Computing Routes..."
            )

        result = OptimizationService.run()

        if result:
            loader_placeholder.empty()
            SessionManager.set("ia_result", result)
            SessionManager.set_phase(AppPhase.RESULTS)
            st.rerun()

        else:
            loader_placeholder.empty()
            self._render_error_screen()

    def _render_error_screen(self):
        """Renders error screen when optimization fails."""

        try:
            error_img_path = Paths.MEDIA / FileNames.TRUCK_ERROR

            truck_error_b64 = DataService.load_image_base64(error_img_path)
        except Exception:
            truck_error_b64 = (
                "https://via.placeholder.com/400x200/000000/FFFFFF?text=IMAGE+NOT+FOUND"
            )

        st.markdown(
            f"""
            <style>
                /* --- 1. CONTENEDOR PRINCIPAL (LA CLAVE) --- */
                .mission-fail-container {{
                    max-width: 1000px;
                    margin: 0 auto;

                    background-color: #0e0e10;
                    border: 1px solid #331111;
                    border-radius: 12px;
                    padding: 4px;
                    box-shadow: 0 0 40px rgba(255, 50, 50, 0.1);
                }}

                .mission-fail-inner {{
                    background: linear-gradient(180deg, #160404 0%, #080101 100%);
                    border-radius: 8px;
                    padding: 25px;
                    text-align: center;
                    position: relative;
                    overflow: hidden;
                }}

                .mission-fail-inner::before {{
                    content: "";
                    position: absolute;
                    top: 0; left: 0;
                    width: 5px; height: 100%;
                    background: #ff3333;
                    box-shadow: 2px 0 15px #ff3333;
                }}

                .error-title {{
                    font-family: 'Courier New', monospace;
                    color: #ff4b4b;
                    font-size: 50px;
                    font-weight: 900;
                    letter-spacing: 3px;
                    text-transform: uppercase;
                    margin-bottom: 2px;
                    text-shadow: 0 0 10px rgba(255, 75, 75, 0.5);
                }}

                .error-subtitle {{
                    color: #999;
                    font-size: 14px;
                    letter-spacing: 2px;
                    text-transform: uppercase;
                    margin-bottom: 20px;
                    border-bottom: 1px solid #331111;
                    display: inline-block;
                    padding-bottom: 5px;
                }}

                /* --- 2. IMAGEN AL 100% --- */
                .error-img-container {{
                    display: block;
                    width: 100%;
                    border: 1px solid #331111;
                    border-radius: 6px;
                    overflow: hidden; /* Para que la imagen respete el borde */
                }}

                .error-visual {{
                    width: auto;
                    height: auto;
                    display: block;
                    object-fit: cover;
                    opacity: 0.9;
                }}

                .log-box {{
                    background-color: #050505;
                    border: 1px solid #222;
                    border-left: 3px solid #444;
                    border-radius: 4px;
                    padding: 15px;
                    text-align: left;
                    font-family: 'Consolas', monospace;
                    font-size: 12px;
                    color: #a0a0a0;
                    line-height: 1.5;
                }}

                .log-label {{ color: #666; font-weight: bold; font-size: 14px; }}
                .log-val {{ color: #ccc; }}
                .log-error {{ color: #ff5555; font-weight: bold; }}

            </style>


            <div class="mission-fail-container">
                <div class="mission-fail-inner">
                    <div class="error-title">⚠️ MISSION ABORTED</div>
                    <div class="error-subtitle">CRITICAL FLEET CONFIGURATION FAILURE</div>
                    <div class="error-img-container"><img src="data:image/png;base64,{truck_error_b64}"
                    style="width:auto; height:auto;" />
                    </div>
                    <div class="log-box">
                        <span class="log-label">> SYSTEM_STATUS:</span> <span class="log-val">HALTED</span><br>
                        <span class="log-label">> DIAGNOSTIC:</span> <span class="log-error">CAPACITY_OVERFLOW_EXCEPTION</span><br>
                        <span class="log-label">> ROOT_CAUSE:</span> <span class="log-val">Vehicle capacity insufficient for order consolidation.</span><br>
                        <br>
                        <span class="log-label">> SOLUTION:</span> <span class="log-val">Increase truck size or enable load splitting protocols.</span>
                    </div>
                </div>
            </div>
        """,
            unsafe_allow_html=True,
        )

        st.markdown("<br>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button(
                "⬅️ RECONFIGURE FLEET ASSETS", type="primary", use_container_width=True
            ):
                SessionManager.set_phase(AppPhase.FORM)
                st.rerun()
