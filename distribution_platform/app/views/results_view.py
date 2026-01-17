"""
Results/Dashboard View - Final Version (Refactored & Complete)
"""

from datetime import datetime, timedelta
from typing import Any
from urllib.parse import quote

import pandas as pd
import streamlit as st

from distribution_platform.app.components.cards import KPICard
from distribution_platform.app.components.charts import AlgorithmVisualizer
from distribution_platform.app.components.displays import (
    PageHeader,
    SectionHeader,
    Timeline,
)
from distribution_platform.app.components.export import ExportHub
from distribution_platform.app.components.images import ImageLoader
from distribution_platform.app.components.loaders import LoaderOverlay
from distribution_platform.app.config.constants import AppPhase
from distribution_platform.app.state.session_manager import SessionManager
from distribution_platform.infrastructure.external.maps import SpainMapRoutes


class ResultsView:
    """Optimization results dashboard with full analytics."""

    def render(self):
        result = SessionManager.get("ia_result")

        # Inject loader first
        LoaderOverlay.persistent_map_loader()

        self._render_header(result)
        self._render_main_kpis(result)
        self._render_tabs(result)

        # Inject map detector
        LoaderOverlay.inject_map_detector()

    def _render_header(self, result: dict):
        PageHeader.render(
            ImageLoader._get_logo_img(),
            "MISSION CONTROL",
            "Fleet & Cargo Configuration Center",
        )

        col_back, _, col_actions = st.columns([1, 2, 2])
        with col_back:
            if st.button("← BACK TO CONTROL", type="secondary"):
                SessionManager.set_phase(AppPhase.FORM)

        with col_actions:
            _, col_exp2 = st.columns(2)
            with col_exp2:
                ExportHub.render(result)

    def _export_results_button(self):
        result = SessionManager.get("ia_result")
        if result and "assignments" in result:
            csv = result["assignments"].to_csv(index=False)
            st.download_button(
                label="📥 EXPORT CSV",
                data=csv,
                file_name="route_assignments.csv",
                mime="text/csv",
                width="stretch",
            )

    def _render_main_kpis(self, result: dict):
        st.markdown("<div class='kpi-section'>", unsafe_allow_html=True)

        cols = st.columns(6)

        trucks_data = [
            v
            for k, v in result["resultados_detallados"].items()
            if k != "pedidos_no_entregables"
        ]
        total_orders = sum(len(t.lista_pedidos_ordenada) for t in trucks_data)
        avg_distance = (
            result["total_distancia"] / len(trucks_data) if trucks_data else 0
        )
        efficiency = (
            (result["total_beneficio"] / result["total_coste"] * 100)
            if result["total_coste"] > 0
            else 0
        )

        kpis = [
            ("🚛", "Active Fleet", result["num_trucks"], " units"),
            ("📦", "Total Orders", total_orders, " delivered"),
            ("📏", "Total Distance", f"{result['total_distancia']:,.0f}", " km"),
            ("⚡", "Avg/Truck", f"{avg_distance:,.0f}", " km"),
            ("💰", "Operating Cost", f"{result['total_coste']:,.0f}", " €"),
            ("📈", "Net Profit", f"{result['total_beneficio']:,.0f}", " €"),
        ]

        for col, (icon, label, value, unit) in zip(cols, kpis, strict=False):
            with col:
                KPICard.render(icon, label, value, unit)

        st.markdown("</div>", unsafe_allow_html=True)

        self._render_efficiency_bar(efficiency, result)

    def _render_efficiency_bar(self, efficiency: float, result: dict):
        profit_ratio = (
            result["total_beneficio"]
            / (result["total_coste"] + result["total_beneficio"])
            * 100
            if (result["total_coste"] + result["total_beneficio"]) > 0
            else 0
        )

        st.markdown(
            f"""
            <div class="efficiency-section">
                <div class="efficiency-header">
                    <span class="efficiency-label">💹 PROFIT EFFICIENCY</span>
                    <span class="efficiency-value">{efficiency:.1f}% ROI</span>
                </div>
                <div class="efficiency-bar-container">
                    <div class="efficiency-bar-bg">
                        <div class="efficiency-bar-fill" style="width: {min(profit_ratio, 100)}%"></div>
                    </div>
                    <div class="efficiency-labels">
                        <span>Cost: €{result["total_coste"]:,.0f}</span>
                        <span>Profit: €{result["total_beneficio"]:,.0f}</span>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    def _render_tabs(self, result: dict):
        tab_geo, tab_inspector, tab_orders, tab_algo = st.tabs(
            [
                "🌍 GEOSPATIAL MAP",
                "🔍 ROUTE INSPECTOR",
                "📦 ORDER MANIFEST",
                "🧬 ALGORITHM & CLUSTERING",
            ]
        )

        with tab_geo:
            self._render_geospatial_tab(result)

        with tab_algo:
            self._render_algorithm_tab(result)

        with tab_orders:
            self._render_orders_tab(result)

        with tab_inspector:
            self._render_route_inspector_tab(result)

    def _render_geospatial_tab(self, result: dict):
        st.markdown("<div class='map-container'>", unsafe_allow_html=True)
        SpainMapRoutes().render(result["routes"])
        st.markdown("</div>", unsafe_allow_html=True)

    def _render_algorithm_tab(self, result: dict):
        st.info(
            "This section visualizes the two phases of Artificial Intelligence: Clustering and Routing."
        )

        # Recuperar imágenes cacheadas
        plots = result.get("plots", {})
        cluster_img = plots.get("clustering")
        routes_img = plots.get("routes")

        # --- FASE 1: CLUSTERING ---
        SectionHeader.render("🧠", "Phase 1: Zonification (Clustering)")

        col_c1, col_c2 = st.columns([3, 1])
        with col_c2:
            st.markdown(f"""
            **Objective:** Divide orders into logical zones.

            **Algorithm:** {result.get("clustering_strategy", "N/A")}

            **What we see:** Polygons that define the delivery area for each driver.
            """)

        with col_c1:
            if cluster_img:
                st.image(f"data:image/png;base64,{cluster_img}", width="stretch")
            else:
                st.warning("Clustering visualization not available.")

        st.markdown("---")

        # --- FASE 2: ROUTING ---
        SectionHeader.render("🚛", "Phase 2: Sequencing (Routing)")

        col_r1, col_r2 = st.columns([3, 1])
        with col_r2:
            st.markdown(f"""
            **Objective:** Order stops to minimize km and time.

            **Algorithm:** {result.get("routing_algorithm", "N/A")}

            **What we see:** The traced line indicates the exact path. Arrows indicate flow direction.
            """)

        with col_r1:
            if routes_img:
                st.image(f"data:image/png;base64,{routes_img}", width="stretch")
            else:
                st.warning("The route map could not be generated.")

        st.markdown("---")

        with st.expander("Watch the process calculation animation (Graph)"):
            traces = result.get("algorithm_trace", {})
            if traces:
                truck_options = list(traces.keys())
                selected_truck = st.selectbox(
                    "Select Truck",
                    options=truck_options,
                    format_func=lambda x: f"🚛 {x.upper().replace('_', ' ')}",
                )
                if selected_truck:
                    AlgorithmVisualizer.render_graph_animation(
                        traces[selected_truck], container_key=selected_truck
                    )

    def _render_orders_tab(self, result: dict):
        """Enhanced Order Manifest with full details."""
        trucks_data = [
            v
            for k, v in result["resultados_detallados"].items()
            if k != "pedidos_no_entregables"
        ]

        # === PRODUCT RECONSTRUCTION ENGINE ===
        original_data_source = SessionManager.get("df")
        product_master_map: dict[int, list[dict[str, Any]]] = {}

        if original_data_source:
            all_raw_orders = [o for sublist in original_data_source for o in sublist]

            for o in all_raw_orders:
                oid = o.pedido_id
                if oid not in product_master_map:
                    product_master_map[oid] = []

                item_name = getattr(
                    o,
                    "producto_nombre",
                    getattr(o, "nombre_producto", getattr(o, "producto", "Unknown")),
                )
                item_qty = getattr(o, "cantidad_producto", getattr(o, "cantidad", 1))
                item_price = getattr(
                    o, "precio_unitario", getattr(o, "precio_venta", 0)
                )

                product_master_map[oid].append(
                    {"nombre": item_name, "cantidad": item_qty, "precio": item_price}
                )

        # Build complete orders list
        all_orders = []
        base_time = datetime.now().replace(hour=8, minute=0, second=0, microsecond=0)

        for truck in trucks_data:
            cumulative_time = 0
            for i, pedido in enumerate(truck.lista_pedidos_ordenada):
                if i < len(truck.tiempos_llegada):
                    eta_str = truck.tiempos_llegada[i]
                else:
                    cumulative_time += 45
                    eta = base_time + timedelta(minutes=cumulative_time)
                    eta_str = eta.strftime("%H:%M")

                # Attributes extraction
                email = getattr(pedido, "email_cliente", "N/A") or "N/A"
                price = (
                    getattr(pedido, "precio_venta", getattr(pedido, "precio", 0)) or 0
                )
                priority = getattr(pedido, "prioridad", "Normal") or "Normal"

                # === USE MASTER MAP IF AVAILABLE ===
                products = []
                product_names = []

                if pedido.pedido_id in product_master_map:
                    raw_products = product_master_map[pedido.pedido_id]
                    for p in raw_products:
                        products.append(
                            {
                                "nombre": p["nombre"],
                                "cantidad": p["cantidad"],
                                "precio": p["precio"],
                            }
                        )
                        product_names.append(p["nombre"])
                else:
                    raw_lines = getattr(pedido, "lineas", []) or getattr(
                        pedido, "productos", []
                    )
                    if raw_lines:
                        for line in raw_lines:
                            p_name = getattr(
                                line,
                                "producto_nombre",
                                getattr(line, "nombre", "Unknown"),
                            )
                            p_qty = getattr(line, "cantidad", 1)
                            p_price = getattr(line, "precio", 0)
                            products.append(
                                {"nombre": p_name, "cantidad": p_qty, "precio": p_price}
                            )
                            product_names.append(p_name)
                    else:
                        p_name = getattr(pedido, "producto_nombre", "General Cargo")
                        products = [{"nombre": p_name, "cantidad": 1, "precio": price}]
                        product_names = [p_name]

                all_orders.append(
                    {
                        "truck_id": truck.camion_id,
                        "order_id": pedido.pedido_id,
                        "destination": pedido.destino,
                        "weight": pedido.cantidad_producto,
                        "eta": eta_str,
                        "price": float(price),
                        "email_cliente": email,
                        "priority": priority,
                        "status": "Scheduled",
                        "stop_number": i + 1,
                        "products": products,
                        "product_names": product_names,
                        "fecha_pedido": getattr(pedido, "fecha_pedido", None),
                    }
                )

        orders_df = pd.DataFrame(all_orders)

        SectionHeader.render("📦", "Complete Order Manifest")

        # Search
        col_f1, col_f2 = st.columns([1, 2])
        with col_f1:
            search = st.text_input("🔎 Search", placeholder="Order ID, Email...")

        filtered_df = orders_df.copy()
        if search:
            s = search.lower()
            filtered_df = filtered_df[
                filtered_df["order_id"].astype(str).str.contains(s)
                | filtered_df["email_cliente"].str.lower().str.contains(s)
            ]

        # Main Table
        display_df = filtered_df[
            [
                "order_id",
                "truck_id",
                "destination",
                "weight",
                "price",
                "eta",
                "priority",
                "email_cliente",
            ]
        ].copy()
        display_df["truck_id"] = display_df["truck_id"].apply(lambda x: f"UNIT-{x:03d}")
        display_df["price"] = display_df["price"].apply(lambda x: f"€{x:,.2f}")
        display_df["weight"] = display_df["weight"].apply(lambda x: f"{x:,} kg")
        display_df.columns = [
            "📋 Order",
            "🚛 Truck",
            "📍 Destination",
            "⚖️ Weight",
            "💰 Value",
            "🕐 ETA",
            "⚡ Priority",
            "📧 Client",
        ]

        st.dataframe(display_df, width="stretch", hide_index=True, height=300)

        st.markdown("---")

        # === ORDER DETAIL VIEWER ===
        SectionHeader.render("🔎", "Order Detail Viewer")

        # Selector moved to top
        selected_order_id = st.selectbox(
            "Select Order to View Details",
            options=filtered_df["order_id"].tolist(),
            format_func=lambda x: f"📦 Order #{x}",
            index=None,
            placeholder="Choose an order...",
        )

        if selected_order_id:
            st.markdown("<br>", unsafe_allow_html=True)
            order_data = filtered_df[filtered_df["order_id"] == selected_order_id].iloc[
                0
            ]

            # Info Cards
            col_i1, col_i2, col_i3, col_i4 = st.columns(4)
            with col_i1:
                st.markdown(
                    f"""<div class="order-info-card"><div class="info-icon">📋</div><div class="info-content"><span class="info-label">Order ID</span><span class="info-value">#{order_data["order_id"]}</span></div></div>""",
                    unsafe_allow_html=True,
                )
            with col_i2:
                st.markdown(
                    f"""<div class="order-info-card"><div class="info-icon">🕐</div><div class="info-content"><span class="info-label">ETA</span><span class="info-value">{order_data["eta"]}</span></div></div>""",
                    unsafe_allow_html=True,
                )
            with col_i3:
                priority_colors = {
                    "Normal": "#3b82f6",
                    "High": "#f59e0b",
                    "Urgent": "#ef4444",
                }
                color = priority_colors.get(order_data["priority"], "#6366f1")
                st.markdown(
                    f"""<div class="order-info-card" style="border-left-color: {color};"><div class="info-icon">⚡</div><div class="info-content"><span class="info-label">Priority</span><span class="info-value" style="color: {color};">{order_data["priority"]}</span></div></div>""",
                    unsafe_allow_html=True,
                )

            # Details Layout
            col_left, col_right = st.columns([1, 1.5], gap="large")

            with col_left:
                st.markdown(
                    f"""
                    <div class="order-detail-card">
                        <h4>📍 Delivery Information</h4>
                        <div class="detail-grid">
                            <div class="detail-item full-width"><span class="detail-label">Destination</span><span class="detail-value">{order_data["destination"]}</span></div>
                            <div class="detail-item"><span class="detail-label">Assigned Truck</span><span class="detail-value">UNIT-{order_data["truck_id"]:03d}</span></div>
                            <div class="detail-item"><span class="detail-label">Stop Number</span><span class="detail-value">#{order_data["stop_number"]}</span></div>
                            <div class="detail-item"><span class="detail-label">Status</span><span class="detail-value status-scheduled">✅ {order_data["status"]}</span></div>
                            <div class="detail-item"><span class="detail-label">Date</span><span class="detail-value">{order_data.get("fecha_pedido", "N/A") or "Today"}</span></div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                st.markdown("<br>", unsafe_allow_html=True)

                st.markdown(
                    f"""
                    <div class="order-detail-card">
                        <h4>👤 Client Information</h4>
                        <div class="detail-grid">
                            <div class="detail-item full-width">
                                <span class="detail-label">Email</span>
                                <span class="detail-value">{order_data["email_cliente"]}</span>
                            </div>
                        </div>
                        <br>
                        {"<a href='mailto:" + order_data["email_cliente"] + "?subject=Order " + str(order_data["order_id"]) + "' class='custom-button primary' target='_blank'>📧 Contact Client</a>" if order_data["email_cliente"] != "N/A" else "<div class='custom-button disabled'>📧 No Email</div>"}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            with col_right:
                product_list_html = "<ul style='margin: 0; padding-left: 20px; color: white; font-size: 0.85rem; max-height: 150px; overflow-y: auto;'>"
                for name in order_data["product_names"]:
                    product_list_html += f"<li>{name}</li>"
                product_list_html += "</ul>"

                st.markdown(
                    f"""
                    <div class="order-detail-card">
                        <h4>💰 Financial Summary</h4>
                        <div class="detail-grid">
                            <div class="detail-item"><span class="detail-label">Total Value</span><span class="detail-value">€{order_data["price"]:,.2f}</span></div>
                            <div class="detail-item"><span class="detail-label">Total Weight</span><span class="detail-value">{order_data["weight"]:,} kg</span></div>
                            <div class="detail-item full-width" style="grid-column: 1 / -1;">
                                <span class="detail-label">Included Items</span>
                                <div class="detail-value" style="margin-top: 8px;">
                                    {product_list_html}
                                </div>
                            </div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    def _render_route_inspector_tab(self, result: dict):
        trucks = [
            v
            for k, v in result["resultados_detallados"].items()
            if k != "pedidos_no_entregables"
        ]

        if not trucks:
            st.warning("No routes generated.")
            return

        col_sel, col_preview = st.columns([1, 2])

        with col_sel:
            sel_id = st.selectbox(
                "SELECT UNIT",
                [t.camion_id for t in trucks],
                format_func=lambda x: f"🚛 UNIT-{x:03d}",
            )

        truck = next((t for t in trucks if t.camion_id == sel_id), None)

        with col_preview:
            if truck:
                (
                    (truck.beneficio_neto / truck.coste_total_ruta * 100)
                    if truck.coste_total_ruta > 0
                    else 0
                )
                st.markdown(
                    f"""<div class="truck-preview-bar"><span>📏 {truck.distancia_total_km:,.1f} km</span><span>📦 {len(truck.lista_pedidos_ordenada)} orders</span><span>💰 €{truck.coste_total_ruta:,.2f} cost</span></div>""",
                    unsafe_allow_html=True,
                )

        if not truck:
            return

        st.markdown("---")

        col_left, col_right = st.columns([1, 2])

        with col_left:
            SectionHeader.render("📍", "Itinerary Trace")
            Timeline.render(truck.ciudades_ordenadas)

            st.markdown("<div style='margin-top: 20px;'>", unsafe_allow_html=True)
            maps_url = self._generate_google_maps_url(truck)
            st.markdown(
                f"""<a href="{maps_url}" target="_blank" class="custom-button primary" style="display:block;text-align:center;">🧭 START NAVIGATION</a>""",
                unsafe_allow_html=True,
            )

            st.markdown(
                f"""
                <div class="route-stats-card">
                    <h5>📊 Route Statistics</h5>
                    <div class="stat-row"><span>Total Distance</span><strong>{truck.distancia_total_km:,.1f} km</strong></div>
                    <div class="stat-row"><span>Estimated Duration</span><strong>{truck.distancia_total_km / 80:.1f} hrs</strong></div>
                    <div class="stat-row"><span>Fuel Estimate</span><strong>{truck.distancia_total_km * 0.3:.0f} L</strong></div>
                    <div class="stat-row"><span>Operating Cost</span><strong>€{truck.coste_total_ruta:,.2f}</strong></div>
                    <div class="stat-row highlight"><span>Net Profit</span><strong>€{truck.beneficio_neto:,.2f}</strong></div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with col_right:
            SectionHeader.render("🗺️", "Route Topology")
            route_single = [r for r in result["routes"] if r["camion_id"] == sel_id]
            SpainMapRoutes().render(route_single)

            st.markdown("<div style='margin-top: 24px;'>", unsafe_allow_html=True)
            SectionHeader.render("📦", "Cargo Manifest & Schedule")

            cargo_data = []
            for i, pedido in enumerate(truck.lista_pedidos_ordenada):
                eta = (
                    truck.tiempos_llegada[i]
                    if i < len(truck.tiempos_llegada)
                    else "N/A"
                )
                cargo_data.append(
                    {
                        "Stop": i + 1,
                        "Order ID": pedido.pedido_id,
                        "Destination": pedido.destino,
                        "Weight (kg)": pedido.cantidad_producto,
                        "ETA": eta,
                    }
                )

            st.dataframe(pd.DataFrame(cargo_data), width="stretch", hide_index=True)

            total_weight = sum(
                p.cantidad_producto for p in truck.lista_pedidos_ordenada
            )
            st.markdown(
                f"""<div class="cargo-summary"><span>📦 <strong>{len(truck.lista_pedidos_ordenada)}</strong> orders</span><span>⚖️ <strong>{total_weight:,}</strong> kg total</span></div>""",
                unsafe_allow_html=True,
            )
            st.markdown("</div>", unsafe_allow_html=True)

    def _generate_google_maps_url(self, truck) -> str:
        coords = truck.ruta_coordenadas

        if not coords or len(coords) < 2:
            return "https://www.google.com/maps"

        origin = f"{coords[0][0]},{coords[0][1]}"
        destination = f"{coords[-1][0]},{coords[-1][1]}"

        waypoints = []
        for i, coord in enumerate(coords[1:-1]):
            if i < 10:
                waypoints.append(f"{coord[0]},{coord[1]}")

        waypoints_str = "|".join(waypoints) if waypoints else ""

        url = f"https://www.google.com/maps/dir/?api=1&origin={origin}&destination={destination}"
        if waypoints_str:
            url += f"&waypoints={quote(waypoints_str)}"
        url += "&travelmode=driving"

        return url
