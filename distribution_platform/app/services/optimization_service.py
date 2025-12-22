"""
Optimization/simulation service.
"""

import math
import random

import pandas as pd
import streamlit as st

from distribution_platform.app.state.session_manager import SessionManager
from distribution_platform.config.settings import MapConfig
from distribution_platform.core.models.optimization import SimulationConfig
from distribution_platform.core.services.optimization_orchestrator import (
    OptimizationOrchestrator,
)


class OptimizationService:
    """Handles route optimization logic."""

    @staticmethod
    def run() -> dict | None:
        """Execute the optimization and return results."""
        try:
            algo = OptimizationService._get_algorithm()
            truck_data = SessionManager.get("selected_truck_data")
            orders_data = SessionManager.get("df")

            if not truck_data or not orders_data:
                return None

            # Validate capacity
            if not OptimizationService._validate_capacity(truck_data, orders_data):
                return None

            # Build config
            config = OptimizationService._build_config(truck_data)

            # Run optimization
            orchestrator = OptimizationOrchestrator(config=config, origin_base="Mataró")
            raw_results = orchestrator.optimize_deliveries(orders_data, algorithm=algo)

            # Format results
            return OptimizationService._format_results(raw_results)

        except Exception as e:
            print(f"CRITICAL SIMULATION ERROR: {e}")
            st.error(f"❌ System Error: {e}")
            return None

    @staticmethod
    def _get_algorithm() -> str:
        algo_select = SessionManager.get("algo_select", "")
        return "ortools" if "OR-Tools" in algo_select else "genetic"

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
                f"⚠️ CAPACITY ERROR: {truck_cap}kg capacity insufficient for {total_orders} orders."
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

        # Build assignments dataframe
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
