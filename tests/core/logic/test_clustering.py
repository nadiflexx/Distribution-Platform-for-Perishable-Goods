from unittest.mock import MagicMock, patch

import pytest

from distribution_platform.core.logic.clustering import ClusteringManager
from distribution_platform.core.models.order import Order


@pytest.fixture
def mock_orders():
    o1 = Order(
        pedido_id=1,
        destino="Madrid",
        cantidad_producto=1000,
        caducidad=10,
        precio_venta=10,
        tiempo_fabricacion_medio=1,
        fecha_pedido="2023-01-01",
        producto="A",
        distancia_km=10,
        email_cliente="a@a.com",
        dias_totales_caducidad=10,
        fecha_caducidad_final="2023-01-10",
    )
    o2 = Order(
        pedido_id=2,
        destino="Madrid",
        cantidad_producto=1000,
        caducidad=10,
        precio_venta=10,
        tiempo_fabricacion_medio=1,
        fecha_pedido="2023-01-01",
        producto="B",
        distancia_km=10,
        email_cliente="a@a.com",
        dias_totales_caducidad=10,
        fecha_caducidad_final="2023-01-10",
    )
    o3 = Order(
        pedido_id=3,
        destino="Barcelona",
        cantidad_producto=500,
        caducidad=5,
        precio_venta=10,
        tiempo_fabricacion_medio=1,
        fecha_pedido="2023-01-01",
        producto="C",
        distancia_km=10,
        email_cliente="a@a.com",
        dias_totales_caducidad=5,
        fecha_caducidad_final="2023-01-10",
    )
    return [o1, o2, o3]


@pytest.fixture
def mock_cache():
    cache = MagicMock()
    cache.get.side_effect = (
        lambda city: "40,-3"
        if city == "Madrid"
        else "41,2"
        if city == "Barcelona"
        else None
    )
    return cache


class TestClusteringManager:
    def test_cluster_orders_basic(self, mock_cache, mock_orders):
        manager = ClusteringManager(mock_cache)

        with patch("distribution_platform.core.logic.clustering.KMeans") as MockKMeans:
            kmeans_instance = MockKMeans.return_value
            kmeans_instance.fit_predict.return_value = [0, 0, 1]

            result = manager.cluster_orders(mock_orders, n_trucks=2, max_capacity=5000)

            assert len(result) == 2
            assert len(result[0]) == 2
            assert len(result[1]) == 1

    def test_enrich_coordinates_missing(self, mock_cache, mock_orders):
        """Si no hay coordenadas, debe filtrar el pedido."""
        mock_cache.get.side_effect = None
        mock_cache.get.return_value = None

        manager = ClusteringManager(mock_cache)

        enriched = manager._enrich_coordinates(mock_orders)

        assert len(enriched) == 0

    def test_balancing_logic(self, mock_cache, mock_orders):
        """
        Prueba crítica: El pedido de Madrid (1000kg) excede la capacidad (800kg).
        Debe moverlo a otro cluster o crear uno nuevo.
        """
        manager = ClusteringManager(mock_cache)

        clusters = {0: [mock_orders[0], mock_orders[1]]}

        balanced = manager._balance_clusters_by_weight(
            clusters, unit_weight=1.0, max_capacity=1500, n_trucks=1
        )

        assert len(balanced) > 1
        assert 1 in balanced

    def test_empty_input(self, mock_cache):
        manager = ClusteringManager(mock_cache)
        assert manager.cluster_orders([], 1) == {}
