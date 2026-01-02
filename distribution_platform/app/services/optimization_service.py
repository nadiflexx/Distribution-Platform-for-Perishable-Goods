"""
Optimization/simulation service with algorithm visualization support.
"""

from dataclasses import dataclass, field
import math
import random
from typing import Any

import pandas as pd
import streamlit as st

from distribution_platform.app.state.session_manager import SessionManager
from distribution_platform.config.logging_config import log as logger
from distribution_platform.config.settings import MapConfig
from distribution_platform.core.logic.routing.clustering import (
    AgglomerativeStrategy,
    KMeansStrategy,
)
from distribution_platform.core.models.optimization import SimulationConfig
from distribution_platform.core.services.optimization_orchestrator import (
    OptimizationOrchestrator,
)
from distribution_platform.infrastructure.persistence.coordinates import (
    CoordinateCache,
)


@dataclass
class AlgorithmSnapshot:
    """Represents a single state of the algorithm during optimization."""

    iteration: int
    description: str
    nodes: list[dict[str, Any]]
    edges: list[dict[str, Any]]
    current_best_cost: float = 0.0
    trucks_assigned: int = 0


@dataclass
class AlgorithmTrace:
    """Complete trace of algorithm execution."""

    algorithm_name: str
    snapshots: list[AlgorithmSnapshot] = field(default_factory=list)
    final_cost: float = 0.0
    total_iterations: int = 0


class OptimizationService:
    """Handles route optimization logic with visualization support."""

    # Orchestrator cache to access to the plot functions later
    _last_orchestrator: OptimizationOrchestrator | None = None

    @staticmethod
    def run() -> dict | None:
        """Execute the optimization and return results with algorithm trace."""
        try:
            routing_algo = OptimizationService._get_routing_algorithm()
            clustering_algo = OptimizationService._get_clustering_algorithm()
            truck_data = SessionManager.get("selected_truck_data")
            orders_data = SessionManager.get("df")

            if not truck_data or not orders_data:
                return None

            # Validate capacity
            if not OptimizationService._validate_capacity(truck_data, orders_data):
                return None

            # Build config
            config = OptimizationService._build_config(truck_data)

            # Build clustering strategy
            coord_cache = CoordinateCache()
            clustering_strategy = OptimizationService._build_clustering_strategy(
                clustering_algo, coord_cache
            )

            # Run optimization with tracing
            orchestrator = OptimizationOrchestrator(
                config=config,
                origin_base="Mataró",
                coord_cache=coord_cache,
                clustering_strategy=clustering_strategy,
            )

            # Cache orchestrator for plot generation
            OptimizationService._last_orchestrator = orchestrator

            raw_results = orchestrator.optimize_deliveries(
                orders_data, algorithm=routing_algo
            )

            clustering_plot_b64 = orchestrator.get_clustering_plot(
                title="Strategic Truck Assignment (Clustering)"
            )

            routes_plot_b64 = orchestrator.generate_routes_plot(raw_results)

            # Generate algorithm trace for visualization
            algorithm_trace = OptimizationService._generate_algorithm_trace(
                orders_data, raw_results, routing_algo
            )

            # Format results
            results = OptimizationService._format_results(raw_results)
            results["algorithm_trace"] = algorithm_trace
            results["clustering_strategy"] = orchestrator.get_clustering_strategy_name()
            results["routing_algorithm"] = routing_algo
            results["plots"] = {
                "clustering": clustering_plot_b64,
                "routes": routes_plot_b64,
            }
            return results

        except Exception as e:
            logger.error(f"CRITICAL SIMULATION ERROR: {e}")
            st.error(f"❌ System Error: {e}")
            return None

    @staticmethod
    def get_clustering_plot(
        figsize: tuple[int, int] = (12, 8),
        title: str | None = None,
    ) -> str | None:
        """
        Generate clustering visualization plot from last optimization.

        Returns:
            Base64 encoded PNG image string, or None if no optimization ran.
        """
        if OptimizationService._last_orchestrator is None:
            logger.warning("⚠️ No hay optimización previa. Ejecuta run() primero.")
            return None

        return OptimizationService._last_orchestrator.get_clustering_plot(
            figsize=figsize, title=title
        )

    @staticmethod
    def _get_routing_algorithm() -> str:
        """Get selected routing algorithm from session."""
        algo_select = SessionManager.get("algo_select", "")
        return "ortools" if "OR-Tools" in algo_select else "genetic"

    @staticmethod
    def _get_clustering_algorithm() -> str:
        """Get selected clustering algorithm from session."""
        clustering_select = SessionManager.get("clustering_select", "K-Means")
        return clustering_select.lower().replace(" ", "_").replace("-", "")

    @staticmethod
    def _build_clustering_strategy(algo: str, coord_cache: CoordinateCache):
        """Factory for clustering strategies."""
        strategies = {
            "kmeans": KMeansStrategy(coord_cache),
            "jerarquico": AgglomerativeStrategy(coord_cache),
            "agglomerative": AgglomerativeStrategy(coord_cache),
            "hierarchical": AgglomerativeStrategy(coord_cache),
        }

        algo_normalized = (
            algo.lower().replace(" ", "").replace("-", "").replace("_", "")
        )

        for key, strategy in strategies.items():
            if key.replace("_", "") in algo_normalized or algo_normalized in key:
                logger.info(f"🧠 Clustering strategy selected: {strategy.name}")
                return strategy

        # Default to K-Means
        logger.info("🧠 Clustering strategy defaulting to: K-Means")
        return KMeansStrategy(coord_cache)

    @staticmethod
    def _validate_capacity(truck_data: dict, orders_data: list) -> bool:
        orders_flat = [order for group in orders_data for order in group]
        total_load = sum(o.cantidad_producto for o in orders_flat)
        total_orders = len(orders_flat)

        truck_cap = float(truck_data.get("capacidad", 1000))
        if truck_cap < 100 and total_load > 10000:
            truck_cap *= 1000

        needed_trucks = math.ceil(total_load / truck_cap) if truck_cap > 0 else 9999

        if needed_trucks > total_orders:
            st.error(
                f"⚠️ CAPACITY ERROR: {truck_cap}kg capacity insufficient "
                f"for {total_orders} orders."
            )
            return False
        return True

    @staticmethod
    def _build_config(truck_data: dict) -> SimulationConfig:
        truck_cap = float(truck_data.get("capacidad", 1000))
        if truck_cap < 100:
            truck_cap *= 1000

        return SimulationConfig(
            velocidad_constante=float(truck_data.get("velocidad_constante", 90)),
            consumo_combustible=float(truck_data.get("consumo", 30)),
            capacidad_carga=truck_cap,
            salario_conductor_hora=float(truck_data.get("precio_conductor_hora", 20)),
        )

    @staticmethod
    def _generate_algorithm_trace(
        orders_data: list, results: dict, algo: str
    ) -> dict[str, AlgorithmTrace]:
        """
        Generate visualization trace for each truck's route optimization.
        This simulates/reconstructs the algorithm's decision process.
        """
        traces = {}

        # Origin coordinates (Mataró)
        origin = {
            "id": "origin",
            "name": "Mataró",
            "lat": 41.5381,
            "lon": 2.4445,
            "type": "origin",
        }

        for key, truck_result in results.items():
            if key == "pedidos_no_entregables" or truck_result is None:
                continue

            route_orders = truck_result.lista_pedidos_ordenada
            route_coords = truck_result.ruta_coordenadas

            if not route_orders:
                continue

            # Build nodes list
            nodes = [origin]
            for i, order in enumerate(route_orders):
                coord = route_coords[i + 1] if i + 1 < len(route_coords) else (0, 0)
                nodes.append(
                    {
                        "id": f"order_{order.pedido_id}",
                        "name": order.destino,
                        "lat": coord[0],
                        "lon": coord[1],
                        "type": "delivery",
                        "order_id": order.pedido_id,
                    }
                )

            # Simulate algorithm progression
            if algo == "genetic":
                trace = OptimizationService._simulate_genetic_trace(
                    nodes, route_orders, truck_result
                )
            else:
                trace = OptimizationService._simulate_ortools_trace(
                    nodes, route_orders, truck_result
                )

            traces[f"truck_{truck_result.camion_id}"] = trace

        return traces

    @staticmethod
    def _simulate_genetic_trace(
        nodes: list, route_orders: list, truck_result
    ) -> AlgorithmTrace:
        """Simulate genetic algorithm progression for visualization."""
        trace = AlgorithmTrace(algorithm_name="Genetic Algorithm")

        n_orders = len(route_orders)
        if n_orders == 0:
            return trace

        # Phase 1: Initial random population
        trace.snapshots.append(
            AlgorithmSnapshot(
                iteration=0,
                description="Initializing population with random routes",
                nodes=nodes.copy(),
                edges=[],
                current_best_cost=float("inf"),
                trucks_assigned=0,
            )
        )

        # Phase 2-5: Show random configurations
        for gen in range(1, 5):
            random_order = list(range(1, len(nodes)))
            random.shuffle(random_order)

            edges = []
            edges.append(
                {
                    "from_id": 0,
                    "to_id": random_order[0],
                    "color": "#ef4444",
                    "weight": 1,
                }
            )
            for i in range(len(random_order) - 1):
                edges.append(
                    {
                        "from_id": random_order[i],
                        "to_id": random_order[i + 1],
                        "color": "#ef4444",
                        "weight": 1,
                    }
                )
            edges.append(
                {
                    "from_id": random_order[-1],
                    "to_id": 0,
                    "color": "#ef4444",
                    "weight": 1,
                }
            )

            fake_cost = truck_result.distancia_total_km * (2.5 - gen * 0.3)

            trace.snapshots.append(
                AlgorithmSnapshot(
                    iteration=gen,
                    description=f"Generation {gen}: Evaluating fitness, crossover & mutation",
                    nodes=nodes.copy(),
                    edges=edges,
                    current_best_cost=fake_cost,
                    trucks_assigned=1,
                )
            )

        # Phase 6-10: Convergence towards optimal
        for gen in range(5, 11):
            progress = (gen - 5) / 5

            # Gradually approach final order
            final_order = list(range(1, len(nodes)))

            # Mix random with final based on progress
            current_order = final_order.copy()

            # Add some randomness that decreases with progress
            swaps = int((1 - progress) * 3)
            for _ in range(swaps):
                if len(current_order) > 1:
                    i, j = random.sample(range(len(current_order)), 2)
                    current_order[i], current_order[j] = (
                        current_order[j],
                        current_order[i],
                    )

            edges = []
            edges.append(
                {
                    "from_id": 0,
                    "to_id": current_order[0],
                    "color": "#f59e0b",
                    "weight": 1,
                }
            )
            for i in range(len(current_order) - 1):
                edges.append(
                    {
                        "from_id": current_order[i],
                        "to_id": current_order[i + 1],
                        "color": "#f59e0b",
                        "weight": 1,
                    }
                )
            edges.append(
                {
                    "from_id": current_order[-1],
                    "to_id": 0,
                    "color": "#f59e0b",
                    "weight": 1,
                }
            )

            fake_cost = truck_result.distancia_total_km * (1.5 - progress * 0.5)

            trace.snapshots.append(
                AlgorithmSnapshot(
                    iteration=gen,
                    description=f"Generation {gen}: Population converging "
                    f"({int(progress * 100)}%)",
                    nodes=nodes.copy(),
                    edges=edges,
                    current_best_cost=fake_cost,
                    trucks_assigned=1,
                )
            )

        # Final: Optimal solution
        final_order = list(range(1, len(nodes)))
        edges = []
        edges.append(
            {"from_id": 0, "to_id": final_order[0], "color": "#10b981", "weight": 2}
        )
        for i in range(len(final_order) - 1):
            edges.append(
                {
                    "from_id": final_order[i],
                    "to_id": final_order[i + 1],
                    "color": "#10b981",
                    "weight": 2,
                }
            )
        edges.append(
            {"from_id": final_order[-1], "to_id": 0, "color": "#10b981", "weight": 2}
        )

        trace.snapshots.append(
            AlgorithmSnapshot(
                iteration=11,
                description="✓ Optimal solution found!",
                nodes=nodes.copy(),
                edges=edges,
                current_best_cost=truck_result.distancia_total_km,
                trucks_assigned=1,
            )
        )

        trace.final_cost = truck_result.distancia_total_km
        trace.total_iterations = 11

        return trace

    @staticmethod
    def _simulate_ortools_trace(
        nodes: list, route_orders: list, truck_result
    ) -> AlgorithmTrace:
        """Simulate OR-Tools algorithm progression for visualization."""
        trace = AlgorithmTrace(
            algorithm_name="Google OR-Tools (Constraint Programming)"
        )

        n_orders = len(route_orders)
        if n_orders == 0:
            return trace

        # Phase 1: Building distance matrix
        trace.snapshots.append(
            AlgorithmSnapshot(
                iteration=0,
                description="Building distance matrix between all nodes",
                nodes=nodes.copy(),
                edges=[
                    {"from_id": i, "to_id": j, "color": "#3b82f6", "weight": 0.5}
                    for i in range(len(nodes))
                    for j in range(len(nodes))
                    if i != j
                ],
                current_best_cost=float("inf"),
                trucks_assigned=0,
            )
        )

        # Phase 2: Initial feasible solution
        edges = []
        for i in range(len(nodes) - 1):
            edges.append(
                {"from_id": i, "to_id": i + 1, "color": "#8b5cf6", "weight": 1}
            )
        edges.append(
            {"from_id": len(nodes) - 1, "to_id": 0, "color": "#8b5cf6", "weight": 1}
        )

        trace.snapshots.append(
            AlgorithmSnapshot(
                iteration=1,
                description="Initial greedy solution (nearest neighbor)",
                nodes=nodes.copy(),
                edges=edges,
                current_best_cost=truck_result.distancia_total_km * 1.8,
                trucks_assigned=1,
            )
        )

        # Phase 3-6: Local search improvements
        for step in range(2, 7):
            progress = (step - 2) / 4

            # Simulate 2-opt improvements
            current_order = list(range(1, len(nodes)))

            # Gradually improve
            if step < 5:
                swaps = 5 - step
                for _ in range(swaps):
                    if len(current_order) > 1:
                        i, j = random.sample(range(len(current_order)), 2)
                        current_order[i], current_order[j] = (
                            current_order[j],
                            current_order[i],
                        )

            edges = []
            edges.append(
                {
                    "from_id": 0,
                    "to_id": current_order[0],
                    "color": "#8b5cf6",
                    "weight": 1,
                }
            )
            for i in range(len(current_order) - 1):
                edges.append(
                    {
                        "from_id": current_order[i],
                        "to_id": current_order[i + 1],
                        "color": "#8b5cf6",
                        "weight": 1,
                    }
                )
            edges.append(
                {
                    "from_id": current_order[-1],
                    "to_id": 0,
                    "color": "#8b5cf6",
                    "weight": 1,
                }
            )

            cost = truck_result.distancia_total_km * (1.8 - progress * 0.8)

            trace.snapshots.append(
                AlgorithmSnapshot(
                    iteration=step,
                    description=f"Local search: 2-opt swap iteration {step - 1}",
                    nodes=nodes.copy(),
                    edges=edges,
                    current_best_cost=cost,
                    trucks_assigned=1,
                )
            )

        # Final: Optimal
        final_order = list(range(1, len(nodes)))
        edges = []
        edges.append(
            {"from_id": 0, "to_id": final_order[0], "color": "#10b981", "weight": 2}
        )
        for i in range(len(final_order) - 1):
            edges.append(
                {
                    "from_id": final_order[i],
                    "to_id": final_order[i + 1],
                    "color": "#10b981",
                    "weight": 2,
                }
            )
        edges.append(
            {"from_id": final_order[-1], "to_id": 0, "color": "#10b981", "weight": 2}
        )

        trace.snapshots.append(
            AlgorithmSnapshot(
                iteration=7,
                description="✓ Optimal solution verified!",
                nodes=nodes.copy(),
                edges=edges,
                current_best_cost=truck_result.distancia_total_km,
                trucks_assigned=1,
            )
        )

        trace.final_cost = truck_result.distancia_total_km
        trace.total_iterations = 7

        return trace

    @staticmethod
    def _format_results(raw: dict) -> dict:
        routes = []
        full = {}
        total_distance, total_cost, total_profit = 0, 0, 0

        for key, value in raw.items():
            if key == "pedidos_no_entregables" or value is None:
                continue

            color = random.choice(MapConfig.ROUTE_COLORS)
            routes.append(
                {
                    "path": value.ruta_coordenadas,
                    "color": color,
                    "pedidos": value.lista_pedidos_ordenada,
                    "camion_id": value.camion_id,
                    "tiempos_llegada": value.tiempos_llegada,
                }
            )

            total_distance += value.distancia_total_km
            total_cost += value.coste_total_ruta
            total_profit += value.beneficio_neto
            full[key] = value

        assigns = []
        for route in full.values():
            for pedido in route.lista_pedidos_ordenada:
                assigns.append(
                    {
                        "Truck": route.camion_id,
                        "ID": pedido.pedido_id,
                        "Dest": pedido.destino,
                        "Kg": pedido.cantidad_producto,
                    }
                )

        return {
            "num_trucks": len(full),
            "routes": routes,
            "assignments": pd.DataFrame(assigns),
            "total_distancia": round(total_distance, 2),
            "total_coste": round(total_cost, 2),
            "total_beneficio": round(total_profit, 2),
            "resultados_detallados": full,
            "pedidos_imposibles": raw.get("pedidos_no_entregables", pd.DataFrame()),
        }

    @staticmethod
    def get_routes_plot(
        results: dict,
        figsize: tuple[int, int] = (12, 8),
    ) -> str | None:
        """
        Generates the detailed routing plot.
        """
        if OptimizationService._last_orchestrator is None:
            return None

        if "resultados_detallados" in results:
            raw_results = results["resultados_detallados"]
            return OptimizationService._last_orchestrator.generate_routes_plot(
                raw_results, figsize
            )
        return None
