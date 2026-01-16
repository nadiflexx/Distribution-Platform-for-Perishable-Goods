"""
Display components: headers, timelines, validation badges, launch sections.
"""

import streamlit as st


class SectionHeader:
    """Section header with icon."""

    @staticmethod
    def render(icon: str, title: str):
        """Renders a section header with an icon and title."""
        st.markdown(
            f"""<div class="section-header"><span class="section-icon">{icon}</span><span class="section-title">{title}</span></div>""",
            unsafe_allow_html=True,
        )


class PageHeader:
    """Renders the main page header with logo support."""

    @staticmethod
    def render(logo_src: str, title: str, subtitle: str):
        """
        Renders a header with a logo and text.

        Args:
            logo_src: The base64 source string (data:image/...) or an emoji.
            title: The main title.
            subtitle: The small subtitle below.
        """

        if logo_src and (
            logo_src.startswith("data:image") or logo_src.startswith("http")
        ):
            logo_html = f'<img src="{logo_src}" class="header-logo">'
        else:
            logo_html = (
                f'<span class="header-emoji">{logo_src}</span>' if logo_src else ""
            )

        st.markdown(
            f"""
            <style>
                .header-container {{
                    display: flex;
                    align-items: center;
                    padding-bottom: 20px;
                    justify-content: center;
                    border-bottom: 1px solid #27272a;
                    margin-bottom: 30px;
                    gap: 20px;
                }}

                .header-logo {{
                    height: 120px;
                    width: auto;
                    object-fit: contain;
                }}

                .header-emoji {{
                    font-size: 4rem;
                }}

                .header-text {{
                    display: flex;
                    flex-direction: column;
                }}

                .header-text h1 {{
                    margin: 0;
                    padding: 0;
                    font-family: 'Rajdhani', sans-serif;
                    font-weight: 700;
                    font-size: 3rem;
                    line-height: 1;
                    text-transform: uppercase;
                    background: linear-gradient(90deg, #fff, #a1a1aa);
                    -webkit-background-clip: text;
                    -webkit-text-fill-color: transparent;
                }}

                .header-text p {{
                    margin: 5px 0 0 0;
                    font-family: 'JetBrains Mono', monospace;
                    font-size: 1rem;
                    color: #a1a1aa;
                    letter-spacing: 0.05em;
                }}
            </style>

            <div class="header-container">
                {logo_html}
                <div class="header-text">
                    <h1>{title}</h1>
                    <p>{subtitle}</p>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


class Timeline:
    """Route timeline display."""

    @staticmethod
    def render(route_list: list[str]):
        """Renders a vertical timeline for the given route list."""
        if not route_list:
            return

        # Build HTML
        items = []
        for i, stop in enumerate(route_list):
            is_start = i == 0
            is_end = i == len(route_list) - 1

            if is_start:
                tag, icon, tag_class = "ORIGIN", "🏭", "tag-origin"
            elif is_end:
                tag, icon, tag_class = "RETURN", "🏁", "tag-return"
            else:
                tag, icon, tag_class = f"STOP {i}", "📦", "tag-stop"

            item_html = (
                '<div class="timeline-item">'
                '<div class="timeline-marker">'
                f'<span class="timeline-icon">{icon}</span>'
                '<div class="timeline-line"></div>'
                "</div>"
                '<div class="timeline-body">'
                f'<span class="timeline-tag {tag_class}">{tag}</span>'
                f'<div class="timeline-content">{stop}</div>'
                "</div>"
                "</div>"
            )
            items.append(item_html)

        # Join all items into container
        full_html = f'<div class="timeline-container">{"".join(items)}</div>'
        st.markdown(full_html, unsafe_allow_html=True)


class ValidationBadge:
    """Success/pending validation display."""

    @staticmethod
    def success():
        """Renders a success validation badge."""
        st.markdown(
            """<div class="validation-success"><span>✅</span> VEHICLE VERIFIED & READY</div>""",
            unsafe_allow_html=True,
        )

    @staticmethod
    def awaiting():
        """Renders an awaiting data stream badge."""
        st.markdown(
            """<div class="awaiting-data"><span class="pulse-icon">📡</span><p>Awaiting Data Stream...</p><small>Sync data to unlock fleet configuration</small></div>""",
            unsafe_allow_html=True,
        )


class LaunchSection:
    """Launch ready badge and section."""

    @staticmethod
    def render():
        """Renders the launch ready section."""
        st.markdown("<div class='launch-divider'></div>", unsafe_allow_html=True)
        st.markdown(
            """<div class="launch-section"><div class="launch-ready-badge"><span class="pulse-dot"></span>SYSTEMS READY</div></div>""",
            unsafe_allow_html=True,
        )
