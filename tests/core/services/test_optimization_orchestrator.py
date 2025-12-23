from unittest.mock import MagicMock, patch

import pytest

from distribution_platform.core.models.optimization import RouteOptimizationResult
from distribution_platform.core.models.order import Order
from distribution_platform.core.services.optimization_orchestrator import (
    OptimizationOrchestrator,
)


@pytest.fixture
def mock_order():
    return Order(
        pedido_id=1,
        fecha_pedido="2023-01-01",
        producto="A",
        cantidad_producto=100,
        precio_venta=10,
        tiempo_fabricacion_medio=1,
        caducidad=10,
        destino="Madrid",
        distancia_km=100,
        email_cliente="a@a.com",
        dias_totales_caducidad=12,
        fecha_caducidad_final="2023-01-13",
    )


@patch(
    "distribution_platform.core.services.optimization_orchestrator.ClusteringManager"
)
@patch("distribution_platform.core.services.optimization_orchestrator.GraphManager")
class TestOrchestrator:
    def test_optimize_no_orders(self, mock_graph, mock_cluster, mock_order):
        orch = OptimizationOrchestrator()
        assert orch.optimize_deliveries([]) == {}

    def test_impossible_destinations(self, mock_graph, mock_cluster):
        orch = OptimizationOrchestrator()
        imp_order = Order(
            pedido_id=2,
            fecha_pedido="2023-01-01",
            producto="B",
            cantidad_producto=100,
            precio_venta=10,
            tiempo_fabricacion_medio=1,
            caducidad=10,
            destino="Tenerife",
            distancia_km=2000,
            email_cliente="b@b.com",
            dias_totales_caducidad=12,
            fecha_caducidad_final="2023-01-13",
        )
        result = orch.optimize_deliveries([imp_order])
        assert "pedidos_no_entregables" in result

    def test_full_flow_genetic(self, mock_graph, mock_cluster, mock_order):
        orch = OptimizationOrchestrator()

        mock_cluster.return_value.cluster_orders.return_value = {0: [mock_order]}
        mock_graph.return_value.generate_distance_matrix.return_value = {}

        with patch(
            "distribution_platform.core.services.optimization_orchestrator.GeneticStrategy"
        ) as MockStrat:
            mock_strategy_instance = MockStrat.return_value

            mock_result = MagicMock(spec=RouteOptimizationResult)
            mock_result.ciudades_ordenadas = ["A", "B"]
            mock_result.distancia_total_km = 100
            mock_result.tiempo_total_viaje_horas = 5.5
            mock_result.consumo_litros = 20.0
            mock_result.coste_total_ruta = 50.0
            mock_result.lista_pedidos_ordenada = [mock_order]

            mock_strategy_instance.optimize.return_value = mock_result

            results = orch.optimize_deliveries([mock_order], algorithm="genetic")

            assert 0 in results
            assert results[0] == mock_result

    def test_full_flow_ortools(self, mock_graph, mock_cluster, mock_order):
        """Flujo feliz con OR-Tools."""
        orch = OptimizationOrchestrator()
        mock_cluster.return_value.cluster_orders.return_value = {0: [mock_order]}

        with patch(
            "distribution_platform.core.services.optimization_orchestrator.ORToolsStrategy"
        ) as MockStrat:
            mock_strategy_instance = MockStrat.return_value

            mock_res = MagicMock(spec=RouteOptimizationResult)
            mock_res.tiempo_total_viaje_horas = 0
            mock_res.consumo_litros = 0
            mock_res.coste_total_ruta = 0
            mock_res.distancia_total_km = 0
            mock_res.lista_pedidos_ordenada = [mock_order]
            mock_res.ciudades_ordenadas = ["Madrid", "Barcelona"]

            mock_strategy_instance.optimize.return_value = mock_res

            orch.optimize_deliveries([mock_order], algorithm="ortools")
            MockStrat.assert_called_once()

    def test_clustering_failure(self, mock_graph, mock_cluster, mock_order):
        orch = OptimizationOrchestrator()
        mock_cluster.return_value.cluster_orders.return_value = {}
        assert orch.optimize_deliveries([mock_order]) == {}

    def test_get_global_stats(self, mock_graph, mock_cluster):
        orch = OptimizationOrchestrator()
        res1 = MagicMock(spec=RouteOptimizationResult)
        res1.coste_total_ruta = 100.0
        res1.distancia_total_km = 50.0
        res1.lista_pedidos_ordenada = [1, 2]

        res2 = MagicMock(spec=RouteOptimizationResult)
        res2.coste_total_ruta = 200.0
        res2.distancia_total_km = 50.0
        res2.lista_pedidos_ordenada = [3]

        fake_results = {0: res1, 1: res2, "pedidos_no_entregables": []}
        stats = orch.get_global_stats(fake_results)

        assert stats["coste_total"] == 300.0
        assert stats["pedidos_entregados"] == 3

    def test_consolidate_nested_lists(self, mock_graph, mock_cluster, mock_order):
        orch = OptimizationOrchestrator()
        nested_orders = [[mock_order], [mock_order]]

        with patch(
            "distribution_platform.core.services.optimization_orchestrator.consolidate_orders"
        ) as mock_consolidate:
            mock_consolidate.return_value = [mock_order, mock_order]
            mock_cluster.return_value.cluster_orders.return_value = {}
            orch.optimize_deliveries(nested_orders)
            mock_consolidate.assert_called_once()
