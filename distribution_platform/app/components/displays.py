"""
Display components: headers, timelines, etc.
"""

import streamlit as st


class SectionHeader:
    """Section header with icon."""

    @staticmethod
    def render(icon: str, title: str):
        st.markdown(
            f"""<div class="section-header"><span class="section-icon">{icon}</span><span class="section-title">{title}</span></div>""",
            unsafe_allow_html=True,
        )


class PageHeader:
    """Page header with icon and subtitle."""

    @staticmethod
    def render(icon: str, title: str, subtitle: str):
        st.markdown(
            f"""
            <div class="page-header animate-in">
                <div class="header-icon">{icon}</div>
                <h1>{title}</h1>
                <p class="header-subtitle">{subtitle}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )


class Timeline:
    """Route timeline display."""

    @staticmethod
    def render(route_list: list[str]):
        if not route_list:
            return

        # Build HTML without extra whitespace/newlines that break rendering
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

            # Build each item as a single concatenated string (no f-string newlines)
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
        st.markdown(
            """<div class="validation-success"><span>✅</span> VEHICLE VERIFIED & READY</div>""",
            unsafe_allow_html=True,
        )

    @staticmethod
    def awaiting():
        st.markdown(
            """<div class="awaiting-data"><span class="pulse-icon">📡</span><p>Awaiting Data Stream...</p><small>Sync data to unlock fleet configuration</small></div>""",
            unsafe_allow_html=True,
        )


class LaunchSection:
    """Launch ready badge and section."""

    @staticmethod
    def render():
        st.markdown("<div class='launch-divider'></div>", unsafe_allow_html=True)
        st.markdown(
            """<div class="launch-section"><div class="launch-ready-badge"><span class="pulse-dot"></span>SYSTEMS READY</div></div>""",
            unsafe_allow_html=True,
        )
