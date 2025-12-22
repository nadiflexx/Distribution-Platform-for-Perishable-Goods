"""
Results/Dashboard View - Complete Version
"""

from urllib.parse import quote

import pandas as pd
import streamlit as st

from distribution_platform.app.components.cards import KPICard
from distribution_platform.app.components.displays import SectionHeader, Timeline
from distribution_platform.app.components.loaders import LoaderOverlay
from distribution_platform.app.config.constants import AppPhase
from distribution_platform.app.state.session_manager import SessionManager
from distribution_platform.infrastructure.external.maps import SpainMapRoutes


class ResultsView:
    """Optimization results dashboard with full analytics."""

    def render(self):
        result = SessionManager.get("ia_result")

        # Inject loader first (covers screen)
        LoaderOverlay.persistent_map_loader()

        # Render content behind loader
        self._render_header()
        self._render_main_kpis(result)
        self._render_tabs(result)

        # Inject map detector (hides loader when ready)
        LoaderOverlay.inject_map_detector()

    def _render_header(self):
        st.markdown(
            """
            <div class="results-header animate-in">
                <h1>🏁 MISSION RESULTS</h1>
                <p class="results-subtitle">Optimization Complete • Routes Generated</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        col_back, col_space, col_actions = st.columns([1, 3, 2])
        with col_back:
            if st.button("← BACK TO CONTROL", type="secondary"):
                SessionManager.set_phase(AppPhase.FORM)

        with col_actions:
            col_exp1, col_exp2 = st.columns(2)
            with col_exp1:
                if st.button(
                    "📥 EXPORT CSV", type="secondary", use_container_width=True
                ):
                    self._export_results()
            with col_exp2:
                if st.button(
                    "🔄 RE-OPTIMIZE", type="secondary", use_container_width=True
                ):
                    SessionManager.set_phase(AppPhase.PROCESSING)

    def _render_main_kpis(self, result: dict):
        st.markdown("<div class='kpi-section'>", unsafe_allow_html=True)

        cols = st.columns(6)

        # Calculate additional metrics
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

        for col, (icon, label, value, unit) in zip(cols, kpis):
            with col:
                KPICard.render(icon, label, value, unit)

        st.markdown("</div>", unsafe_allow_html=True)

        # Efficiency bar
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
        tab_geo, tab_fleet, tab_orders, tab_inspector = st.tabs(
            [
                "🌍 GEOSPATIAL MAP",
                "📊 FLEET ANALYTICS",
                "📦 ORDER MANIFEST",
                "🔍 ROUTE INSPECTOR",
            ]
        )

        with tab_geo:
            self._render_geospatial_tab(result)

        with tab_fleet:
            self._render_fleet_analytics_tab(result)

        with tab_orders:
            self._render_orders_tab(result)

        with tab_inspector:
            self._render_route_inspector_tab(result)

    def _render_geospatial_tab(self, result: dict):
        st.markdown("<div class='map-container'>", unsafe_allow_html=True)
        SpainMapRoutes().render(result["routes"])
        st.markdown("</div>", unsafe_allow_html=True)

    def _render_fleet_analytics_tab(self, result: dict):
        trucks_data = [
            v
            for k, v in result["resultados_detallados"].items()
            if k != "pedidos_no_entregables"
        ]

        if not trucks_data:
            st.warning("No fleet data available.")
            return

        col_table, col_chart = st.columns([1.5, 1])

        with col_table:
            SectionHeader.render("📋", "Fleet Performance Summary")

            fleet_df = pd.DataFrame(
                [
                    {
                        "Unit": f"UNIT-{t.camion_id:03d}",
                        "Stops": len(t.ciudades_ordenadas)
                        - 2,  # Exclude origin and return
                        "Orders": len(t.lista_pedidos_ordenada),
                        "Distance (km)": f"{t.distancia_total_km:,.1f}",
                        "Cost (€)": f"{t.coste_total_ruta:,.2f}",
                        "Revenue (€)": f"{t.beneficio_neto + t.coste_total_ruta:,.2f}",
                        "Profit (€)": f"{t.beneficio_neto:,.2f}",
                        "Efficiency": f"{(t.beneficio_neto / t.coste_total_ruta * 100) if t.coste_total_ruta > 0 else 0:.1f}%",
                    }
                    for t in trucks_data
                ]
            )

            st.dataframe(
                fleet_df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Unit": st.column_config.TextColumn("🚛 Unit", width="small"),
                    "Stops": st.column_config.NumberColumn("📍 Stops", width="small"),
                    "Orders": st.column_config.NumberColumn("📦 Orders", width="small"),
                    "Distance (km)": st.column_config.TextColumn(
                        "📏 Distance", width="small"
                    ),
                    "Cost (€)": st.column_config.TextColumn("💰 Cost", width="small"),
                    "Revenue (€)": st.column_config.TextColumn(
                        "💵 Revenue", width="small"
                    ),
                    "Profit (€)": st.column_config.TextColumn(
                        "📈 Profit", width="small"
                    ),
                    "Efficiency": st.column_config.TextColumn("⚡ ROI", width="small"),
                },
            )

        with col_chart:
            SectionHeader.render("📊", "Distribution Analysis")

            # Distance distribution
            chart_data = pd.DataFrame(
                {
                    "Unit": [f"U-{t.camion_id:03d}" for t in trucks_data],
                    "Distance": [t.distancia_total_km for t in trucks_data],
                    "Profit": [t.beneficio_neto for t in trucks_data],
                }
            )

            st.bar_chart(chart_data.set_index("Unit")["Distance"], color="#6366f1")
            st.caption("Distance per truck (km)")

            st.bar_chart(chart_data.set_index("Unit")["Profit"], color="#10b981")
            st.caption("Profit per truck (€)")

        # Undelivered orders section
        if not result.get("pedidos_imposibles", pd.DataFrame()).empty:
            st.markdown("---")
            SectionHeader.render("⚠️", "Undeliverable Orders")
            st.warning(
                f"**{len(result['pedidos_imposibles'])} orders** could not be assigned due to capacity constraints."
            )
            with st.expander("View undeliverable orders"):
                st.dataframe(
                    result["pedidos_imposibles"],
                    use_container_width=True,
                    hide_index=True,
                )

    def _render_orders_tab(self, result: dict):
        trucks_data = [
            v
            for k, v in result["resultados_detallados"].items()
            if k != "pedidos_no_entregables"
        ]

        SectionHeader.render("📦", "Complete Order Manifest")

        # Build complete orders dataframe
        all_orders = []
        for truck in trucks_data:
            for i, pedido in enumerate(truck.lista_pedidos_ordenada):
                arrival_time = (
                    truck.tiempos_llegada[i]
                    if i < len(truck.tiempos_llegada)
                    else "N/A"
                )
                all_orders.append(
                    {
                        "truck_id": truck.camion_id,
                        "order_id": pedido.pedido_id,
                        "destination": pedido.destino,
                        "weight": pedido.cantidad_producto,
                        "arrival": arrival_time,
                        # Add more fields if available
                        "price": getattr(
                            pedido, "precio_venta", getattr(pedido, "precio", 0)
                        ),
                        "client": getattr(
                            pedido, "cliente_id", getattr(pedido, "cliente", "N/A")
                        ),
                    }
                )

        orders_df = pd.DataFrame(all_orders)

        # Filters
        col_filter1, col_filter2, col_filter3 = st.columns(3)

        with col_filter1:
            truck_filter = st.multiselect(
                "Filter by Truck",
                options=[f"UNIT-{t.camion_id:03d}" for t in trucks_data],
                default=None,
                placeholder="All trucks",
            )

        with col_filter2:
            dest_filter = st.multiselect(
                "Filter by Destination",
                options=sorted(orders_df["destination"].unique()),
                default=None,
                placeholder="All destinations",
            )

        with col_filter3:
            search = st.text_input(
                "🔍 Search Order ID", placeholder="Enter order ID..."
            )

        # Apply filters
        filtered_df = orders_df.copy()
        if truck_filter:
            truck_ids = [int(t.split("-")[1]) for t in truck_filter]
            filtered_df = filtered_df[filtered_df["truck_id"].isin(truck_ids)]
        if dest_filter:
            filtered_df = filtered_df[filtered_df["destination"].isin(dest_filter)]
        if search:
            filtered_df = filtered_df[
                filtered_df["order_id"].astype(str).str.contains(search, case=False)
            ]

        # Display stats
        st.markdown(
            f"""
            <div class="orders-stats">
                <span>📊 Showing <strong>{len(filtered_df)}</strong> of <strong>{len(orders_df)}</strong> orders</span>
                <span>📦 Total Weight: <strong>{filtered_df["weight"].sum():,.0f} kg</strong></span>
                <span>💰 Total Value: <strong>€{filtered_df["price"].sum():,.2f}</strong></span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Display table
        display_df = filtered_df.copy()
        display_df["truck_id"] = display_df["truck_id"].apply(lambda x: f"UNIT-{x:03d}")
        display_df.columns = [
            "🚛 Truck",
            "📋 Order ID",
            "📍 Destination",
            "⚖️ Weight (kg)",
            "🕐 ETA",
            "💰 Value (€)",
            "👤 Client",
        ]

        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True,
            height=400,
        )

        # Order detail expander
        st.markdown("---")
        SectionHeader.render("🔎", "Order Detail Viewer")

        selected_order = st.selectbox(
            "Select an order to view details",
            options=orders_df["order_id"].tolist(),
            format_func=lambda x: f"Order #{x}",
            index=None,
            placeholder="Choose an order...",
        )

        if selected_order:
            self._render_order_detail(selected_order, trucks_data)

    def _render_order_detail(self, order_id: int, trucks_data: list):
        """Render detailed view of a specific order."""
        # Find the order
        order = None
        parent_truck = None

        for truck in trucks_data:
            for pedido in truck.lista_pedidos_ordenada:
                if pedido.pedido_id == order_id:
                    order = pedido
                    parent_truck = truck
                    break
            if order:
                break

        if not order:
            st.error("Order not found")
            return

        col1, col2 = st.columns(2)

        with col1:
            st.markdown(
                f"""
                <div class="order-detail-card">
                    <h4>📋 Order #{order.pedido_id}</h4>
                    <div class="detail-grid">
                        <div class="detail-item">
                            <span class="detail-label">Destination</span>
                            <span class="detail-value">{order.destino}</span>
                        </div>
                        <div class="detail-item">
                            <span class="detail-label">Weight</span>
                            <span class="detail-value">{order.cantidad_producto:,} kg</span>
                        </div>
                        <div class="detail-item">
                            <span class="detail-label">Assigned Truck</span>
                            <span class="detail-value">UNIT-{parent_truck.camion_id:03d}</span>
                        </div>
                        <div class="detail-item">
                            <span class="detail-label">Client ID</span>
                            <span class="detail-value">{getattr(order, "cliente_id", "N/A")}</span>
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with col2:
            # Products in order (if available)
            productos = getattr(order, "productos", getattr(order, "lineas", None))

            if productos:
                st.markdown("**📦 Products in this order:**")
                if isinstance(productos, list):
                    for prod in productos:
                        prod_name = getattr(
                            prod, "nombre", getattr(prod, "producto", str(prod))
                        )
                        prod_qty = getattr(prod, "cantidad", 1)
                        st.markdown(f"- {prod_name} (x{prod_qty})")
                else:
                    st.info("Product details not available")
            else:
                st.info("Product details not available for this order")

    def _render_route_inspector_tab(self, result: dict):
        trucks = [
            v
            for k, v in result["resultados_detallados"].items()
            if k != "pedidos_no_entregables"
        ]

        if not trucks:
            st.warning("No routes generated.")
            return

        # Truck selector with preview
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
                efficiency = (
                    (truck.beneficio_neto / truck.coste_total_ruta * 100)
                    if truck.coste_total_ruta > 0
                    else 0
                )
                st.markdown(
                    f"""
                    <div class="truck-preview-bar">
                        <span>📏 {truck.distancia_total_km:,.1f} km</span>
                        <span>📦 {len(truck.lista_pedidos_ordenada)} orders</span>
                        <span>💰 €{truck.coste_total_ruta:,.2f} cost</span>
                        <span>📈 €{truck.beneficio_neto:,.2f} profit</span>
                        <span>⚡ {efficiency:.1f}% ROI</span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        if not truck:
            return

        st.markdown("---")

        # Main content
        col_left, col_right = st.columns([1, 2])

        with col_left:
            SectionHeader.render("📍", "Itinerary Trace")
            Timeline.render(truck.ciudades_ordenadas)

            # Navigation button
            st.markdown("<div style='margin-top: 20px;'>", unsafe_allow_html=True)
            if st.button(
                "🧭 START NAVIGATION", type="primary", use_container_width=True
            ):
                maps_url = self._generate_google_maps_url(truck)
                st.markdown(
                    f"""
                    <script>window.open("{maps_url}", "_blank");</script>
                    <div class="nav-link-box">
                        <a href="{maps_url}" target="_blank">🗺️ Open in Google Maps</a>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            st.markdown("</div>", unsafe_allow_html=True)

            # Route stats card
            st.markdown(
                f"""
                <div class="route-stats-card">
                    <h5>📊 Route Statistics</h5>
                    <div class="stat-row">
                        <span>Total Distance</span>
                        <strong>{truck.distancia_total_km:,.1f} km</strong>
                    </div>
                    <div class="stat-row">
                        <span>Estimated Duration</span>
                        <strong>{truck.distancia_total_km / 80:.1f} hrs</strong>
                    </div>
                    <div class="stat-row">
                        <span>Fuel Estimate</span>
                        <strong>{truck.distancia_total_km * 0.3:.0f} L</strong>
                    </div>
                    <div class="stat-row">
                        <span>Operating Cost</span>
                        <strong>€{truck.coste_total_ruta:,.2f}</strong>
                    </div>
                    <div class="stat-row">
                        <span>Total Revenue</span>
                        <strong>€{truck.beneficio_neto + truck.coste_total_ruta:,.2f}</strong>
                    </div>
                    <div class="stat-row highlight">
                        <span>Net Profit</span>
                        <strong>€{truck.beneficio_neto:,.2f}</strong>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with col_right:
            # Map
            SectionHeader.render("🗺️", "Route Topology")
            route_single = [r for r in result["routes"] if r["camion_id"] == sel_id]
            SpainMapRoutes().render(route_single)

            # Cargo manifest with arrival times
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
                        "Value (€)": getattr(
                            pedido, "precio_venta", getattr(pedido, "precio", 0)
                        ),
                    }
                )

            cargo_df = pd.DataFrame(cargo_data)

            st.dataframe(
                cargo_df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Stop": st.column_config.NumberColumn("📍", width="small"),
                    "Order ID": st.column_config.TextColumn("Order", width="small"),
                    "Destination": st.column_config.TextColumn(
                        "Destination", width="medium"
                    ),
                    "Weight (kg)": st.column_config.NumberColumn(
                        "Weight", format="%d kg", width="small"
                    ),
                    "ETA": st.column_config.TextColumn("🕐 ETA", width="small"),
                    "Value (€)": st.column_config.NumberColumn(
                        "Value", format="€%.2f", width="small"
                    ),
                },
            )

            # Summary row
            total_weight = sum(
                p.cantidad_producto for p in truck.lista_pedidos_ordenada
            )
            total_value = sum(
                getattr(p, "precio_venta", getattr(p, "precio", 0))
                for p in truck.lista_pedidos_ordenada
            )

            st.markdown(
                f"""
                <div class="cargo-summary">
                    <span>📦 <strong>{len(truck.lista_pedidos_ordenada)}</strong> orders</span>
                    <span>⚖️ <strong>{total_weight:,}</strong> kg total</span>
                    <span>💰 <strong>€{total_value:,.2f}</strong> total value</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

            st.markdown("</div>", unsafe_allow_html=True)

    def _generate_google_maps_url(self, truck) -> str:
        """Generate Google Maps directions URL for the route."""
        # Get coordinates from the route
        coords = truck.ruta_coordenadas

        if not coords or len(coords) < 2:
            return "https://www.google.com/maps"

        # Origin and destination
        origin = f"{coords[0][0]},{coords[0][1]}"
        destination = f"{coords[-1][0]},{coords[-1][1]}"

        # Waypoints (intermediate stops)
        waypoints = []
        for i, coord in enumerate(coords[1:-1]):
            if i < 10:  # Google Maps limit
                waypoints.append(f"{coord[0]},{coord[1]}")

        waypoints_str = "|".join(waypoints) if waypoints else ""

        url = f"https://www.google.com/maps/dir/?api=1&origin={origin}&destination={destination}"
        if waypoints_str:
            url += f"&waypoints={quote(waypoints_str)}"
        url += "&travelmode=driving"

        return url

    def _export_results(self):
        """Export results to CSV."""
        result = SessionManager.get("ia_result")

        if result and "assignments" in result:
            csv = result["assignments"].to_csv(index=False)
            st.download_button(
                label="📥 Download CSV",
                data=csv,
                file_name="route_assignments.csv",
                mime="text/csv",
            )
            st.toast("Export ready!", icon="✅")
