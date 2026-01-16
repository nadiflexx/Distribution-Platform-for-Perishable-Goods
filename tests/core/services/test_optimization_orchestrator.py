import base64
from unittest.mock import MagicMock, patch

import pytest

from distribution_platform.core.logic.routing.clustering.base import ClusteringStrategy
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
        orch = OptimizationOrchestrator()
        mock_cluster.return_value.cluster_orders.return_value = {0: [mock_order]}
        with patch(
            "distribution_platform.core.services.optimization_orchestrator.ORToolsStrategy"
        ) as MockStrat:
            mock_strategy_instance = MockStrat.return_value
            mock_res = MagicMock(spec=RouteOptimizationResult)
            mock_res.lista_pedidos_ordenada = [mock_order]
            mock_res.ciudades_ordenadas = ["Madrid"]
            mock_res.distancia_total_km = 10
            mock_res.tiempo_total_viaje_horas = 5.5
            mock_res.consumo_litros = 20.0
            mock_res.coste_total_ruta = 50.0
            mock_res.lista_pedidos_ordenada = [mock_order]
            mock_strategy_instance.optimize.return_value = mock_res  # Mock success

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
        res1.tiempo_total_viaje_horas = 5.5
        res2 = MagicMock(spec=RouteOptimizationResult)
        res2.coste_total_ruta = 200.0
        res2.distancia_total_km = 50.0
        res2.lista_pedidos_ordenada = [3]
        res2.tiempo_total_viaje_horas = 5.5
        fake_results = {0: res1, 1: res2, "pedidos_no_entregables": []}

        stats = orch.get_global_stats(fake_results)
        assert stats["coste_total"] == 300.0

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

    def test_strategy_management(self, mock_graph, mock_cluster):
        orch = OptimizationOrchestrator()

        mock_new_strat = MagicMock(spec=ClusteringStrategy)
        mock_new_strat.name = "MockStrategy"
        orch.set_clustering_strategy(mock_new_strat)

        mock_cluster.return_value.get_strategy_name.return_value = "MockStrategy"
        assert orch.get_clustering_strategy_name() == "MockStrategy"

        orch.get_clustering_plot(title="Test")
        mock_cluster.return_value.generate_plot.assert_called_with(
            figsize=(12, 8), title="Test"
        )

    def test_optimize_edge_cases(self, mock_graph, mock_cluster, mock_order):
        orch = OptimizationOrchestrator()

        mock_cluster.return_value.cluster_orders.return_value = {0: [], 1: [mock_order]}

        with patch(
            "distribution_platform.core.services.optimization_orchestrator.GeneticStrategy"
        ) as MockStrat:
            strat_instance = MockStrat.return_value
            strat_instance.optimize.return_value = None

            results = orch.optimize_deliveries([mock_order], algorithm="genetic")

            assert 0 in results
            assert results[0] is None

            assert 1 not in results

            assert isinstance(results, dict)

    def test_generate_routes_plot(self, mock_graph, mock_cluster, mock_order):
        orch = OptimizationOrchestrator()

        mock_res = MagicMock(spec=RouteOptimizationResult)
        mock_res.camion_id = 1
        mock_res.ruta_coordenadas = [(40.416, -3.703), (41.385, 2.173)]
        mock_res.ciudades_ordenadas = ["Madrid", "Barcelona"]

        results = {
            0: mock_res,
            "pedidos_no_entregables": [],
        }

        base64_img = orch.generate_routes_plot(results)

        assert isinstance(base64_img, str)
        assert len(base64_img) > 100

        try:
            decoded = base64.b64decode(base64_img)
            assert len(decoded) > 0
        except Exception:
            pytest.fail("The output is not a valid base64 image")

    def test_generate_routes_plot_empty(self, mock_graph, mock_cluster):
        orch = OptimizationOrchestrator()
        assert orch.generate_routes_plot({}) == ""
