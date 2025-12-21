from unittest.mock import MagicMock

import pytest

from distribution_platform.core.logic.routing.strategies.genetic import GeneticStrategy
from distribution_platform.core.models.optimization import SimulationConfig
from distribution_platform.core.models.order import Order


@pytest.fixture
def orders():
    return [
        Order(
            pedido_id=1,
            destino="A",
            precio_venta=10,
            cantidad_producto=1,
            caducidad=10,
            fecha_pedido="2023-01-01",
            producto="P",
            tiempo_fabricacion_medio=1,
            distancia_km=10,
            email_cliente="valid@email.com",  # <--- CORREGIDO
            dias_totales_caducidad=10,
            fecha_caducidad_final="2023-01-10",
        ),
        Order(
            pedido_id=2,
            destino="B",
            precio_venta=10,
            cantidad_producto=1,
            caducidad=10,
            fecha_pedido="2023-01-01",
            producto="P",
            tiempo_fabricacion_medio=1,
            distancia_km=10,
            email_cliente="valid@email.com",  # <--- CORREGIDO
            dias_totales_caducidad=10,
            fecha_caducidad_final="2023-01-10",
        ),
    ]


@pytest.fixture
def genetic_strat():
    mock_matrix = MagicMock()
    # Usamos configuración por defecto válida
    config = SimulationConfig()
    strat = GeneticStrategy(mock_matrix, config, "Origin")
    strat._get_distance = lambda o, d: 10.0 if o != d else 0.0
    return strat


class TestGeneticStrategy:
    def test_crossover_integrity(self, genetic_strat, orders):
        p1 = orders[:]
        p2 = orders[::-1]
        child = genetic_strat._crossover_ox(p1, p2)
        assert len(child) == len(p1)
        child_ids = sorted([o.pedido_id for o in child])
        assert child_ids == [1, 2]

    def test_mutation_inversion(self, genetic_strat, orders):
        route = orders[:]
        genetic_strat._mutate_inversion(route)
        assert len(route) == len(orders)
        assert sorted([o.pedido_id for o in route]) == [1, 2]

    def test_optimize_trivial(self, genetic_strat, orders):
        result = genetic_strat.optimize(orders, generations=1, pop_size=2)
        assert result is not None
        assert len(result.lista_pedidos_ordenada) == 2
        assert result.valida is True

    def test_optimize_empty(self, genetic_strat):
        assert genetic_strat.optimize([]) is None
        assert genetic_strat.optimize([None]) is None

    def test_quick_fitness(self, genetic_strat, orders):
        score = genetic_strat._quick_fitness(orders)
        assert score == 30.0

    def test_full_evolution(self, genetic_strat, orders):
        """
        Ejecuta el bucle principal del algoritmo genético.
        Necesitamos suficientes pedidos para que no entre en caso trivial.
        """
        # Creamos 5 pedidos falsos para forzar evolución
        many_orders = [
            Order(
                pedido_id=i,
                destino=f"D{i}",
                precio_venta=10,
                cantidad_producto=1,
                caducidad=10,
                fecha_pedido="2023-01-01",
                producto="P",
                tiempo_fabricacion_medio=1,
                distancia_km=10,
                email_cliente="a@a.com",
                dias_totales_caducidad=10,
                fecha_caducidad_final="2023-01-10",
            )
            for i in range(5)
        ]

        # Ejecutamos pocas generaciones para que sea rápido pero cubra el código
        result = genetic_strat.optimize(many_orders, generations=2, pop_size=4)

        assert result is not None
        assert len(result.lista_pedidos_ordenada) == 5
        # Verificamos que se calcularon métricas financieras
        assert result.coste_total_ruta > 0

    def test_build_result_with_graph_service(self, genetic_strat, orders):
        """Verifica la integración con el servicio de grafo para coordenadas."""
        mock_graph = MagicMock()
        mock_graph.get_coords.return_value = (40.0, -3.0)  # Lat, Lon fake
        genetic_strat.graph_service = mock_graph

        # Simulamos datos de fitness
        fit_data = (100, True, 50, 1, 1, 10, 20, 10, 10, [1, 2])

        result = genetic_strat._build_result(orders, fit_data)

        # Debe tener coordenadas para Origen + 2 pedidos + Origen = 4 puntos
        assert len(result.ruta_coordenadas) == 4
        assert result.ruta_coordenadas[0] == (40.0, -3.0)
