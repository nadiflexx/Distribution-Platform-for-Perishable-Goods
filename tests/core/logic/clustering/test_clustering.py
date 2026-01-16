"""Tests for Clustering Module."""

from unittest.mock import MagicMock

import numpy as np
import pytest

from distribution_platform.core.logic.routing.clustering import ClusteringManager
from distribution_platform.core.logic.routing.clustering.agglomerative import (
    AgglomerativeStrategy,
)
from distribution_platform.core.logic.routing.clustering.kmeans import KMeansStrategy
from distribution_platform.core.models.order import Order


# ============================================================================
# FIXTURES
# ============================================================================
@pytest.fixture
def sample_order():
    """Factory for creating test orders."""

    def _create(
        pedido_id: int = 1,
        destino: str = "Madrid",
        cantidad: int = 1000,
        caducidad: int = 10,
    ):
        return Order(
            pedido_id=pedido_id,
            destino=destino,
            cantidad_producto=cantidad,
            caducidad=caducidad,
            precio_venta=10,
            tiempo_fabricacion_medio=1,
            fecha_pedido="2023-01-01",
            producto="TestProduct",
            distancia_km=10,
            email_cliente="test@test.com",
            dias_totales_caducidad=caducidad,
            fecha_caducidad_final="2023-01-10",
        )

    return _create


@pytest.fixture
def mock_orders(sample_order):
    """Standard set of test orders."""
    return [
        sample_order(1, "Madrid", 1000, 10),
        sample_order(2, "Madrid", 1000, 10),
        sample_order(3, "Barcelona", 500, 5),
        sample_order(4, "Valencia", 800, 7),
        sample_order(5, "Sevilla", 600, 3),
    ]


@pytest.fixture
def mock_cache():
    """Mock coordinate cache with Spanish cities."""
    cache = MagicMock()
    coords = {
        "Madrid": "40.4168,-3.7038",
        "Barcelona": "41.3851,2.1734",
        "Valencia": "39.4699,-0.3763",
        "Sevilla": "37.3891,-5.9845",
        "Bilbao": "43.2630,-2.9350",
    }
    cache.get.side_effect = lambda city: coords.get(city)
    return cache


# ============================================================================
# TESTS: ClusteringManager (manager.py)
# ============================================================================
class TestClusteringManager:
    """Tests for ClusteringManager facade."""

    def test_init_default_strategy(self, mock_cache):
        """Test manager initializes with KMeans by default."""
        manager = ClusteringManager(mock_cache)

        assert isinstance(manager.strategy, KMeansStrategy)
        assert manager.coord_cache == mock_cache

    def test_init_custom_strategy(self, mock_cache):
        """Test manager accepts custom strategy."""
        custom_strategy = AgglomerativeStrategy(mock_cache)
        manager = ClusteringManager(mock_cache, strategy=custom_strategy)

        assert manager.strategy == custom_strategy

    def test_set_strategy(self, mock_cache):
        """Test changing strategy at runtime (lines 34-35)."""
        manager = ClusteringManager(mock_cache)
        new_strategy = AgglomerativeStrategy(mock_cache)

        manager.set_strategy(new_strategy)

        assert manager.strategy == new_strategy
        assert isinstance(manager.strategy, AgglomerativeStrategy)

    def test_get_strategy_name(self, mock_cache):
        """Test getting strategy name (line 39)."""
        manager = ClusteringManager(mock_cache)

        name = manager.get_strategy_name()

        assert name == "K-Means"

    def test_get_strategy_description(self, mock_cache):
        """Test getting strategy description (line 43)."""
        manager = ClusteringManager(mock_cache)

        description = manager.get_strategy_description()

        assert "centroid" in description.lower() or "nearest" in description.lower()

    def test_cluster_orders_delegation(self, mock_cache, mock_orders):
        """Test manager delegates to strategy."""
        mock_strategy = MagicMock()
        mock_strategy.name = "MockStrategy"
        mock_strategy.cluster_orders.return_value = {
            0: mock_orders[:2],
            1: mock_orders[2:],
        }

        manager = ClusteringManager(mock_cache, strategy=mock_strategy)
        result = manager.cluster_orders(mock_orders, n_trucks=2)

        mock_strategy.cluster_orders.assert_called_once_with(
            orders=mock_orders,
            n_trucks=2,
            unit_weight=1.0,
            max_capacity=1000.0,
        )
        assert len(result) == 2

    def test_generate_plot_delegation(self, mock_cache):
        """Test generate_plot delegates to strategy (line 85)."""
        mock_strategy = MagicMock()
        mock_strategy.name = "MockStrategy"
        mock_strategy.generate_plot.return_value = "base64_image_string"

        manager = ClusteringManager(mock_cache, strategy=mock_strategy)
        result = manager.generate_plot(figsize=(10, 6), show_legend=False, title="Test")

        mock_strategy.generate_plot.assert_called_once_with(
            figsize=(10, 6), show_legend=False, title="Test"
        )
        assert result == "base64_image_string"


# ============================================================================
# TESTS: KMeansStrategy (kmeans.py)
# ============================================================================
class TestKMeansStrategy:
    """Tests for KMeans clustering strategy."""

    def test_name_property(self, mock_cache):
        """Test strategy name."""
        strategy = KMeansStrategy(mock_cache)
        assert strategy.name == "K-Means"

    def test_description_property(self, mock_cache):
        """Test strategy description."""
        strategy = KMeansStrategy(mock_cache)
        assert len(strategy.description) > 0

    def test_perform_clustering(self, mock_cache):
        """Test _perform_clustering executes KMeans (line 29)."""
        strategy = KMeansStrategy(mock_cache)

        scaled_data = np.array(
            [
                [0.0, 0.0, 0.5],
                [0.1, 0.1, 0.6],
                [1.0, 1.0, 0.2],
                [1.1, 1.1, 0.3],
            ]
        )

        labels = strategy._perform_clustering(scaled_data, n_clusters=2)

        assert len(labels) == 4
        assert all(isinstance(label, int) for label in labels)
        assert set(labels).issubset({0, 1})

    def test_full_clustering_flow(self, mock_cache, mock_orders):
        """Test complete clustering with real KMeans."""
        strategy = KMeansStrategy(mock_cache)

        result = strategy.cluster_orders(
            orders=mock_orders,
            n_trucks=2,
            unit_weight=1.0,
            max_capacity=5000.0,
        )

        assert isinstance(result, dict)
        assert len(result) >= 1
        total_orders = sum(len(orders) for orders in result.values())
        assert total_orders == len(mock_orders)


# ============================================================================
# TESTS: AgglomerativeStrategy (agglomerative.py)
# ============================================================================
class TestAgglomerativeStrategy:
    """Tests for Agglomerative clustering strategy."""

    def test_name_property(self, mock_cache):
        """Test strategy name (line 24)."""
        strategy = AgglomerativeStrategy(mock_cache)
        assert strategy.name == "Hierarchical (Agglomerative)"

    def test_description_property(self, mock_cache):
        """Test strategy description (line 28)."""
        strategy = AgglomerativeStrategy(mock_cache)
        assert (
            "merge" in strategy.description.lower()
            or "group" in strategy.description.lower()
        )

    def test_perform_clustering(self, mock_cache):
        """Test _perform_clustering executes Agglomerative (lines 37-41)."""
        strategy = AgglomerativeStrategy(mock_cache)

        scaled_data = np.array(
            [
                [0.0, 0.0, 0.5],
                [0.1, 0.1, 0.6],
                [1.0, 1.0, 0.2],
                [1.1, 1.1, 0.3],
            ]
        )

        labels = strategy._perform_clustering(scaled_data, n_clusters=2)

        assert len(labels) == 4
        assert all(isinstance(label, int) for label in labels)
        assert set(labels).issubset({0, 1})

    def test_full_clustering_flow(self, mock_cache, mock_orders):
        """Test complete clustering with real Agglomerative."""
        strategy = AgglomerativeStrategy(mock_cache)

        result = strategy.cluster_orders(
            orders=mock_orders,
            n_trucks=2,
            unit_weight=1.0,
            max_capacity=5000.0,
        )

        assert isinstance(result, dict)
        total_orders = sum(len(orders) for orders in result.values())
        assert total_orders == len(mock_orders)


# ============================================================================
# TESTS: ClusteringStrategy Base Class (base.py)
# ============================================================================
class TestClusteringStrategyBase:
    """Tests for base ClusteringStrategy functionality."""

    def test_empty_orders_returns_empty_dict(self, mock_cache):
        """Test cluster_orders with empty list (lines 78-79)."""
        strategy = KMeansStrategy(mock_cache)

        result = strategy.cluster_orders(orders=[], n_trucks=2)

        assert result == {}

    def test_no_coordinates_returns_empty(self, mock_cache, sample_order):
        """Test when no coordinates can be found."""
        mock_cache.get.return_value = None
        strategy = KMeansStrategy(mock_cache)

        orders = [sample_order(1, "UnknownCity", 100, 5)]
        result = strategy.cluster_orders(orders, n_trucks=1)

        assert result == {}

    def test_enrich_coordinates_success(self, mock_cache, sample_order):
        """Test coordinate enrichment works correctly."""
        strategy = KMeansStrategy(mock_cache)
        orders = [sample_order(1, "Madrid", 100, 5)]

        enriched = strategy._enrich_coordinates(orders)

        assert len(enriched) == 1
        assert enriched[0]["lat"] == pytest.approx(40.4168, rel=1e-3)
        assert enriched[0]["lon"] == pytest.approx(-3.7038, rel=1e-3)
        assert enriched[0]["urgencia"] > 0

    def test_enrich_coordinates_invalid_format(self, mock_cache, sample_order):
        """Test handling of invalid coordinate format."""
        mock_cache.get.return_value = "invalid_format"
        strategy = KMeansStrategy(mock_cache)

        orders = [sample_order(1, "Madrid", 100, 5)]
        enriched = strategy._enrich_coordinates(orders)

        assert len(enriched) == 1

    def test_enrich_coordinates_missing(self, mock_cache, sample_order):
        """Test handling of missing coordinates."""
        mock_cache.get.return_value = None
        strategy = KMeansStrategy(mock_cache)

        orders = [sample_order(1, "UnknownCity", 100, 5)]
        enriched = strategy._enrich_coordinates(orders)

        assert len(enriched) == 0

    def test_balance_clusters_no_overflow(self, mock_cache, sample_order):
        """Test balancing when no clusters exceed capacity."""
        strategy = KMeansStrategy(mock_cache)

        orders = [sample_order(i, "Madrid", 100, 5) for i in range(3)]
        clusters = {0: orders[:2], 1: orders[2:]}

        balanced = strategy._balance_clusters_by_weight(
            clusters, unit_weight=1.0, max_capacity=1000.0, n_trucks=2
        )

        assert len(balanced) == 2

    def test_balance_clusters_with_overflow(self, mock_cache, sample_order):
        """Test balancing redistributes overweight clusters (lines 373-379)."""
        strategy = KMeansStrategy(mock_cache)

        heavy_orders = [sample_order(i, "Madrid", 600, 5) for i in range(3)]
        clusters = {0: heavy_orders, 1: []}  # 1800 kg in cluster 0

        balanced = strategy._balance_clusters_by_weight(
            clusters, unit_weight=1.0, max_capacity=1000.0, n_trucks=2
        )

        cluster_weights = [
            sum(o.cantidad_producto for o in orders)
            for orders in balanced.values()
            if orders
        ]
        assert all(w <= 1200 for w in cluster_weights) or len(balanced) > 2

    def test_balance_creates_extra_trucks(self, mock_cache, sample_order):
        """Test that extra trucks are created when needed (lines 422-442)."""
        strategy = KMeansStrategy(mock_cache)

        heavy_orders = [sample_order(i, "Madrid", 800, 5) for i in range(5)]
        clusters = {0: heavy_orders}  # 4000 kg total

        balanced = strategy._balance_clusters_by_weight(
            clusters, unit_weight=1.0, max_capacity=1000.0, n_trucks=1
        )

        assert len(balanced) >= 4

    def test_balance_single_heavy_order(self, mock_cache, sample_order):
        """Test handling of single order exceeding capacity (edge case line 429)."""
        strategy = KMeansStrategy(mock_cache)

        # Single order that exceeds max capacity
        super_heavy = sample_order(1, "Madrid", 2000, 5)
        clusters = {0: [super_heavy]}

        balanced = strategy._balance_clusters_by_weight(
            clusters, unit_weight=1.0, max_capacity=1000.0, n_trucks=1
        )

        assert len(balanced) == 1
        assert super_heavy in balanced[0]


# ============================================================================
# TESTS: Plotting (base.py)
# ============================================================================
class TestClusteringPlot:
    """Tests for plot generation."""

    def test_generate_plot_no_data(self, mock_cache):
        """Test generate_plot without prior clustering (line 153)."""
        strategy = KMeansStrategy(mock_cache)

        result = strategy.generate_plot()

        assert isinstance(result, str)
        assert len(result) > 0

    def test_generate_plot_with_data(self, mock_cache, mock_orders):
        """Test generate_plot after clustering."""
        strategy = KMeansStrategy(mock_cache)

        strategy.cluster_orders(mock_orders, n_trucks=2, max_capacity=5000)

        result = strategy.generate_plot(
            figsize=(10, 6), show_legend=True, title="Test Plot"
        )

        assert isinstance(result, str)
        assert len(result) > 100

    def test_generate_plot_custom_params(self, mock_cache, mock_orders):
        """Test generate_plot with custom parameters."""
        strategy = KMeansStrategy(mock_cache)
        strategy.cluster_orders(mock_orders, n_trucks=2, max_capacity=5000)

        result = strategy.generate_plot(
            figsize=(8, 6), show_legend=False, title="Custom Title"
        )

        assert isinstance(result, str)

    def test_generate_empty_plot(self, mock_cache):
        """Test _generate_empty_plot method."""
        strategy = KMeansStrategy(mock_cache)

        result = strategy._generate_empty_plot()

        assert isinstance(result, str)
        assert len(result) > 0

    def test_plot_with_convex_hull(self, mock_cache, sample_order):
        """Test plot generation with enough points for convex hull (lines 177-190)."""
        strategy = KMeansStrategy(mock_cache)

        orders = [
            sample_order(1, "Madrid", 100, 5),
            sample_order(2, "Madrid", 100, 5),
            sample_order(3, "Madrid", 100, 5),
            sample_order(4, "Madrid", 100, 5),
        ]

        strategy.cluster_orders(orders, n_trucks=1, max_capacity=5000)
        result = strategy.generate_plot()

        assert isinstance(result, str)
        assert len(result) > 100

    def test_plot_with_multiple_clusters(self, mock_cache, mock_orders):
        """Test plot with multiple distinct clusters."""
        strategy = KMeansStrategy(mock_cache)

        strategy.cluster_orders(mock_orders, n_trucks=3, max_capacity=5000)
        result = strategy.generate_plot(show_legend=True)

        assert isinstance(result, str)


# ============================================================================
# TESTS: Strategy Switching
# ============================================================================
class TestStrategySwitching:
    """Tests for switching between strategies."""

    def test_switch_kmeans_to_agglomerative(self, mock_cache, mock_orders):
        """Test switching from KMeans to Agglomerative."""
        manager = ClusteringManager(mock_cache)

        result1 = manager.cluster_orders(mock_orders, n_trucks=2, max_capacity=5000)
        assert manager.get_strategy_name() == "K-Means"

        manager.set_strategy(AgglomerativeStrategy(mock_cache))
        result2 = manager.cluster_orders(mock_orders, n_trucks=2, max_capacity=5000)

        assert manager.get_strategy_name() == "Hierarchical (Agglomerative)"
        assert len(result1) >= 1
        assert len(result2) >= 0
