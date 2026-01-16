"""
Optimization Orchestrator.
Main entry point for the Routing System. Integrates:
- Clustering (K-Means / Agglomerative)
- Graph (Distances)
- Routing Strategies (Genetic / OR-Tools)
"""

from collections import Counter
import math

import matplotlib

from distribution_platform.config.logging_config import log as logger
from distribution_platform.core.logic.graph import GraphManager
from distribution_platform.core.logic.order_processing import consolidate_orders
from distribution_platform.core.logic.routing.clustering import (
    ClusteringManager,
    ClusteringStrategy,
    KMeansStrategy,
)
from distribution_platform.core.logic.routing.strategies.genetic import GeneticStrategy
from distribution_platform.core.logic.routing.strategies.ortools import (
    ORToolsStrategy,
)
from distribution_platform.core.models.optimization import (
    RouteOptimizationResult,
    SimulationConfig,
)
from distribution_platform.core.models.order import Order
from distribution_platform.infrastructure.persistence.coordinates import (
    CoordinateCache,
)

matplotlib.use("Agg")
import base64
import io

import matplotlib.patheffects as pe
import matplotlib.pyplot as plt
import numpy as np


class OptimizationOrchestrator:
    """Main Orchestrator for Delivery Optimization. Integrates Clustering, Graph, and Routing."""

    IMPOSSIBLE_DESTS = {
        "las palmas",
        "santa cruz de tenerife",
        "islas baleares",
        "palma de mallorca",
        "ibiza",
        "menorca",
        "formentera",
        "tenerife",
        "gran canaria",
        "lanzarote",
        "fuerteventura",
        "la palma",
        "la gomera",
        "el hierro",
        "ceuta",
        "melilla",
    }

    def __init__(
        self,
        config: SimulationConfig | None = None,
        origin_base: str = "Mataró",
        coord_cache: CoordinateCache | None = None,
        clustering_strategy: ClusteringStrategy | None = None,
    ):
        """Initializes the Optimization Orchestrator."""
        self.config = config if config else SimulationConfig()
        self.origin = origin_base
        self.coord_cache = coord_cache if coord_cache else CoordinateCache()

        # Initialize clustering with strategy (default: K-Means)
        if clustering_strategy is None:
            clustering_strategy = KMeansStrategy(self.coord_cache)

        self.clustering = ClusteringManager(
            self.coord_cache, strategy=clustering_strategy
        )
        self.graph = GraphManager(self.coord_cache)

    def set_clustering_strategy(self, strategy: ClusteringStrategy) -> None:
        """Change clustering strategy at runtime."""
        self.clustering.set_strategy(strategy)

    def get_clustering_strategy_name(self) -> str:
        """Returns current clustering strategy name."""
        return self.clustering.get_strategy_name()

    def get_clustering_plot(
        self,
        figsize: tuple[int, int] = (12, 8),
        title: str | None = None,
    ) -> str:
        """
        Generate clustering visualization plot.

        Returns:
            Base64 encoded PNG image string.
        """
        return self.clustering.generate_plot(figsize=figsize, title=title)

    def optimize_deliveries(
        self,
        orders: list[Order] | list[list[Order]],
        algorithm: str = "genetic",
        **kwargs,
    ) -> dict[int | str, RouteOptimizationResult | list[Order] | None]:
        """
        Executes the full optimization pipeline with console logging.
        """
        if not orders:
            logger.warning("⚠️ No hay pedidos para optimizar")
            return {}

        # 1. Pre-process: Consolidate
        if orders and isinstance(orders[0], list):
            logger.info(
                "🔄 Detected grouped orders. Consolidating lines by order_id..."
            )
            total_lines = len(sum(orders, []))
            orders = consolidate_orders(orders)
            logger.info(
                f"   ✅ {total_lines} lines → {len(orders)} consolidated orders\n"
            )

        # 2. Filter: Impossible Destinations
        logger.debug(f"Starting filtering of {len(orders)} orders")
        valid_orders = []
        impossible_orders = []

        for p in orders:
            dest_norm = p.destino.lower()
            if any(i in dest_norm for i in self.IMPOSSIBLE_DESTS):
                impossible_orders.append(p)
            else:
                valid_orders.append(p)

        logger.debug(
            f"Filtered result: {len(valid_orders)} deliverable, "
            f"{len(impossible_orders)} impossible destinations\n"
        )

        if impossible_orders:
            logger.warning(
                f"⚠️: {len(impossible_orders)} orders to impossible destinations "
                "INACCESIBLE by road."
            )

        if not valid_orders:
            logger.error("❌ There are no deliverable orders by road")
            return {"pedidos_no_entregables": impossible_orders}

        # 3. Fleet Calculation
        total_weight = sum(
            o.cantidad_producto * self.config.peso_unitario_default
            for o in valid_orders
        )
        capacidad_camion = self.config.capacidad_carga
        n_trucks = max(1, math.ceil(total_weight / capacidad_camion))

        logger.info("📦 LOAD ANALYSIS:")
        logger.info(f"   Total orders: {len(valid_orders)}")
        logger.info(f"   Total weight: {total_weight:.2f} kg")
        logger.info(f"   Capacity per truck: {capacidad_camion:.2f} kg")
        logger.info(f"   Minimum trucks needed: {n_trucks}")
        logger.info(f"   ✅ Using {n_trucks} truck(s)\n")

        # 4. Clustering (using selected strategy)
        logger.info(
            f"🧠 Grouping {len(valid_orders)} orders in {n_trucks} truck(s) "
            f"using [{self.clustering.get_strategy_name()}]..."
        )
        clusters = self.clustering.cluster_orders(
            valid_orders, n_trucks, self.config.peso_unitario_default, capacidad_camion
        )

        if not clusters:
            logger.error("❌ The orders could not be grouped into clusters")
            return {}

        logger.info(f"   ✅ Clustering completed: {len(clusters)} groups created\n")

        # 5. Distance Matrix
        logger.info("📊 Generating distance matrix...\n")
        dist_matrix = self.graph.generate_distance_matrix()

        # 6. Select Routing Strategy
        if algorithm == "ortools":
            strategy = ORToolsStrategy(
                dist_matrix, self.config, self.origin, self.graph
            )
        else:
            strategy = GeneticStrategy(
                dist_matrix, self.config, self.origin, self.graph
            )

        # 7. Execute Optimization
        results = {}
        for cid, group in clusters.items():
            if not group:
                results[cid] = None
                logger.warning(f"⚠️ Truck {cid + 1}: No orders assigned")
                continue

            peso_cluster = sum(
                o.cantidad_producto * self.config.peso_unitario_default for o in group
            )
            ocupacion = (peso_cluster / capacidad_camion) * 100

            logger.info(f"🚚 TRUCK {cid + 1}:")
            logger.info(
                f"   Orders: {len(group)} | Weight: {peso_cluster:.2f} kg | "
                f"Occupancy: {ocupacion:.1f}%"
            )

            # Run Algorithm
            result = strategy.optimize(group, **kwargs)

            if result:
                result.camion_id = cid + 1
                results[cid] = result

                # Print resume data
                ciudades_counts = Counter(result.ciudades_ordenadas)
                ruta_resumida = " → ".join(
                    [
                        f"{c} ({cnt})" if cnt > 1 else c
                        for c, cnt in ciudades_counts.items()
                    ]
                )
                logger.info(f"   ✅ Route: {ruta_resumida}")
                logger.info(
                    f"   📏 Distance: {result.distancia_total_km} km | "
                    f"⏱️ Time: {result.tiempo_total_viaje_horas} h"
                )
                logger.info(
                    f"   ⛽ Consum: {result.consumo_litros} L | "
                    f"💰 Cost: {result.coste_total_ruta} €\n"
                )
            else:
                logger.error(f"   ❌ Failed to optimize route Truck {cid + 1}")
        # 8. Show final resume
        logger.info("=" * 70)
        logger.info("📊 FINAL RESUME OF FLEET UTILIZATION")
        logger.info("=" * 70)

        peso_total_transportado = 0
        capacidad_total_disp = 0

        for cid, res in results.items():
            if res:
                peso_camion = sum(
                    p.cantidad_producto * self.config.peso_unitario_default
                    for p in res.lista_pedidos_ordenada
                )
                peso_total_transportado += peso_camion
                capacidad_total_disp += capacidad_camion
                pct = (peso_camion / capacidad_camion) * 100
                logger.info(
                    f"🚛 Truck {cid + 1}: {peso_camion:.1f}/{capacidad_camion:.1f} kg "
                    f"({pct:.1f}% occupancy)"
                )

        aprovechamiento_global = (
            (peso_total_transportado / capacidad_total_disp * 100)
            if capacidad_total_disp > 0
            else 0
        )
        logger.info(f"\n✅ Global fleet utilization: {aprovechamiento_global:.1f}%")
        logger.info(f"📦 Total transport carried: {peso_total_transportado:.1f} kg")
        logger.info(f"🚛 Total available capacity: {capacidad_total_disp:.1f} kg")
        logger.info("=" * 70 + "\n")

        # 9. Add rejected orders
        if impossible_orders:
            results["pedidos_no_entregables"] = impossible_orders

        return results

    def get_global_stats(self, results: dict) -> dict:
        """Calculates aggregated stats from results."""
        total_cost = 0.0
        total_km = 0.0
        total_orders = 0

        for res in results.values():
            if isinstance(res, RouteOptimizationResult):
                total_cost += res.coste_total_ruta
                total_km += res.distancia_total_km
                total_orders += len(res.lista_pedidos_ordenada)

        return {
            "coste_total": round(total_cost, 2),
            "km_totales": round(total_km, 2),
            "pedidos_entregados": total_orders,
        }

    def generate_routes_plot(
        self,
        results: dict,
        figsize: tuple[int, int] = (12, 8),
    ) -> str:
        """
        Generates a clean route map (Tactical Style).
        - No large numbers.
        - Directional arrows.
        - Smart city labels (anti-overlap).
        """
        if not results:
            return ""

        # Dark Style Config
        plt.style.use("dark_background")
        fig, ax = plt.subplots(figsize=figsize)
        fig.patch.set_facecolor("#0e1117")
        ax.set_facecolor("#0e1117")

        # Colors
        cmap = plt.colormaps.get_cmap("tab10")
        valid_results = [
            r
            for k, r in results.items()
            if k != "pedidos_no_entregables" and r is not None
        ]
        colors = cmap(np.linspace(0, 1, max(len(valid_results), 1)))

        label_positions = []
        min_label_dist = 0.04

        # 1. Deposit Draw (Star Central)
        if valid_results:
            origin_coords = valid_results[0].ruta_coordenadas[0]
            ax.scatter(
                origin_coords[1],
                origin_coords[0],
                c="white",
                s=400,
                marker="*",
                edgecolors="#FFD700",
                linewidth=2,
                zorder=10,
                label="Distribution Center",
            )

        # 2. DRAW ROUTES
        for idx, result in enumerate(valid_results):
            if not result or not result.ruta_coordenadas:
                continue

            color = colors[idx]
            coords = result.ruta_coordenadas

            # Extract lat/lon
            lats = np.array([c[0] for c in coords])
            lons = np.array([c[1] for c in coords])

            # Extract city names (excluding origin/destination for labels)
            route_cities = result.ciudades_ordenadas

            # --- A. TRAYECTORY LINES ---
            ax.plot(
                lons,
                lats,
                color=color,
                alpha=0.7,
                linewidth=1.8,
                linestyle="-",
                zorder=2,
            )

            # --- B. DIRECTION ARROWS  ---
            for i in range(len(lons) - 1):
                dx = lons[i + 1] - lons[i]
                dy = lats[i + 1] - lats[i]

                if abs(dx) > 0.02 or abs(dy) > 0.02:
                    ax.arrow(
                        lons[i],
                        lats[i],
                        dx * 0.55,
                        dy * 0.55,
                        color=color,
                        head_width=0.04,
                        head_length=0.04,
                        shape="full",
                        length_includes_head=True,
                        alpha=0.8,
                        zorder=3,
                    )

            # --- C. NODES (STOPS) ---
            # Draw small points on stops (excluding the origin/destination final which is the depot)
            stop_lons = lons[1:-1]
            stop_lats = lats[1:-1]
            stop_cities = route_cities[1:-1]

            ax.scatter(
                stop_lons,
                stop_lats,
                c=[color],
                s=60,
                alpha=1.0,
                edgecolors="white",
                linewidth=1.0,
                zorder=4,
            )

            # --- D. SMART LABELS (CITIES) ---
            for slon, slat, scity in zip(
                stop_lons, stop_lats, stop_cities, strict=False
            ):
                # Check for collision
                collision = False
                for existing_lon, existing_lat in label_positions:
                    dist = np.sqrt(
                        (slon - existing_lon) ** 2 + (slat - existing_lat) ** 2
                    )
                    if dist < min_label_dist:
                        collision = True
                        break

                if not collision:
                    display_name = scity[:10] + "." if len(scity) > 10 else scity

                    text = ax.text(
                        slon,
                        slat + 0.015,
                        display_name,
                        color="white",
                        fontsize=7,
                        fontweight="bold",
                        ha="center",
                        va="bottom",
                        zorder=5,
                    )
                    text.set_path_effects(
                        [pe.withStroke(linewidth=2, foreground="black")]
                    )

                    label_positions.append((slon, slat))

        # Final Touches
        ax.set_title(
            "DISTRIBUTED AND FLOWS NETWORKS - ROUTE MAP",
            fontsize=14,
            fontweight="bold",
            color="white",
            pad=20,
        )
        ax.set_aspect("equal")
        ax.axis("off")

        # Legend
        import matplotlib.lines as mlines

        legend_handles = [
            mlines.Line2D(
                [],
                [],
                color=colors[i],
                marker="o",
                markersize=6,
                label=f"Truck {res.camion_id}",
                linestyle="-",
            )
            for i, res in enumerate(valid_results)
        ]

        ax.legend(
            handles=legend_handles,
            loc="lower left",
            fontsize=7,
            frameon=True,
            facecolor="#1c1f26",
            edgecolor="#444",
            labelcolor="white",
            ncol=2,
        )

        plt.tight_layout()

        buffer = io.BytesIO()
        fig.savefig(
            buffer, format="png", dpi=150, bbox_inches="tight", facecolor="#0e1117"
        )
        buffer.seek(0)
        img = base64.b64encode(buffer.read()).decode("utf-8")
        plt.close(fig)

        return img
