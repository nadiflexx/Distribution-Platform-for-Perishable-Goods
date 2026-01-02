"""
Base Clustering Strategy.

Defines the interface for clustering algorithms and shares common
logic like coordinate enrichment, weight balancing, and visualization.
"""

from abc import ABC, abstractmethod
import base64
import io

import matplotlib
import matplotlib.patheffects as pe  # <--- IMPORTANTE PARA EL BORDE DEL TEXTO

# Backend sin GUI para servidores
matplotlib.use("Agg")
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.spatial import ConvexHull
from sklearn.preprocessing import StandardScaler

from distribution_platform.config.logging_config import log as logger
from distribution_platform.core.models.order import Order
from distribution_platform.infrastructure.persistence.coordinates import (
    CoordinateCache,
)


class ClusteringStrategy(ABC):
    """Abstract Base Class for Order Clustering Algorithms."""

    def __init__(self, coord_cache: CoordinateCache):
        self.scaler = StandardScaler()
        self.coord_cache = coord_cache

        # Cache del último clustering para plotting
        self._last_data: list[dict] | None = None
        self._last_labels: list[int] | None = None
        self._last_n_clusters: int = 0

    @abstractmethod
    def _perform_clustering(
        self, scaled_data: np.ndarray, n_clusters: int
    ) -> list[int]:
        """Execute the specific clustering algorithm. Returns cluster indices."""
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Strategy name for logging and display."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Human-readable description of the algorithm."""
        pass

    def cluster_orders(
        self,
        orders: list[Order],
        n_trucks: int,
        unit_weight: float = 1.0,
        max_capacity: float = 1000.0,
    ) -> dict[int, list[Order]]:
        """
        Groups orders into clusters and balances them by weight constraint.
        """
        if not orders:
            return {}

        # 1. Enrich with Coordinates
        data_enriched = self._enrich_coordinates(orders)
        if not data_enriched:
            logger.error("❌ No se pudieron obtener coordenadas para ningún pedido")
            return {}

        # 2. Prepare Data for ML (Lat, Lon, Urgency)
        df = pd.DataFrame(
            [
                {"lat": item["lat"], "lon": item["lon"], "urgencia": item["urgencia"]}
                for item in data_enriched
            ]
        )

        # 3. Normalize
        scaled_data = self.scaler.fit_transform(df)

        # 4. Execute specific clustering algorithm
        clusters_indices = self._perform_clustering(scaled_data, n_trucks)

        # 5. Cache for plotting
        self._last_data = data_enriched
        self._last_labels = clusters_indices
        self._last_n_clusters = n_trucks

        # 6. Reconstruct
        result: dict[int, list[Order]] = {i: [] for i in range(n_trucks)}
        for idx, cluster_id in enumerate(clusters_indices):
            result[cluster_id].append(data_enriched[idx]["pedido"])

        # 7. Balance by Weight
        return self._balance_clusters_by_weight(
            result, unit_weight, max_capacity, n_trucks
        )

    def generate_plot(
        self,
        figsize: tuple[int, int] = (12, 8),
        show_legend: bool = True,
        title: str | None = None,
    ) -> str:
        """
        Generates a professional scatter plot with Convex Hulls and Smart Labeling.
        """
        if self._last_data is None or self._last_labels is None:
            logger.warning(
                "⚠️ No hay datos de clustering. Ejecuta cluster_orders primero."
            )
            return self._generate_empty_plot()

        # --- 1. AESTHETIC CONFIGURATION  ---
        plt.style.use("dark_background")
        fig, ax = plt.subplots(figsize=figsize)
        fig.patch.set_facecolor("#0e1117")
        ax.set_facecolor("#0e1117")

        # Data
        lats = np.array([item["lat"] for item in self._last_data])
        lons = np.array([item["lon"] for item in self._last_data])
        labels = np.array(self._last_labels)
        cities = np.array([item["pedido"].destino for item in self._last_data])

        # Colors
        cmap = plt.colormaps.get_cmap("tab10")
        colors = cmap(np.linspace(0, 1, max(self._last_n_clusters, 1)))

        legend_patches = []

        # Cache for avoiding label overlaps
        # Saving tuples (x, y)
        label_positions: list[tuple[float, float]] = []

        min_label_dist = 0.04

        # --- 2. DRAW CLUSTERS ---
        for cluster_id in range(self._last_n_clusters):
            mask = labels == cluster_id
            if not np.any(mask):
                continue

            c_lons = lons[mask]
            c_lats = lats[mask]
            c_cities = cities[mask]
            color = colors[cluster_id]

            # A. Puntos (Orders)
            ax.scatter(
                c_lons,
                c_lats,
                c=[color],
                s=40,
                alpha=0.9,
                edgecolors="white",
                linewidth=0.3,
                zorder=3,
            )

            # B. Envolvente Convexa (Polygon)
            if len(c_lons) >= 3:
                points = np.column_stack((c_lons, c_lats))
                try:
                    hull = ConvexHull(points)
                    hull_points = points[hull.vertices]
                    hull_points = np.vstack((hull_points, hull_points[0]))

                    poly = mpatches.Polygon(
                        hull_points,
                        closed=True,
                        facecolor=color,
                        alpha=0.1,
                        edgecolor=color,
                        linewidth=1.5,
                        linestyle="--",
                        zorder=2,
                    )
                    ax.add_patch(poly)
                except Exception:
                    pass

            # C. Centroid
            cent_lon, cent_lat = np.mean(c_lons), np.mean(c_lats)
            ax.scatter(
                cent_lon,
                cent_lat,
                c=[color],
                s=150,
                marker="P",
                edgecolors="white",
                linewidth=1.5,
                zorder=4,
            )

            dists_to_center = np.sqrt(
                (c_lons - cent_lon) ** 2 + (c_lats - cent_lat) ** 2
            )
            sorted_indices = np.argsort(-dists_to_center)

            for idx in sorted_indices:
                lon, lat, city = c_lons[idx], c_lats[idx], c_cities[idx]

                collision = False
                for existing_lon, existing_lat in label_positions:
                    dist = np.sqrt(
                        (lon - existing_lon) ** 2 + (lat - existing_lat) ** 2
                    )
                    if dist < min_label_dist:
                        collision = True
                        break

                if not collision:
                    short_city = city[:12] + ".." if len(city) > 12 else city

                    text = ax.text(
                        lon,
                        lat + 0.01,
                        short_city,
                        fontsize=7,
                        color="white",
                        ha="center",
                        va="bottom",
                        zorder=5,
                        fontweight="bold",
                    )

                    text.set_path_effects(
                        [pe.withStroke(linewidth=2, foreground="black"), pe.Normal()]
                    )

                    label_positions.append((lon, lat))

            # Legend
            legend_patches.append(
                mpatches.Patch(
                    color=color, label=f"C-{cluster_id + 1} ({len(c_lons)})", alpha=0.7
                )
            )

        # --- 3. FINAL ADJUSTMENTS ---
        plot_title = title or f"ASIGNACIÓN DE ZONAS ({self.name})"
        ax.set_title(plot_title, fontsize=14, fontweight="bold", color="white", pad=15)

        ax.set_aspect("equal")
        ax.axis("off")

        if show_legend:
            legend = ax.legend(
                handles=legend_patches,
                loc="lower left",
                fontsize=8,
                frameon=True,
                facecolor="#1c1f26",
                edgecolor="#444",
                ncol=2,
            )
            for t in legend.get_texts():
                t.set_color("white")

        plt.tight_layout()

        # Render
        buffer = io.BytesIO()
        fig.savefig(
            buffer, format="png", dpi=150, bbox_inches="tight", facecolor="#0e1117"
        )
        buffer.seek(0)
        img = base64.b64encode(buffer.read()).decode("utf-8")
        plt.close(fig)

        return img

    def _generate_empty_plot(self) -> str:
        """Generates an empty plot with error message."""
        fig, ax = plt.subplots(figsize=(10, 6))
        fig.patch.set_facecolor("#0e1117")
        ax.set_facecolor("#0e1117")

        ax.text(
            0.5,
            0.5,
            "No hay datos de clustering disponibles.\nEjecuta cluster_orders() primero.",
            ha="center",
            va="center",
            fontsize=14,
            color="white",
            transform=ax.transAxes,
        )
        ax.set_axis_off()

        buffer = io.BytesIO()
        fig.savefig(buffer, format="png", dpi=100, facecolor="#0e1117")
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.read()).decode("utf-8")
        plt.close(fig)

        return image_base64

    def _enrich_coordinates(self, orders: list[Order]) -> list[dict]:
        """
        Enriches orders with coordinates from the cache.
        """
        data_matrix = []
        for p in orders:
            coord_str = self.coord_cache.get(p.destino)
            if coord_str is None:
                continue

            try:
                lat, lon = map(float, coord_str.split(","))
            except (ValueError, AttributeError):
                continue

            # Urgency factor (lower days = higher urgency)
            factor_urgencia = (1.0 / (p.caducidad + 1)) * 50

            data_matrix.append(
                {"pedido": p, "lat": lat, "lon": lon, "urgencia": factor_urgencia}
            )

        return data_matrix

    def _balance_clusters_by_weight(
        self,
        clusters: dict[int, list[Order]],
        unit_weight: float,
        max_capacity: float,
        n_trucks: int,
    ) -> dict[int, list[Order]]:
        """
        Re-balances clusters that exceed max weight capacity.
        """
        weight_cache = {}
        for _, ords in clusters.items():
            for o in ords:
                if id(o) not in weight_cache:
                    weight_cache[id(o)] = o.cantidad_producto * unit_weight

        def get_cluster_weight(order_list):
            return sum(weight_cache[id(o)] for o in order_list)

        max_iters = 5
        iter_count = 0
        redistributions = 0

        while iter_count < max_iters:
            overloaded = [
                (k, v)
                for k, v in clusters.items()
                if get_cluster_weight(v) > max_capacity
            ]

            if not overloaded:
                break

            max_moves = 10
            moves = 0

            for cid, _ in overloaded:
                if moves >= max_moves:
                    break
                if not clusters[cid]:
                    continue

                current_w = get_cluster_weight(clusters[cid])
                if current_w <= max_capacity:
                    continue

                # Remove heaviest
                heaviest = max(clusters[cid], key=lambda p: weight_cache[id(p)])
                clusters[cid].remove(heaviest)

                redistributions += 1
                moves += 1

                w_order = weight_cache[id(heaviest)]

                # Find space
                candidates = [
                    k
                    for k in clusters
                    if get_cluster_weight(clusters[k]) + w_order <= max_capacity
                ]

                if candidates:
                    # Strategy: Fill emptiest valid cluster
                    dest = min(
                        candidates, key=lambda k: get_cluster_weight(clusters[k])
                    )
                    clusters[dest].append(heaviest)
                else:
                    # No space, dump to emptiest (will handle overflow in final step)
                    dest = min(
                        clusters.keys(), key=lambda k: get_cluster_weight(clusters[k])
                    )
                    clusters[dest].append(heaviest)

            iter_count += 1

        # FINAL STEP: Add extra trucks if still overloaded
        overloaded_ids = [
            k for k, v in clusters.items() if get_cluster_weight(v) > max_capacity
        ]

        if overloaded_ids:
            next_id = max(clusters.keys()) + 1
            for cid in overloaded_ids:
                while get_cluster_weight(clusters[cid]) > max_capacity:
                    if not clusters[cid]:
                        break

                    # Move heaviest out
                    p = max(clusters[cid], key=lambda x: weight_cache[id(x)])

                    # Edge case: Single order > capacity
                    if weight_cache[id(p)] > max_capacity and len(clusters[cid]) == 1:
                        break  # Cannot fix

                    clusters[cid].remove(p)

                    # Try find space again
                    found = False
                    for k in clusters:
                        if (
                            get_cluster_weight(clusters[k]) + weight_cache[id(p)]
                            <= max_capacity
                        ):
                            clusters[k].append(p)
                            found = True
                            break

                    if not found:
                        clusters[next_id] = [p]
                        next_id += 1

        return clusters
