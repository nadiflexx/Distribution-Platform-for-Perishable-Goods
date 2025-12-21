"""
Optimization Orchestrator.
Main entry point for the Routing System. Integrates:
- Clustering (K-Means)
- Graph (Distances)
- Routing Strategies (Genetic / ILS)
"""

from collections import Counter
import logging
import math

# Logic Modules
from distribution_platform.core.logic.clustering import ClusteringManager
from distribution_platform.core.logic.graph import GraphManager
from distribution_platform.core.logic.order_processing import consolidate_orders

# Strategies
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

logger = logging.getLogger(__name__)


class OptimizationOrchestrator:
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
    ):
        self.config = config if config else SimulationConfig()
        self.origin = origin_base
        self.coord_cache = coord_cache if coord_cache else CoordinateCache()

        # Initialize Managers
        self.clustering = ClusteringManager(self.coord_cache)
        self.graph = GraphManager(self.coord_cache)

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
            print("⚠️ No hay pedidos para optimizar")
            return {}

        # 1. Pre-process: Consolidate
        if orders and isinstance(orders[0], list):
            print(
                "🔄 Detectados pedidos agrupados. Consolidando líneas por pedido_id..."
            )
            total_lines = len(sum(orders, []))
            orders = consolidate_orders(orders)  # type: ignore
            print(f"   ✅ {total_lines} líneas → {len(orders)} pedidos consolidados\n")

        # 2. Filter: Impossible Destinations
        print(f"DEBUG: Iniciando filtrado de {len(orders)} pedidos")
        valid_orders = []
        impossible_orders = []

        for p in orders:  # type: ignore
            # Normalización simple para búsqueda
            dest_norm = p.destino.lower()
            if any(i in dest_norm for i in self.IMPOSSIBLE_DESTS):
                impossible_orders.append(p)
                # print(f"DEBUG: Pedido {p.pedido_id} → {p.destino} ES IMPOSIBLE")
            else:
                valid_orders.append(p)

        print(
            f"DEBUG: Resultado filtrado: {len(valid_orders)} entregables, {len(impossible_orders)} imposibles\n"
        )

        if impossible_orders:
            print(
                f"⚠️ ADVERTENCIA: {len(impossible_orders)} pedidos a destinos INACCESIBLES por carretera."
            )

        if not valid_orders:
            print("❌ No hay pedidos entregables por carretera")
            return {"pedidos_no_entregables": impossible_orders}

        # 3. Fleet Calculation
        total_weight = sum(
            o.cantidad_producto * self.config.peso_unitario_default
            for o in valid_orders
        )
        capacidad_camion = self.config.capacidad_carga
        n_trucks = max(1, math.ceil(total_weight / capacidad_camion))

        print("📦 ANÁLISIS DE CARGA:")
        print(f"   Total pedidos: {len(valid_orders)}")
        print(f"   Peso total: {total_weight:.2f} kg")
        print(f"   Capacidad por camión: {capacidad_camion:.2f} kg")
        print(f"   Camiones mínimos necesarios: {n_trucks}")
        print(f"   ✅ Usando {n_trucks} camion(es)\n")

        # 4. Clustering
        print(f"🧠 Agrupando {len(valid_orders)} pedidos en {n_trucks} camion(es)...")
        clusters = self.clustering.cluster_orders(
            valid_orders, n_trucks, self.config.peso_unitario_default, capacidad_camion
        )

        if not clusters:
            print("❌ No se pudieron agrupar los pedidos")
            return {}

        # 5. Distance Matrix
        print("📊 Generando matriz de distancias...\n")
        dist_matrix = self.graph.generate_distance_matrix()

        # 6. Select Strategy
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
                print(f"⚠️ Camión {cid + 1}: Sin pedidos asignados")
                continue

            # Calcular peso del cluster para print
            peso_cluster = sum(
                o.cantidad_producto * self.config.peso_unitario_default for o in group
            )
            ocupacion = (peso_cluster / capacidad_camion) * 100

            print(f"🚚 CAMIÓN {cid + 1}:")
            print(
                f"   Pedidos: {len(group)} | Peso: {peso_cluster:.2f} kg | Ocupación: {ocupacion:.1f}%"
            )

            # Run Algorithm
            result = strategy.optimize(group, **kwargs)

            if result:
                result.camion_id = cid + 1
                results[cid] = result

                # Print resumen ruta
                ciudades_counts = Counter(result.ciudades_ordenadas)
                ruta_resumida = " → ".join(
                    [
                        f"{c} ({cnt})" if cnt > 1 else c
                        for c, cnt in ciudades_counts.items()
                    ]
                )
                print(f"   ✅ Ruta: {ruta_resumida}")
                print(
                    f"   📏 Distancia: {result.distancia_total_km} km | ⏱️ Tiempo: {result.tiempo_total_viaje_horas} h"
                )
                print(
                    f"   ⛽ Consumo: {result.consumo_litros} L | 💰 Coste: {result.coste_total_ruta} €\n"
                )
            else:
                print(f"   ❌ Fallo al optimizar ruta Camión {cid + 1}")

        # 8. Mostrar Resumen Final
        print("=" * 70)
        print("📊 RESUMEN DE APROVECHAMIENTO DE FLOTA")
        print("=" * 70)

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
                print(
                    f"🚛 Camión {cid + 1}: {peso_camion:.1f}/{capacidad_camion:.1f} kg ({pct:.1f}% ocupación)"
                )

        aprovechamiento_global = (
            (peso_total_transportado / capacidad_total_disp * 100)
            if capacidad_total_disp > 0
            else 0
        )
        print(f"\n✅ Aprovechamiento global de la flota: {aprovechamiento_global:.1f}%")
        print(f"📦 Total peso transportado: {peso_total_transportado:.1f} kg")
        print(f"🚛 Capacidad total disponible: {capacidad_total_disp:.1f} kg")
        print("=" * 70 + "\n")

        # 9. Add rejected orders
        if impossible_orders:
            results["pedidos_no_entregables"] = impossible_orders  # type: ignore

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
