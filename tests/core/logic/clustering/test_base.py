import base64
from unittest.mock import MagicMock

import numpy as np
import pytest

from distribution_platform.core.logic.routing.clustering.base import ClusteringStrategy
from distribution_platform.core.models.order import Order
from distribution_platform.infrastructure.persistence.coordinates import CoordinateCache

DEFAULT_ORDER_ATTRS = {
    "fecha_pedido": "2023-01-01",
    "producto": "Producto Test",
    "precio_venta": 10.0,
    "tiempo_fabricacion_medio": 24,
    "distancia_km": 100.0,
    "email_cliente": "test@example.com",
    "dias_totales_caducidad": 30,
    "fecha_caducidad_final": "2023-02-01",
    "caducidad": 5,
}


class MockClusteringStrategy(ClusteringStrategy):
    @property
    def name(self) -> str:
        return "Mock Strategy"

    @property
    def description(self) -> str:
        return "Test implementation"

    def _perform_clustering(
        self, scaled_data: np.ndarray, n_clusters: int
    ) -> list[int]:
        return [i % n_clusters for i in range(len(scaled_data))]


@pytest.fixture
def mock_coord_cache():
    cache = MagicMock(spec=CoordinateCache)
    cache.get.return_value = "40.4168,-3.7038"
    return cache


@pytest.fixture
def strategy(mock_coord_cache):
    return MockClusteringStrategy(mock_coord_cache)


@pytest.fixture
def sample_orders():
    return [
        Order(
            pedido_id=1, destino="Madrid", cantidad_producto=100, **DEFAULT_ORDER_ATTRS
        ),
        Order(
            pedido_id=2,
            destino="Barcelona",
            cantidad_producto=200,
            **DEFAULT_ORDER_ATTRS,
        ),
        Order(
            pedido_id=3,
            destino="Valencia",
            cantidad_producto=150,
            **DEFAULT_ORDER_ATTRS,
        ),
    ]


def test_initialization(strategy):
    assert strategy.name == "Mock Strategy"
    assert strategy.scaler is not None


def test_enrich_coordinates_success(strategy, mock_coord_cache, sample_orders):
    mock_coord_cache.get.side_effect = ["40.0,-3.0", "41.0,2.0", "39.0,-0.3"]

    enriched = strategy._enrich_coordinates(sample_orders)

    assert len(enriched) == 3
    assert enriched[0]["lat"] == 40.0
    assert enriched[0]["lon"] == -3.0
    assert enriched[0]["urgencia"] == pytest.approx(8.33, 0.01)
    assert enriched[0]["pedido"].pedido_id == 1


def test_enrich_coordinates_missing_data(strategy, mock_coord_cache, sample_orders):
    mock_coord_cache.get.side_effect = ["40.0,-3.0", None, "invalid,coords"]

    enriched = strategy._enrich_coordinates(sample_orders)

    assert len(enriched) == 1
    assert enriched[0]["pedido"].pedido_id == 1


def test_cluster_orders_flow(strategy, mock_coord_cache, sample_orders):
    n_trucks = 2

    result = strategy.cluster_orders(
        sample_orders, n_trucks=n_trucks, unit_weight=1.0, max_capacity=1000.0
    )

    assert len(result) == 2
    assert len(result[0]) == 2
    assert len(result[1]) == 1
    assert strategy._last_data is not None


def test_cluster_orders_empty_input(strategy):
    assert strategy.cluster_orders([], 5) == {}


def test_balancing_logic_simple_redistribution(strategy, mock_coord_cache):
    o1 = Order(pedido_id=1, destino="A", cantidad_producto=80, **DEFAULT_ORDER_ATTRS)
    o2 = Order(pedido_id=2, destino="B", cantidad_producto=30, **DEFAULT_ORDER_ATTRS)

    orders = [o1, o2]

    strategy._perform_clustering = lambda data, k: [0, 0]

    result = strategy.cluster_orders(orders, n_trucks=2, max_capacity=100.0)

    assert len(result[0]) == 1
    assert result[0][0].cantidad_producto == 30

    assert len(result[1]) == 1
    assert result[1][0].cantidad_producto == 80


def test_balancing_logic_needs_new_truck(strategy, mock_coord_cache):
    o1 = Order(pedido_id=1, destino="A", cantidad_producto=90, **DEFAULT_ORDER_ATTRS)
    o2 = Order(pedido_id=2, destino="B", cantidad_producto=90, **DEFAULT_ORDER_ATTRS)

    orders = [o1, o2]

    strategy._perform_clustering = lambda data, k: [0, 0]

    result = strategy.cluster_orders(orders, n_trucks=1, max_capacity=100.0)

    assert len(result) >= 2

    total_pedidos = sum(len(v) for v in result.values())
    assert total_pedidos == 2

    for _, cluster_orders in result.items():
        weight = sum(o.cantidad_producto for o in cluster_orders)
        assert weight <= 100.0


def test_generate_plot_without_data(strategy):
    plot_b64 = strategy.generate_plot()
    assert isinstance(plot_b64, str)
    assert len(plot_b64) > 0
    assert base64.b64decode(plot_b64)


def test_generate_plot_with_data(strategy, sample_orders):
    strategy.cluster_orders(sample_orders, n_trucks=2)

    plot_b64 = strategy.generate_plot(title="Test Plot")

    assert isinstance(plot_b64, str)
    assert len(plot_b64) > 100

    decoded = base64.b64decode(plot_b64)
    assert decoded[:8] == b"\x89PNG\r\n\x1a\n"


def test_smart_labeling_logic_in_plot(strategy, sample_orders):
    orders = sample_orders
    strategy.cluster_orders(orders, n_trucks=1)

    try:
        strategy.generate_plot()
    except Exception as e:
        pytest.fail(f"generate_plot raised exception: {e}")
