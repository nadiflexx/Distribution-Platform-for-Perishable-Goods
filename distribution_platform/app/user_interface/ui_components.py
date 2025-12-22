import math
import os
import random
import time

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

# --- Internal Core Imports ---
from distribution_platform.config.settings import MapConfig, Paths
from distribution_platform.core.inference_engine.engine import InferenceMotor
from distribution_platform.core.knowledge_base import rules
from distribution_platform.core.knowledge_base.rules import (
    parse_truck_data,
)
from distribution_platform.core.models.optimization import SimulationConfig
from distribution_platform.core.services.etl_service import run_etl
from distribution_platform.core.services.optimization_orchestrator import (
    OptimizationOrchestrator,
)
from distribution_platform.infrastructure.external.maps import SpainMapRoutes
from distribution_platform.infrastructure.persistence.truck_repository import (
    TruckRepository,
)

# Initialize Repository
repository = TruckRepository()

# Supported file types for data upload
SUPPORTED_FILE_TYPES = ["csv", "txt", "xlsx"]

# ==============================================================================
#   VISUAL COMPONENT LIBRARY
# ==============================================================================


class UI:
    """Static library for reusable UI components matching the CSS theme."""

    @staticmethod
    def card(title, icon, content_fn=None):
        st.markdown(
            f"""
        <div class="pro-card animate-in">
            <div class="card-header">
                <span class="card-icon">{icon}</span>
                <span class="card-title">{title}</span>
            </div>
        """,
            unsafe_allow_html=True,
        )
        if content_fn:
            content_fn()
        st.markdown("</div>", unsafe_allow_html=True)

    @staticmethod
    def section_header(icon, title):
        """Renders a properly formatted section header."""
        st.markdown(
            f"""
            <div class="section-header">
                <span class="section-icon">{icon}</span>
                <span class="section-title">{title}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    @staticmethod
    def loading_overlay_static(
        title="SYSTEM PROCESSING", subtitle="Calculating optimal topology..."
    ):
        """Static loading overlay using pure HTML/CSS (renders immediately)."""
        st.markdown(
            f"""
            <style>
                @import url('https://fonts.googleapis.com/css2?family=Rajdhani:wght@300;500;700&family=JetBrains+Mono:wght@400&display=swap');
                
                .static-loader-overlay {{
                    position: fixed;
                    top: 0;
                    left: 0;
                    width: 100vw;
                    height: 100vh;
                    background: #030305;
                    z-index: 999999;
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    justify-content: center;
                }}
                
                .static-loader-content {{
                    text-align: center;
                }}
                
                .static-loader-logo {{
                    position: relative;
                    width: 120px;
                    height: 120px;
                    margin: 0 auto 30px;
                }}
                
                .static-logo-ring {{
                    position: absolute;
                    width: 100%;
                    height: 100%;
                    border: 2px solid transparent;
                    border-top-color: #6366f1;
                    border-radius: 50%;
                    animation: static-spin 1.5s linear infinite;
                }}
                
                .static-logo-ring.ring-2 {{
                    width: 80%;
                    height: 80%;
                    top: 10%;
                    left: 10%;
                    border-top-color: #06b6d4;
                    animation-direction: reverse;
                    animation-duration: 1s;
                }}
                
                .static-logo-core {{
                    position: absolute;
                    top: 50%;
                    left: 50%;
                    transform: translate(-50%, -50%);
                    font-family: 'Rajdhani', sans-serif;
                    font-size: 28px;
                    font-weight: 700;
                    color: #6366f1;
                    text-shadow: 0 0 20px rgba(99, 102, 241, 0.5);
                }}
                
                .static-loader-title {{
                    font-family: 'Rajdhani', sans-serif;
                    font-size: 2.5rem;
                    color: white;
                    margin: 0 0 10px 0;
                    text-transform: uppercase;
                    letter-spacing: 0.1em;
                }}
                
                .static-loader-subtitle {{
                    color: #a1a1aa;
                    font-family: 'JetBrains Mono', monospace;
                    font-size: 0.9rem;
                    margin: 0;
                }}
                
                .static-scanner-line {{
                    width: 300px;
                    height: 3px;
                    background: #1f1f22;
                    position: relative;
                    overflow: hidden;
                    margin: 25px auto;
                    border-radius: 3px;
                }}
                
                .static-scanner-line::after {{
                    content: '';
                    position: absolute;
                    left: 0;
                    top: 0;
                    height: 100%;
                    width: 40%;
                    background: linear-gradient(90deg, transparent, #6366f1, #06b6d4, transparent);
                    animation: static-scan 1.5s infinite linear;
                }}
                
                .static-loader-dots {{
                    display: flex;
                    justify-content: center;
                    gap: 8px;
                    margin-top: 10px;
                }}
                
                .static-loader-dots span {{
                    width: 8px;
                    height: 8px;
                    background: #6366f1;
                    border-radius: 50%;
                    animation: static-pulse-dot 1.4s infinite ease-in-out;
                }}
                
                .static-loader-dots span:nth-child(2) {{ animation-delay: 0.2s; }}
                .static-loader-dots span:nth-child(3) {{ animation-delay: 0.4s; }}
                
                @keyframes static-spin {{ to {{ transform: rotate(360deg); }} }}
                @keyframes static-scan {{ 0% {{ left: -40%; }} 100% {{ left: 100%; }} }}
                @keyframes static-pulse-dot {{
                    0%, 80%, 100% {{ transform: scale(0.6); opacity: 0.5; }}
                    40% {{ transform: scale(1); opacity: 1; }}
                }}
            </style>
            
            <div class="static-loader-overlay">
                <div class="static-loader-content">
                    <div class="static-loader-logo">
                        <div class="static-logo-ring"></div>
                        <div class="static-logo-ring ring-2"></div>
                        <div class="static-logo-core">BC</div>
                    </div>
                    <h1 class="static-loader-title">{title}</h1>
                    <p class="static-loader-subtitle">{subtitle}</p>
                    <div class="static-scanner-line"></div>
                    <div class="static-loader-dots">
                        <span></span><span></span><span></span>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    @staticmethod
    def inject_persistent_loader():
        """
        Injects a loading overlay that persists until the map is fully loaded.
        Uses CSS-only hiding (no DOM manipulation) to avoid conflicts with Streamlit.
        """
        st.markdown(
            """
            <style>
                @import url('https://fonts.googleapis.com/css2?family=Rajdhani:wght@300;500;700&family=JetBrains+Mono:wght@400&display=swap');
                
                #persistentMapLoader {
                    position: fixed;
                    top: 0;
                    left: 0;
                    width: 100vw;
                    height: 100vh;
                    background: #030305;
                    z-index: 999999;
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    justify-content: center;
                    opacity: 1;
                    visibility: visible;
                    transition: opacity 0.8s ease-out, visibility 0.8s ease-out;
                }
                
                #persistentMapLoader.loader-hidden {
                    opacity: 0;
                    visibility: hidden;
                    pointer-events: none;
                }
                
                .persist-loader-logo {
                    position: relative;
                    width: 120px;
                    height: 120px;
                    margin-bottom: 30px;
                }
                
                .persist-logo-ring {
                    position: absolute;
                    width: 100%;
                    height: 100%;
                    border: 2px solid transparent;
                    border-top-color: #6366f1;
                    border-radius: 50%;
                    animation: persist-spin 1.5s linear infinite;
                }
                
                .persist-logo-ring.ring-2 {
                    width: 80%;
                    height: 80%;
                    top: 10%;
                    left: 10%;
                    border-top-color: #06b6d4;
                    animation-direction: reverse;
                    animation-duration: 1s;
                }
                
                .persist-logo-core {
                    position: absolute;
                    top: 50%;
                    left: 50%;
                    transform: translate(-50%, -50%);
                    font-family: 'Rajdhani', sans-serif;
                    font-size: 28px;
                    font-weight: 700;
                    color: #6366f1;
                    text-shadow: 0 0 20px rgba(99, 102, 241, 0.5);
                }
                
                .persist-loader-title {
                    font-family: 'Rajdhani', sans-serif;
                    font-size: 2.5rem;
                    color: white;
                    margin: 0 0 10px 0;
                    text-transform: uppercase;
                    letter-spacing: 0.1em;
                }
                
                .persist-loader-subtitle {
                    color: #a1a1aa;
                    font-family: 'JetBrains Mono', monospace;
                    font-size: 0.9rem;
                    margin: 0;
                }
                
                .persist-loader-status {
                    color: #6366f1;
                    font-family: 'JetBrains Mono', monospace;
                    font-size: 0.75rem;
                    margin-top: 30px;
                    opacity: 0.8;
                    min-height: 20px;
                }
                
                .persist-scanner-line {
                    width: 300px;
                    height: 3px;
                    background: #1f1f22;
                    position: relative;
                    overflow: hidden;
                    margin: 25px auto;
                    border-radius: 3px;
                }
                
                .persist-scanner-line::after {
                    content: '';
                    position: absolute;
                    left: 0;
                    top: 0;
                    height: 100%;
                    width: 40%;
                    background: linear-gradient(90deg, transparent, #6366f1, #06b6d4, transparent);
                    animation: persist-scan 1.5s infinite linear;
                }
                
                .persist-loader-dots {
                    display: flex;
                    justify-content: center;
                    gap: 8px;
                    margin-top: 10px;
                }
                
                .persist-loader-dots span {
                    width: 8px;
                    height: 8px;
                    background: #6366f1;
                    border-radius: 50%;
                    animation: persist-pulse-dot 1.4s infinite ease-in-out;
                }
                
                .persist-loader-dots span:nth-child(2) { animation-delay: 0.2s; }
                .persist-loader-dots span:nth-child(3) { animation-delay: 0.4s; }
                
                @keyframes persist-spin { to { transform: rotate(360deg); } }
                @keyframes persist-scan { 0% { left: -40%; } 100% { left: 100%; } }
                @keyframes persist-pulse-dot {
                    0%, 80%, 100% { transform: scale(0.6); opacity: 0.5; }
                    40% { transform: scale(1); opacity: 1; }
                }
            </style>
            
            <div id="persistentMapLoader">
                <div class="persist-loader-logo">
                    <div class="persist-logo-ring"></div>
                    <div class="persist-logo-ring ring-2"></div>
                    <div class="persist-logo-core">BC</div>
                </div>
                <h1 class="persist-loader-title">ENGINE OPTIMIZATION</h1>
                <p class="persist-loader-subtitle">Rendering Geospatial Topology...</p>
                <div class="persist-scanner-line"></div>
                <div class="persist-loader-dots">
                    <span></span><span></span><span></span>
                </div>
                <div class="persist-loader-status" id="persistLoaderStatus">Initializing visualization engine...</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    @staticmethod
    def inject_map_detector_script():
        """
        Injects JavaScript that detects when the map is loaded and hides the overlay.
        Only uses CSS class toggle - no DOM manipulation to avoid Streamlit conflicts.
        """
        components.html(
            """
            <script>
                (function() {
                    const parentDoc = window.parent.document;
                    
                    function updateStatus(msg) {
                        try {
                            const status = parentDoc.getElementById('persistLoaderStatus');
                            if (status) status.textContent = msg;
                        } catch (e) {}
                    }
                    
                    function hideOverlay() {
                        try {
                            const overlay = parentDoc.getElementById('persistentMapLoader');
                            if (overlay && !overlay.classList.contains('loader-hidden')) {
                                updateStatus('Visualization ready!');
                                // Only add CSS class - don't manipulate DOM
                                overlay.classList.add('loader-hidden');
                            }
                        } catch (e) {
                            console.log('Overlay hide error:', e);
                        }
                    }
                    
                    function checkMapLoaded() {
                        try {
                            const iframes = parentDoc.querySelectorAll('iframe');
                            
                            for (let iframe of iframes) {
                                try {
                                    const srcdoc = iframe.srcdoc || '';
                                    const src = iframe.src || '';
                                    
                                    // Check for Leaflet/Folium map
                                    if (srcdoc.includes('leaflet') || srcdoc.includes('folium') || 
                                        srcdoc.includes('L.map') || src.includes('leaflet')) {
                                        
                                        updateStatus('Map container detected...');
                                        
                                        // Try to check tiles inside iframe
                                        try {
                                            const iframeDoc = iframe.contentDocument || iframe.contentWindow?.document;
                                            if (iframeDoc) {
                                                const tiles = iframeDoc.querySelectorAll('.leaflet-tile-loaded');
                                                if (tiles.length > 2) {
                                                    updateStatus('Map tiles loaded!');
                                                    return true;
                                                }
                                            }
                                        } catch (e) {
                                            // Cross-origin - assume map is loading
                                        }
                                        
                                        return true;
                                    }
                                } catch (e) {}
                            }
                            
                            // Check for any Leaflet elements
                            const leafletElements = parentDoc.querySelectorAll('.folium-map, [class*="leaflet"]');
                            if (leafletElements.length > 0) {
                                updateStatus('Leaflet elements found...');
                                return true;
                            }
                            
                        } catch (e) {}
                        
                        return false;
                    }
                    
                    // Polling mechanism
                    let attempts = 0;
                    const maxAttempts = 120; // 12 seconds max
                    const startTime = Date.now();
                    
                    function poll() {
                        attempts++;
                        const elapsed = Date.now() - startTime;
                        
                        updateStatus('Loading map... (' + Math.round(elapsed/1000) + 's)');
                        
                        if (checkMapLoaded()) {
                            // Map found - wait for tiles to render
                            updateStatus('Finalizing render...');
                            setTimeout(hideOverlay, 2000);
                            return;
                        }
                        
                        if (attempts < maxAttempts) {
                            setTimeout(poll, 100);
                        } else {
                            updateStatus('Ready');
                            hideOverlay();
                        }
                    }
                    
                    // Start polling
                    setTimeout(poll, 500);
                    
                    // Fallback timeout
                    setTimeout(function() {
                        try {
                            const overlay = parentDoc.getElementById('persistentMapLoader');
                            if (overlay && !overlay.classList.contains('loader-hidden')) {
                                hideOverlay();
                            }
                        } catch (e) {}
                    }, 15000);
                    
                })();
            </script>
            """,
            height=0,
        )

    @staticmethod
    def truck_hero(image_source, data):
        c_img, c_specs = st.columns([1.5, 1])
        with c_img:
            st.markdown('<div class="truck-hero">', unsafe_allow_html=True)
            UI.load_image(image_source, width="stretch")
            st.markdown("</div>", unsafe_allow_html=True)
        with c_specs:
            st.markdown(
                f"""
            <div class="spec-grid">
                <div class="spec-item">
                    <div class="spec-label">Capacity</div>
                    <div class="spec-value">{data.get("capacidad", 0):,} <span class="spec-unit">kg</span></div>
                </div>
                <div class="spec-item">
                    <div class="spec-label">Consumption</div>
                    <div class="spec-value">{data.get("consumo", 0)} <span class="spec-unit">L/100km</span></div>
                </div>
                <div class="spec-item">
                    <div class="spec-label">Speed</div>
                    <div class="spec-value">{data.get("velocidad_constante", 0)} <span class="spec-unit">km/h</span></div>
                </div>
                <div class="spec-item">
                    <div class="spec-label">Driver Cost</div>
                    <div class="spec-value">{data.get("precio_conductor_hora", 0)} <span class="spec-unit">€/h</span></div>
                </div>
            </div>""",
                unsafe_allow_html=True,
            )

    @staticmethod
    def timeline(route_list):
        if not route_list:
            return
        items_html = ""
        for i, stop in enumerate(route_list):
            is_start, is_end = (i == 0), (i == len(route_list) - 1)
            if is_start:
                tag = "ORIGIN"
                icon = "🏭"
                tag_class = "tag-origin"
            elif is_end:
                tag = "RETURN"
                icon = "🏁"
                tag_class = "tag-return"
            else:
                tag = f"STOP {i}"
                icon = "📦"
                tag_class = "tag-stop"

            items_html += f"""
            <div class="timeline-item">
                <div class="timeline-marker">
                    <span class="timeline-icon">{icon}</span>
                    <div class="timeline-line"></div>
                </div>
                <div class="timeline-body">
                    <span class="timeline-tag {tag_class}">{tag}</span>
                    <div class="timeline-content">{stop}</div>
                </div>
            </div>"""
        st.markdown(
            f"""<div class="timeline-container">{items_html}</div>""",
            unsafe_allow_html=True,
        )

    @staticmethod
    def kpi_card(icon, label, value, unit="", delta=None, delta_color="normal"):
        delta_html = ""
        if delta is not None:
            color = "#10b981" if delta_color == "normal" else "#ef4444"
            arrow = "↑" if delta >= 0 else "↓"
            delta_html = f'<div class="kpi-delta" style="color:{color}">{arrow} {abs(delta)}%</div>'

        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-icon">{icon}</div>
                <div class="kpi-label">{label}</div>
                <div class="kpi-value">{value}<span class="kpi-unit">{unit}</span></div>
                {delta_html}
            </div>
            """,
            unsafe_allow_html=True,
        )

    @staticmethod
    def load_image(img_input, width=None):
        try:
            use_container_width = False
            if width == "stretch":
                use_container_width = True
                width = None

            if hasattr(img_input, "type"):
                st.image(
                    img_input, use_container_width=use_container_width, width=width
                )
            elif os.path.exists(str(img_input)):
                st.image(
                    str(img_input), use_container_width=use_container_width, width=width
                )
            else:
                st.markdown(
                    """<div class="no-image">
                        <span>📷</span>
                        <p>NO VISUAL</p>
                    </div>""",
                    unsafe_allow_html=True,
                )
        except:
            st.error("Image Error")


# ==============================================================================
#   STATE MANAGEMENT
# ==============================================================================


def init_state():
    """Initializes session state. Preserves form data between reloads."""
    defaults = {
        "app_phase": "SPLASH",
        "load_success": False,
        "truck_validated": False,
        "df": None,
        "selected_truck_data": None,
        "ia_result": None,
        # UI selector persistence
        "sel_cat": "Heavy Duty",
        "sel_model": None,
        "sel_custom_db": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


# ==============================================================================
#   VIEWS
# ==============================================================================


def view_splash_screen():
    UI.loading_overlay_static("BRAINCORE LOGISTICS", "Initializing components...")
    time.sleep(2.5)
    st.session_state.app_phase = "FORM"
    st.rerun()


def view_processing_screen():
    """Processing phase - computes results then transitions to results view."""
    UI.loading_overlay_static(
        "ENGINE OPTIMIZATION", "Solving VRP Matrix & Computing Routes..."
    )

    result = _execute_simulation_logic()

    if result:
        st.session_state.ia_result = result
        st.session_state.app_phase = "RESULTS"
        st.rerun()
    else:
        time.sleep(3)
        st.session_state.app_phase = "FORM"
        st.rerun()


def view_form_page():
    st.markdown(
        """
        <div class="page-header animate-in">
            <div class="header-icon">🎯</div>
            <h1>MISSION CONTROL</h1>
            <p class="header-subtitle">Fleet & Cargo Configuration Center</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    c1, c2 = st.columns([1, 1.8], gap="large")

    # --- DATA INGESTION ---
    with c1:

        def render_data():
            conn = st.radio(
                "SOURCE",
                ["Database", "Files"],
                horizontal=True,
                label_visibility="collapsed",
            )
            files = {}
            if conn == "Files":
                st.markdown(
                    """
                    <div class="upload-section-header">
                        <span>📂</span> REQUIRED DATASETS
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                st.caption("Supported formats: CSV, TXT, XLSX")

                files["pedidos"] = st.file_uploader(
                    "📦 Orders (Pedidos)",
                    type=SUPPORTED_FILE_TYPES,
                    key="upload_pedidos",
                )
                files["clientes"] = st.file_uploader(
                    "👥 Clients (Clientes)",
                    type=SUPPORTED_FILE_TYPES,
                    key="upload_clientes",
                )
                files["lineas_pedido"] = st.file_uploader(
                    "📋 Order Lines (Líneas de Pedido)",
                    type=SUPPORTED_FILE_TYPES,
                    key="upload_lineas",
                )
                files["productos"] = st.file_uploader(
                    "🏷️ Products (Productos)",
                    type=SUPPORTED_FILE_TYPES,
                    key="upload_productos",
                )
                files["destinos"] = st.file_uploader(
                    "📍 Destinations (Destinos)",
                    type=SUPPORTED_FILE_TYPES,
                    key="upload_destinos",
                )
                files["provincias"] = st.file_uploader(
                    "🗺️ Provinces (Provincias)",
                    type=SUPPORTED_FILE_TYPES,
                    key="upload_provincias",
                )

            st.markdown("<div style='height: 20px'></div>", unsafe_allow_html=True)

            if st.button(
                "⚡ SYNC DATA STREAM", type="secondary", use_container_width=True
            ):
                _load_data_logic(conn, files)

        UI.card("DATA INGESTION", "💾", render_data)

    # --- FLEET CONFIGURATION ---
    with c2:

        def render_fleet():
            if not st.session_state.load_success:
                st.markdown(
                    """
                    <div class="awaiting-data">
                        <span class="pulse-icon">📡</span>
                        <p>Awaiting Data Stream...</p>
                        <small>Sync data to unlock fleet configuration</small>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                return

            cat = st.selectbox(
                "VEHICLE CLASS",
                ["Heavy Duty", "Medium Duty", "Custom Prototype"],
                index=["Heavy Duty", "Medium Duty", "Custom Prototype"].index(
                    st.session_state.sel_cat
                ),
                key="cat_selector",
            )
            st.session_state.sel_cat = cat

            if cat == "Custom Prototype":
                _render_custom_form_logic()
            else:
                cat_key = "large" if "Heavy" in cat else "medium"
                trucks = repository.get_trucks(cat_key)

                idx = 0
                if st.session_state.sel_model in trucks:
                    idx = list(trucks.keys()).index(st.session_state.sel_model)

                model = st.selectbox(
                    "MODEL SELECTION",
                    list(trucks.keys()),
                    index=idx,
                    key="model_selector",
                )
                st.session_state.sel_model = model

                if model:
                    data = trucks[model]
                    img_path = Paths.TRUCK_IMAGES[cat_key] / data["imagen"]

                    current_truck = data | {"nombre": model, "imagen": str(img_path)}

                    if st.session_state.selected_truck_data != current_truck:
                        st.session_state.selected_truck_data = current_truck
                        st.session_state.truck_validated = False

                    UI.truck_hero(img_path, data)

            st.markdown("<div style='height: 20px'></div>", unsafe_allow_html=True)

            if st.session_state.truck_validated:
                st.markdown(
                    """
                    <div class="validation-success">
                        <span>✅</span> VEHICLE VERIFIED & READY
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            else:
                if st.button(
                    "🔒 VERIFY VEHICLE INTEGRITY",
                    type="primary",
                    use_container_width=True,
                ):
                    _validate_truck_logic()

        UI.card("FLEET CONFIGURATION", "🚛", render_fleet)

    # --- LAUNCH SECTION ---
    if st.session_state.truck_validated and st.session_state.load_success:
        st.markdown("<div class='launch-divider'></div>", unsafe_allow_html=True)

        _, cm, _ = st.columns([1, 2, 1])
        with cm:
            st.markdown(
                """
                <div class="launch-section">
                    <div class="launch-ready-badge">
                        <span class="pulse-dot"></span>
                        SYSTEMS READY
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            st.selectbox(
                "ALGORITHM",
                ["Genetic Evolutionary", "Google OR-Tools"],
                key="algo_select",
                label_visibility="collapsed",
            )

            if st.button(
                "🚀 INITIATE SEQUENCE", type="primary", use_container_width=True
            ):
                st.session_state.app_phase = "PROCESSING"
                st.rerun()


def view_results_page():
    """
    Results page with persistent loading overlay.
    Overlay is injected FIRST and hidden via CSS class (no DOM manipulation).
    """
    ia = st.session_state.ia_result

    # =========================================================================
    # STEP 1: INJECT LOADING OVERLAY FIRST (covers everything immediately)
    # =========================================================================
    UI.inject_persistent_loader()

    # =========================================================================
    # STEP 2: RENDER ALL PAGE CONTENT (happens behind the overlay)
    # =========================================================================

    st.markdown(
        """
        <div class="results-header animate-in">
            <h1>🏁 MISSION RESULTS</h1>
            <p class="results-subtitle">Optimization Complete • Routes Generated</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col_back, _ = st.columns([1, 5])
    with col_back:
        if st.button("← BACK TO CONTROL", type="secondary"):
            st.session_state.app_phase = "FORM"
            st.rerun()

    # KPI Section
    st.markdown("<div class='kpi-section'>", unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        UI.kpi_card("🚛", "Active Fleet", ia["num_trucks"], " units")
    with c2:
        UI.kpi_card("📏", "Total Distance", f"{ia['total_distancia']:,.0f}", " km")
    with c3:
        UI.kpi_card("💰", "Operating Cost", f"{ia['total_coste']:,.0f}", " €")
    with c4:
        UI.kpi_card("📈", "Net Profit", f"{ia['total_beneficio']:,.0f}", " €")
    st.markdown("</div>", unsafe_allow_html=True)

    # Tabs with Map
    tab_geo, tab_detail = st.tabs(["🌍 GEOSPATIAL MAP", "🔍 ROUTE INSPECTOR"])

    with tab_geo:
        st.markdown("<div class='map-container'>", unsafe_allow_html=True)
        SpainMapRoutes().render(ia["routes"])
        st.markdown("</div>", unsafe_allow_html=True)

    with tab_detail:
        trucks = [
            v
            for k, v in ia["resultados_detallados"].items()
            if k != "pedidos_no_entregables"
        ]
        if not trucks:
            st.warning("No routes generated.")
        else:
            sel_id = st.selectbox(
                "SELECT UNIT",
                [t.camion_id for t in trucks],
                format_func=lambda x: f"🚛 UNIT-{x:03d}",
            )

            truck = next((t for t in trucks if t.camion_id == sel_id), None)

            if truck:
                st.markdown("<div class='route-detail-grid'>", unsafe_allow_html=True)
                c_tl, c_map = st.columns([1, 2])

                with c_tl:
                    UI.section_header("📍", "Itinerary Trace")
                    UI.timeline(truck.ciudades_ordenadas)

                with c_map:
                    UI.section_header("🗺️", "Route Topology")
                    r_single = [r for r in ia["routes"] if r["camion_id"] == sel_id]
                    SpainMapRoutes().render(r_single)

                    st.markdown(
                        "<div style='margin-top: 24px;'>", unsafe_allow_html=True
                    )
                    UI.section_header("📦", "Cargo Manifest")
                    data_t = [
                        {
                            "Order ID": p.pedido_id,
                            "Destination": p.destino,
                            "Weight (kg)": f"{p.cantidad_producto:,}",
                        }
                        for p in truck.lista_pedidos_ordenada
                    ]
                    st.dataframe(
                        pd.DataFrame(data_t),
                        use_container_width=True,
                        hide_index=True,
                        column_config={
                            "Order ID": st.column_config.TextColumn(
                                "Order ID", width="small"
                            ),
                            "Destination": st.column_config.TextColumn(
                                "Destination", width="medium"
                            ),
                            "Weight (kg)": st.column_config.TextColumn(
                                "Weight", width="small"
                            ),
                        },
                    )
                    st.markdown("</div>", unsafe_allow_html=True)

                st.markdown("</div>", unsafe_allow_html=True)

    # =========================================================================
    # STEP 3: INJECT MAP DETECTOR (hides overlay when map is ready)
    # =========================================================================
    UI.inject_map_detector_script()


# ==============================================================================
#   LOGIC HELPERS
# ==============================================================================


def _render_custom_form_logic():
    custom_trucks = repository.get_trucks("custom")
    options = ["+ CREATE NEW PROTOTYPE"] + list(custom_trucks.keys())

    idx = 0
    if st.session_state.sel_custom_db in options:
        idx = options.index(st.session_state.sel_custom_db)

    selection = st.selectbox(
        "PROTOTYPE DATABASE", options, index=idx, key="custom_selector"
    )
    st.session_state.sel_custom_db = selection

    if selection == "+ CREATE NEW PROTOTYPE":
        st.markdown(
            "<div class='new-prototype-form'>",
            unsafe_allow_html=True,
        )
        c1, c2 = st.columns([1, 1.5])
        with c1:
            uploaded_img = st.file_uploader(
                "Upload Schematic", type=["png", "jpg"], label_visibility="collapsed"
            )
            if uploaded_img:
                st.image(uploaded_img, width=180)
        with c2:
            name = st.text_input("Prototype ID", value="X-1")
            cap = st.number_input("Capacity (kg)", value=1000, min_value=100)
            fuel = st.number_input(
                "Fuel Consumption (L/100km)", value=25.0, min_value=1.0
            )
            spd = st.number_input("Cruise Speed (km/h)", value=90.0, min_value=20.0)
            cost = st.number_input("Driver Cost (€/h)", value=20.0, min_value=5.0)

        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<div style='height: 15px'></div>", unsafe_allow_html=True)

        if st.button("💾 SAVE TO DATABASE", type="secondary", use_container_width=True):
            img_filename = repository.save_image(uploaded_img, name)
            truck_data = {
                "capacidad": cap,
                "consumo": fuel,
                "velocidad_constante": spd,
                "precio_conductor_hora": cost,
                "imagen": img_filename,
            }
            repository.save_custom_truck(name, truck_data)

            full_img_path = Paths.TRUCK_IMAGES["custom"] / img_filename

            st.session_state.selected_truck_data = truck_data | {
                "nombre": name,
                "imagen": str(full_img_path),
            }
            st.session_state.truck_validated = False
            st.session_state.sel_custom_db = name

            st.toast("Prototype Saved Successfully", icon="✅")
            st.rerun()
    else:
        data = custom_trucks[selection]
        img_path = Paths.TRUCK_IMAGES["custom"] / data.get("imagen", "default.png")

        current_truck = data | {"nombre": selection, "imagen": str(img_path)}

        if st.session_state.selected_truck_data != current_truck:
            st.session_state.selected_truck_data = current_truck
            st.session_state.truck_validated = False

        UI.truck_hero(img_path, data)


def _load_data_logic(conn, files):
    try:
        with st.spinner("Synchronizing data streams..."):
            if conn == "Database":
                st.session_state.df = run_etl(use_database=False)
            else:
                required_files = [
                    "pedidos",
                    "clientes",
                    "lineas_pedido",
                    "productos",
                    "destinos",
                    "provincias",
                ]
                missing = [f for f in required_files if not files.get(f)]

                if missing:
                    missing_names = ", ".join(missing)
                    st.error(f"❌ Missing required files: {missing_names}")
                    return

                st.session_state.df = run_etl(uploaded_files=files)

        st.session_state.load_success = True
        st.session_state.truck_validated = False
        st.rerun()
        st.toast("Data Stream Synchronized", icon="✅")
    except Exception as e:
        st.error(f"❌ ETL Failure: {e}")


def _validate_truck_logic():
    d = st.session_state.selected_truck_data
    if not d:
        st.warning("⚠️ Select a vehicle first")
        return

    valid, obj = parse_truck_data(d)
    if not valid:
        st.error(f"❌ {obj['error']}")
        return

    res = InferenceMotor(rules.obtain_rules()).evaluate(obj)
    if res.is_valid:
        st.session_state.truck_validated = True
        st.toast("Vehicle Validated Successfully", icon="🛡️")
        st.rerun()
    else:
        st.error("❌ Validation Failed - Vehicle does not meet requirements")


def _execute_simulation_logic():
    try:
        algo = (
            "ortools"
            if "OR-Tools" in st.session_state.get("algo_select", "")
            else "genetic"
        )
        t_data = st.session_state.selected_truck_data

        if not t_data:
            return None

        orders_flat = [order for group in st.session_state.df for order in group]
        total_load = sum(o.cantidad_producto for o in orders_flat)
        total_orders = len(orders_flat)

        truck_cap = float(t_data.get("capacidad", 1000))
        if truck_cap < 100 and total_load > 10000:
            truck_cap *= 1000

        needed_trucks = math.ceil(total_load / truck_cap) if truck_cap > 0 else 9999
        if needed_trucks > total_orders:
            st.error(
                f"⚠️ CAPACITY ERROR: {truck_cap}kg capacity insufficient for {total_orders} orders."
            )
            return None

        cfg = SimulationConfig(
            velocidad_constante=float(t_data.get("velocidad_constante", 90)),
            consumo_combustible=float(t_data.get("consumo", 30)),
            capacidad_carga=truck_cap,
            salario_conductor_hora=float(t_data.get("precio_conductor_hora", 20)),
        )

        orch = OptimizationOrchestrator(config=cfg, origin_base="Mataró")
        raw = orch.optimize_deliveries(st.session_state.df, algorithm=algo)

        routes = []
        full = {}
        td, tc, tb = 0, 0, 0

        for k, v in raw.items():
            if k == "pedidos_no_entregables" or v is None:
                continue

            color = random.choice(MapConfig.ROUTE_COLORS)
            routes.append(
                {
                    "path": v.ruta_coordenadas,
                    "color": color,
                    "pedidos": v.lista_pedidos_ordenada,
                    "camion_id": v.camion_id,
                    "tiempos_llegada": v.tiempos_llegada,
                }
            )
            td += v.distancia_total_km
            tc += v.coste_total_ruta
            tb += v.beneficio_neto
            full[k] = v

        assigns = []
        for r in full.values():
            for p in r.lista_pedidos_ordenada:
                assigns.append(
                    {
                        "Truck": r.camion_id,
                        "ID": p.pedido_id,
                        "Dest": p.destino,
                        "Kg": p.cantidad_producto,
                    }
                )

        return {
            "num_trucks": len(full),
            "routes": routes,
            "assignments": pd.DataFrame(assigns),
            "total_distancia": round(td, 2),
            "total_coste": round(tc, 2),
            "total_beneficio": round(tb, 2),
            "resultados_detallados": full,
            "pedidos_imposibles": raw.get("pedidos_no_entregables", pd.DataFrame()),
        }
    except Exception as e:
        print(f"CRITICAL SIMULATION ERROR: {e}")
        st.error(f"❌ System Error: {e}")
        return None
