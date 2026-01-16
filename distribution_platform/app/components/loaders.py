"""
Loading overlay components.
"""

import streamlit as st
import streamlit.components.v1 as components

from distribution_platform.app.components.images import ImageLoader


class LoaderOverlay:
    """Loading overlay components for different scenarios."""

    _TRANSITION_SHIELD_CSS = """
        <style>
            /* Global transition shield - prevents white flash */
            html, body, .stApp {
                background: #030305 !important;
            }

            /* Immediate dark overlay while page loads */
            .stApp::before {
                content: '';
                position: fixed;
                top: 0;
                left: 0;
                width: 100vw;
                height: 100vh;
                background: #030305;
                z-index: 99990;
                pointer-events: none;
                animation: fadeOutShield 0.5s ease-out 0.3s forwards;
            }

            @keyframes fadeOutShield {
                to { opacity: 0; visibility: hidden; }
            }
        </style>
    """

    @staticmethod
    def inject_transition_shield():
        """Inject CSS that prevents white flash during page transitions."""
        st.markdown(LoaderOverlay._TRANSITION_SHIELD_CSS, unsafe_allow_html=True)

    @staticmethod
    def static(
        title: str = "SYSTEM PROCESSING",
        subtitle: str = "Calculating optimal topology...",
    ):
        """Static full-screen loader (no JS detection)."""

        logo_src = ImageLoader._get_logo_img()

        logo_html = (
            f'<img src="{logo_src}" style="width: 100px; height: auto; opacity: 0.9;">'
            if logo_src
            else ""
        )

        st.markdown(
            f"""
            <style>
                @import url('https://fonts.googleapis.com/css2?family=Rajdhani:wght@300;500;700&family=JetBrains+Mono:wght@400&display=swap');

                html, body, .stApp {{
                    background: #030305 !important;
                }}

                .static-loader-overlay {{
                    position: fixed;
                    top: 0; left: 0;
                    width: 100vw; height: 100vh;
                    background: #030305;
                    z-index: 999999;
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    justify-content: center;
                }}
                .static-loader-logo {{
                    position: relative;
                    width: 120px; height: 120px;
                    margin: 0 auto 30px;
                }}
                .static-logo-ring {{
                    position: absolute;
                    width: 100%; height: 100%;
                    border: 2px solid transparent;
                    border-top-color: #6366f1;
                    border-radius: 50%;
                    animation: static-spin 1.5s linear infinite;
                }}
                .static-logo-ring.ring-2 {{
                    width: 80%; height: 80%;
                    top: 10%; left: 10%;
                    border-top-color: #06b6d4;
                    animation-direction: reverse;
                    animation-duration: 1s;
                }}
                .static-logo-core {{
                    position: absolute;
                    top: 50%; left: 50%;
                    transform: translate(-50%, -50%);
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    width: 100%;
                    height: 100%;
                }}
                .static-loader-title {{
                    font-family: 'Rajdhani', sans-serif;
                    font-size: 2.5rem; color: white;
                    margin: 0 0 10px 0;
                    text-transform: uppercase;
                    letter-spacing: 0.1em;
                }}
                .static-loader-subtitle {{
                    color: #a1a1aa;
                    font-family: 'JetBrains Mono', monospace;
                    font-size: 0.9rem; margin: 0;
                }}
                .static-scanner-line {{
                    width: 300px; height: 3px;
                    background: #1f1f22;
                    position: relative; overflow: hidden;
                    margin: 25px auto; border-radius: 3px;
                }}
                .static-scanner-line::after {{
                    content: '';
                    position: absolute;
                    left: 0; top: 0;
                    height: 100%; width: 40%;
                    background: linear-gradient(90deg, transparent, #6366f1, #06b6d4, transparent);
                    animation: static-scan 1.5s infinite linear;
                }}
                .static-loader-dots {{
                    display: flex;
                    justify-content: center;
                    gap: 8px; margin-top: 10px;
                }}
                .static-loader-dots span {{
                    width: 8px; height: 8px;
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
                <div class="static-loader-logo">
                    <div class="static-logo-ring"></div>
                    <div class="static-logo-ring ring-2"></div>
                    <div class="static-logo-core">
                        {logo_html}
                    </div>
                </div>
                <h1 class="static-loader-title">{title}</h1>
                <p class="static-loader-subtitle">{subtitle}</p>
                <div class="static-scanner-line"></div>
                <div class="static-loader-dots">
                    <span></span><span></span><span></span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    @staticmethod
    def persistent_map_loader():
        """Loader that hides when map is detected. Includes transition shield."""

        logo_src = ImageLoader._get_logo_img()
        logo_html = (
            f'<img src="{logo_src}" style="width: 100px; height: auto; opacity: 0.9;">'
            if logo_src
            else "SC"
        )

        st.markdown(
            f"""
            <style>
                @import url('https://fonts.googleapis.com/css2?family=Rajdhani:wght@300;500;700&family=JetBrains+Mono:wght@400&display=swap');

                html, body, .stApp {{
                    background: #030305 !important;
                }}

                #persistentMapLoader {{
                    position: fixed;
                    top: 0; left: 0;
                    width: 100vw; height: 100vh;
                    background: #030305;
                    z-index: 999999;
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    justify-content: center;
                    opacity: 1; visibility: visible;
                    transition: opacity 0.8s ease-out, visibility 0.8s ease-out;
                }}
                #persistentMapLoader.loader-hidden {{
                    opacity: 0;
                    visibility: hidden;
                    pointer-events: none;
                }}
                .persist-loader-logo {{
                    position: relative;
                    width: 120px; height: 120px;
                    margin-bottom: 30px;
                }}
                .persist-logo-ring {{
                    position: absolute;
                    width: 100%; height: 100%;
                    border: 2px solid transparent;
                    border-top-color: #6366f1;
                    border-radius: 50%;
                    animation: persist-spin 1.5s linear infinite;
                }}
                .persist-logo-ring.ring-2 {{
                    width: 80%; height: 80%;
                    top: 10%; left: 10%;
                    border-top-color: #06b6d4;
                    animation-direction: reverse;
                    animation-duration: 1s;
                }}
                .persist-logo-core {{
                    position: absolute;
                    top: 50%; left: 50%;
                    transform: translate(-50%, -50%);
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    width: 100%;
                    height: 100%;

                    font-family: 'Rajdhani', sans-serif;
                    font-size: 28px; font-weight: 700;
                    color: #6366f1;
                    text-shadow: 0 0 20px rgba(99, 102, 241, 0.5);
                }}
                .persist-loader-title {{
                    font-family: 'Rajdhani', sans-serif;
                    font-size: 2.5rem; color: white;
                    margin: 0 0 10px 0;
                    text-transform: uppercase;
                    letter-spacing: 0.1em;
                }}
                .persist-loader-subtitle {{
                    color: #a1a1aa;
                    font-family: 'JetBrains Mono', monospace;
                    font-size: 0.9rem; margin: 0;
                }}
                .persist-loader-status {{
                    color: #6366f1;
                    font-family: 'JetBrains Mono', monospace;
                    font-size: 0.75rem;
                    margin-top: 30px; opacity: 0.8;
                    min-height: 20px;
                }}
                .persist-scanner-line {{
                    width: 300px; height: 3px;
                    background: #1f1f22;
                    position: relative; overflow: hidden;
                    margin: 25px auto; border-radius: 3px;
                }}
                .persist-scanner-line::after {{
                    content: '';
                    position: absolute;
                    left: 0; top: 0;
                    height: 100%; width: 40%;
                    background: linear-gradient(90deg, transparent, #6366f1, #06b6d4, transparent);
                    animation: persist-scan 1.5s infinite linear;
                }}
                .persist-loader-dots {{
                    display: flex;
                    justify-content: center;
                    gap: 8px; margin-top: 10px;
                }}
                .persist-loader-dots span {{
                    width: 8px; height: 8px;
                    background: #6366f1;
                    border-radius: 50%;
                    animation: persist-pulse-dot 1.4s infinite ease-in-out;
                }}
                .persist-loader-dots span:nth-child(2) {{ animation-delay: 0.2s; }}
                .persist-loader-dots span:nth-child(3) {{ animation-delay: 0.4s; }}

                @keyframes persist-spin {{ to {{ transform: rotate(360deg); }} }}
                @keyframes persist-scan {{ 0% {{ left: -40%; }} 100% {{ left: 100%; }} }}
                @keyframes persist-pulse-dot {{
                    0%, 80%, 100% {{ transform: scale(0.6); opacity: 0.5; }}
                    40% {{ transform: scale(1); opacity: 1; }}
                }}
            </style>

            <div id="persistentMapLoader">
                <div class="persist-loader-logo">
                    <div class="persist-logo-ring"></div>
                    <div class="persist-logo-ring ring-2"></div>
                    <div class="persist-logo-core">
                        {logo_html}
                    </div>
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
    def inject_map_detector():
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
                                overlay.classList.add('loader-hidden');
                            }
                        } catch (e) {}
                    }

                    function checkMapLoaded() {
                        try {
                            const iframes = parentDoc.querySelectorAll('iframe');
                            for (let iframe of iframes) {
                                const srcdoc = iframe.srcdoc || '';
                                if (srcdoc.includes('leaflet') || srcdoc.includes('folium') || srcdoc.includes('L.map')) {
                                    updateStatus('Map container detected...');
                                    return true;
                                }
                            }
                            const leafletElements = parentDoc.querySelectorAll('.folium-map, [class*="leaflet"]');
                            if (leafletElements.length > 0) return true;
                        } catch (e) {}
                        return false;
                    }

                    let attempts = 0;
                    const maxAttempts = 120;

                    function poll() {
                        attempts++;
                        updateStatus('Loading map... (' + Math.round(attempts * 0.1) + 's)');

                        if (checkMapLoaded()) {
                            updateStatus('Finalizing render...');
                            setTimeout(hideOverlay, 2000);
                            return;
                        }

                        if (attempts < maxAttempts) {
                            setTimeout(poll, 100);
                        } else {
                            hideOverlay();
                        }
                    }

                    setTimeout(poll, 500);
                    setTimeout(hideOverlay, 15000); // Ultimate fallback
                })();
            </script>
            """,
            height=0,
        )
