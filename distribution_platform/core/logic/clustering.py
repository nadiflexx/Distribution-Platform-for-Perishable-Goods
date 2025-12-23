"""
Clustering Logic.

Uses K-Means to group orders based on geographical proximity and urgency.
"""

import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

from distribution_platform.config.logging_config import log as logger
from distribution_platform.core.models.order import Order
from distribution_platform.infrastructure.persistence.coordinates import (
    CoordinateCache,
)


class ClusteringManager:
    """
    Manager for K-Means Clustering of Orders.
    """

    def __init__(self, coord_cache: CoordinateCache):
        self.scaler = StandardScaler()
        self.coord_cache = coord_cache

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

        # 4. K-Means
        kmeans = KMeans(n_clusters=n_trucks, random_state=42, n_init=10)
        clusters_indices = kmeans.fit_predict(scaled_data)

        # 5. Reconstruct
        result: dict[int, list[Order]] = {i: [] for i in range(n_trucks)}
        for idx, cluster_id in enumerate(clusters_indices):
            result[cluster_id].append(data_enriched[idx]["pedido"])

        # 6. Balance by Weight
        return self._balance_clusters_by_weight(
            result, unit_weight, max_capacity, n_trucks
        )

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

        # Helper for weight calc
        # Pre-cache weights to avoid re-calculation loop
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
