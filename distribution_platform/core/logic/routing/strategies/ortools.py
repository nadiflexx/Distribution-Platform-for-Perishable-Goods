"""
Google OR-Tools Strategy.
Robust implementation with debug logging.
"""

import logging

from ortools.constraint_solver import pywrapcp, routing_enums_pb2

from distribution_platform.core.models.optimization import RouteOptimizationResult
from distribution_platform.core.models.order import Order

from .base import RoutingStrategy

logger = logging.getLogger(__name__)


class ORToolsStrategy(RoutingStrategy):
    """
    Wrapper for Google OR-Tools Routing Solver.
    """

    def optimize(self, orders: list[Order], **kwargs) -> RouteOptimizationResult | None:
        if not orders:
            return None

        try:
            # 1. Preparar Datos
            # Lista de lugares: [Origen, Destino1, Destino2, ...]
            # Usamos índices para mapear: 0 -> Origen, i -> orders[i-1]
            locations = [self.origin] + [o.destino for o in orders]
            n_locations = len(locations)

            # print(f"      🔧 OR-Tools: Solving TSP for {n_locations} nodes...")

            # 2. Configurar Manager y Modelo
            # 1 vehículo, inicia en 0, termina en 0
            manager = pywrapcp.RoutingIndexManager(n_locations, 1, 0)
            routing = pywrapcp.RoutingModel(manager)

            # 3. Definir Matriz de Costes (Distancia)
            # Pre-calculamos para evitar callbacks lentos a pandas
            matrix_cache = {}

            def get_dist_cached(from_node, to_node):
                key = (from_node, to_node)
                if key not in matrix_cache:
                    # Usar _get_distance de la clase base (safe lookup)
                    val = self._get_distance(locations[from_node], locations[to_node])
                    # OR-Tools usa enteros. x1000 para metros
                    matrix_cache[key] = int(val * 1000)
                return matrix_cache[key]

            def distance_callback(from_index, to_index):
                from_node = manager.IndexToNode(from_index)
                to_node = manager.IndexToNode(to_index)
                return get_dist_cached(from_node, to_node)

            transit_callback_index = routing.RegisterTransitCallback(distance_callback)
            routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

            # 4. Parámetros de Búsqueda
            search_parameters = pywrapcp.DefaultRoutingSearchParameters()
            # Estrategia inicial rápida
            search_parameters.first_solution_strategy = (
                routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
            )
            # Límite de tiempo estricto
            search_parameters.time_limit.seconds = 2
            # Logs (opcional, set to True to see C++ logs in console)
            # search_parameters.log_search = True

            # 5. Resolver
            solution = routing.SolveWithParameters(search_parameters)

            if not solution:
                logger.error("OR-Tools failed to find a solution.")
                return None

            # 6. Extraer Ruta
            index = routing.Start(0)
            optimized_orders = []

            # Saltamos el nodo inicial (Origen)
            index = solution.Value(routing.NextVar(index))

            # Iterar hasta terminar
            while not routing.IsEnd(index):
                node_index = manager.IndexToNode(index)

                # node_index 0 es Origen. Si sale aquí, algo raro pasó, lo saltamos
                if node_index != 0:
                    # Mapear node_index a orders list (1-based offset)
                    original_order = orders[node_index - 1]
                    optimized_orders.append(original_order)

                index = solution.Value(routing.NextVar(index))

            # 7. Construir Resultado
            # Usamos el helper de la clase base si existe, o construimos manual
            # print(f"      ✅ Solución encontrada: {len(optimized_orders)} paradas.")

            # Recalculamos métricas detalladas usando la lógica Python
            return self._build_result_ortools(optimized_orders)

        except Exception as e:
            logger.error(f"Critical error in OR-Tools optimize: {e}", exc_info=True)
            return None

    def _build_result_ortools(self, orders: list[Order]) -> RouteOptimizationResult:
        """
        Replicates the result building logic to ensure consistence with Genetic strategy.
        Uses _simulate_schedule from Base.
        """
        dist_total = 0.0
        time_total = 0.0
        drive_total = 0.0
        penalty = 0.0
        arrivals = []

        curr = self.origin

        for p in orders:
            # Distancia
            d = self._get_distance(curr, p.destino)
            dist_total += d

            # Tiempos (Safe simulation)
            t, dr = self._simulate_schedule(d)
            time_total += t
            drive_total += dr
            arrivals.append(time_total)

            # Caducidad
            days = time_total / 24.0
            limit = getattr(p, "dias_totales_caducidad", p.caducidad)
            if days > limit:
                penalty += 10000

            curr = p.destino

        # Vuelta
        d_back = self._get_distance(curr, self.origin)
        dist_total += d_back
        t, dr = self._simulate_schedule(d_back)
        time_total += t
        drive_total += dr

        # Costes
        c_driver = drive_total * self.config.salario_conductor_hora
        liters = (dist_total / 100) * self.config.consumo_combustible
        c_fuel = liters * self.config.precio_combustible_litro
        c_total = c_driver + c_fuel

        # Mapa
        coords = []
        if self.graph_service:
            lo, la = self.graph_service.get_coords(self.origin)
            coords.append((lo, la))
            for p in orders:
                c = self.graph_service.get_coords(p.destino)
                if c[0]:
                    coords.append(c)
            coords.append((lo, la))

        cities = [self.origin] + [p.destino for p in orders] + [self.origin]
        rev = sum(float(o.precio_venta) for o in orders)

        return RouteOptimizationResult(
            camion_id=0,
            lista_pedidos_ordenada=orders,
            ciudades_ordenadas=cities,
            ruta_coordenadas=coords,
            tiempos_llegada=[round(x, 2) for x in arrivals],
            distancia_total_km=round(dist_total, 2),
            tiempo_total_viaje_horas=round(time_total, 2),
            tiempo_conduccion_pura_horas=round(drive_total, 2),
            consumo_litros=round(liters, 2),
            coste_combustible=round(c_fuel, 2),
            coste_conductor=round(c_driver, 2),
            coste_total_ruta=round(c_total, 2),
            ingresos_totales=round(rev, 2),
            beneficio_neto=round(rev - c_total, 2),
            valida=(penalty == 0),
            mensaje="✅ Optimal (OR-Tools)" if penalty == 0 else "⚠️ Issues",
        )
