"""
Genetic Algorithm Strategy (Memetic Version).
Enhanced with 2-Opt Mutation and larger population to compete with exact solvers.
"""

import random

from distribution_platform.core.models.optimization import RouteOptimizationResult
from distribution_platform.core.models.order import Order

from .base import RoutingStrategy


class GeneticStrategy(RoutingStrategy):
    """
    Implementation of a Memetic Genetic Algorithm (GA + Local Search).
    """

    def optimize(self, orders: list[Order], **kwargs) -> RouteOptimizationResult | None:
        generations = kwargs.get("generations", 500)
        pop_size = kwargs.get("pop_size", 200)

        if not orders:
            return None
        orders = [p for p in orders if p is not None]
        if not orders:
            return None

        if len(orders) <= 2:
            return self._build_result(orders, self._calculate_fitness(orders))

        if len(orders) < 10:
            generations = 100
            pop_size = 50

        population = [self._greedy_route(orders)]
        for _ in range(pop_size - 1):
            population.append(random.sample(orders, len(orders)))

        best_genome = None
        best_score = float("inf")

        stagnant_gens = 0
        max_stagnant = 40

        for _ in range(generations):
            scored_pop = []

            for individual in population:
                score = self._quick_fitness(individual)

                if score < best_score:
                    best_score = score
                    best_genome = list(individual)
                    stagnant_gens = 0

                scored_pop.append((score, individual))

            stagnant_gens += 1

            if stagnant_gens >= max_stagnant:
                break

            scored_pop.sort(key=lambda x: x[0])
            survivors = [x[1] for x in scored_pop[: int(pop_size * 0.3)]]

            new_pop = []

            new_pop.append(list(survivors[0]))

            while len(new_pop) < pop_size:
                parent1 = random.choice(survivors)
                parent2 = random.choice(survivors)

                child = self._crossover_ox(parent1, parent2)

                if random.random() < 0.3:
                    self._mutate_inversion(child)

                new_pop.append(child)

            population = new_pop

        final_route = self._two_opt_polish(best_genome)

        full_metrics = self._calculate_fitness(final_route)
        return self._build_result(final_route, full_metrics)

    def _crossover_ox(self, p1: list[Order], p2: list[Order]) -> list[Order]:
        size = len(p1)
        a, b = sorted(random.sample(range(size), 2))
        child: list[Order | None] = [None] * size
        child[a:b] = p1[a:b]
        pos = b
        for item in p2:
            if item not in p1[a:b]:
                if pos >= size:
                    pos = 0
                child[pos] = item
                pos += 1
        return child  # type: ignore

    def _mutate_inversion(self, route: list[Order]) -> None:
        """
        Inversion Mutation (simulates a 2-opt move).
        Selects a segment and reverses it. Better for geometry.
        """
        size = len(route)
        if size < 2:
            return
        i, j = sorted(random.sample(range(size), 2))
        route[i : j + 1] = route[i : j + 1][::-1]

    def _quick_fitness(self, route):
        """Geometric distance only (Fast)."""
        d = 0.0
        curr = self.origin
        for p in route:
            d += self._get_distance(curr, p.destino)
            curr = p.destino
        d += self._get_distance(curr, self.origin)
        return d

    def _greedy_route(self, orders):
        unvisited = orders[:]
        route = []
        curr = self.origin
        while unvisited:
            nxt = min(unvisited, key=lambda o: self._get_distance(curr, o.destino))
            route.append(nxt)
            unvisited.remove(nxt)
            curr = nxt.destino
        return route

    def _two_opt_polish(self, route):
        """Deterministic 2-Opt for the final result."""
        if not route:
            return []
        best = route[:]
        improved = True
        while improved:
            improved = False
            for i in range(len(best) - 1):
                for j in range(i + 1, len(best)):
                    if j - i == 1:
                        continue
                    new_r = best[:]
                    new_r[i:j] = best[i:j][::-1]
                    if self._quick_fitness(new_r) < self._quick_fitness(best):
                        best = new_r
                        improved = True
                        break
                if improved:
                    break
        return best

    def _calculate_fitness(self, route: list[Order]) -> tuple:
        """Full simulation (Time, Cost, Labor Rules). Slow."""
        dist_total = 0.0
        time_total = 0.0
        drive_total = 0.0
        penalty = 0.0
        arrivals = []
        curr = self.origin

        for p in route:
            d = self._get_distance(curr, p.destino)
            dist_total += d
            t, dr = self._simulate_schedule(d)
            time_total += t
            drive_total += dr
            arrivals.append(time_total)
            if (time_total / 24.0) > getattr(p, "caducidad", 99):
                penalty += 10000
            curr = p.destino

        d_back = self._get_distance(curr, self.origin)
        dist_total += d_back
        t, dr = self._simulate_schedule(d_back)
        time_total += t
        drive_total += dr

        c_driver = drive_total * self.config.salario_conductor_hora
        liters = (dist_total / 100) * self.config.consumo_combustible
        c_fuel = liters * self.config.precio_combustible_litro
        c_total = c_driver + c_fuel
        score = c_total + penalty

        return (
            score,
            penalty == 0,
            dist_total,
            time_total,
            drive_total,
            liters,
            c_total,
            c_driver,
            c_fuel,
            arrivals,
        )

    def _build_result(self, orders, fit_data):
        (_, valid, dist, time, drive, lit, cost, c_driv, c_fuel, arrs) = fit_data

        cities = [self.origin] + [p.destino for p in orders] + [self.origin]

        coords = []
        if self.graph_service:
            lo, la = self.graph_service.get_coords(self.origin)
            coords.append((lo, la))
            for p in orders:
                c = self.graph_service.get_coords(p.destino)
                if c[0]:
                    coords.append(c)
            coords.append((lo, la))

        return RouteOptimizationResult(
            camion_id=0,
            lista_pedidos_ordenada=orders,
            ciudades_ordenadas=cities,
            ruta_coordenadas=coords,
            tiempos_llegada=[round(x, 2) for x in arrs],
            distancia_total_km=round(dist, 2),
            tiempo_total_viaje_horas=round(time, 2),
            tiempo_conduccion_pura_horas=round(drive, 2),
            consumo_litros=round(lit, 2),
            coste_combustible=round(c_fuel, 2),
            coste_conductor=round(c_driv, 2),
            coste_total_ruta=round(cost, 2),
            ingresos_totales=round(sum(p.precio_venta for p in orders), 2),
            beneficio_neto=round(sum(p.precio_venta for p in orders) - cost, 2),
            valida=valid,
            mensaje="✅ Optimal (Genetic)" if valid else "⚠️ Issues",
        )
