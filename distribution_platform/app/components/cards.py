"""
Card-based UI components.
"""

from collections.abc import Callable

import streamlit as st

from .images import ImageLoader


class Card:
    """Generic card container."""

    @staticmethod
    def render(title: str, icon: str, content_fn: Callable | None = None):
        st.markdown(
            f"""<div class="pro-card animate-in"><div class="card-header"><span class="card-icon">{icon}</span><span class="card-title">{title}</span></div>""",
            unsafe_allow_html=True,
        )
        if content_fn:
            content_fn()
        st.markdown("</div>", unsafe_allow_html=True)


class KPICard:
    """KPI display card."""

    @staticmethod
    def render(
        icon: str, label: str, value: str, unit: str = "", highlight: bool = False
    ):
        highlight_class = "kpi-highlight" if highlight else ""
        st.markdown(
            f"""<div class="kpi-card {highlight_class}"><div class="kpi-icon">{icon}</div><div class="kpi-label">{label}</div><div class="kpi-value">{value}<span class="kpi-unit">{unit}</span></div></div>""",
            unsafe_allow_html=True,
        )

    @staticmethod
    def render_mini(icon: str, label: str, value: str):
        """Smaller KPI for inline use."""
        st.markdown(
            f"""<div class="kpi-mini"><span class="kpi-mini-icon">{icon}</span><span class="kpi-mini-label">{label}:</span><span class="kpi-mini-value">{value}</span></div>""",
            unsafe_allow_html=True,
        )


class TruckHero:
    """Truck display with specs."""

    @staticmethod
    def render(image_source, data: dict):
        c_img, c_specs = st.columns([1.5, 1])

        with c_img:
            st.markdown('<div class="truck-hero">', unsafe_allow_html=True)
            ImageLoader.render(image_source, width="stretch")
            st.markdown("</div>", unsafe_allow_html=True)

        with c_specs:
            st.markdown(
                f"""<div class="spec-grid"><div class="spec-item"><div class="spec-label">Capacity</div><div class="spec-value">{data.get("capacidad", 0):,} <span class="spec-unit">kg</span></div></div><div class="spec-item"><div class="spec-label">Consumption</div><div class="spec-value">{data.get("consumo", 0)} <span class="spec-unit">L/100km</span></div></div><div class="spec-item"><div class="spec-label">Speed</div><div class="spec-value">{data.get("velocidad_constante", 0)} <span class="spec-unit">km/h</span></div></div><div class="spec-item"><div class="spec-label">Driver Cost</div><div class="spec-value">{data.get("precio_conductor_hora", 0)} <span class="spec-unit">€/h</span></div></div></div>""",
                unsafe_allow_html=True,
            )


class InfoCard:
    """Information display card."""

    @staticmethod
    def render(title: str, items: dict, icon: str = "ℹ️"):
        items_html = "".join(
            [
                f'<div class="info-item"><span class="info-label">{k}</span><span class="info-value">{v}</span></div>'
                for k, v in items.items()
            ]
        )
        st.markdown(
            f"""<div class="info-card"><div class="info-header"><span>{icon}</span> {title}</div>{items_html}</div>""",
            unsafe_allow_html=True,
        )
