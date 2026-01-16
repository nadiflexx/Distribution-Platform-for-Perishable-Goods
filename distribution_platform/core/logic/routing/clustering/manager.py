"""
Clustering Manager.

Facade that uses a ClusteringStrategy to group orders.
Provides backward compatibility with the original interface.
"""

from distribution_platform.core.models.order import Order
from distribution_platform.infrastructure.persistence.coordinates import (
    CoordinateCache,
)

from .base import ClusteringStrategy
from .kmeans import KMeansStrategy


class ClusteringManager:
    """
    Manager for Order Clustering.

    Acts as a facade, delegating to the selected clustering strategy.
    """

    def __init__(
        self, coord_cache: CoordinateCache, strategy: ClusteringStrategy | None = None
    ):
        self.coord_cache = coord_cache
        # Default strategy: K-Means (backward compatible)
        self.strategy = strategy or KMeansStrategy(coord_cache)

    def set_strategy(self, strategy: ClusteringStrategy) -> None:
        """Change the clustering strategy at runtime."""
        self.strategy = strategy

    def get_strategy_name(self) -> str:
        """Returns current strategy name for UI display."""
        return self.strategy.name

    def get_strategy_description(self) -> str:
        """Returns current strategy description for UI display."""
        return self.strategy.description

    def cluster_orders(
        self,
        orders: list[Order],
        n_trucks: int,
        unit_weight: float = 1.0,
        max_capacity: float = 1000.0,
    ) -> dict[int, list[Order]]:
        """
        Groups orders into clusters using the selected strategy.
        """

        result = self.strategy.cluster_orders(
            orders=orders,
            n_trucks=n_trucks,
            unit_weight=unit_weight,
            max_capacity=max_capacity,
        )
        return result

    def generate_plot(
        self,
        figsize: tuple[int, int] = (12, 8),
        show_legend: bool = True,
        title: str | None = None,
    ) -> str:
        """
        Generates visualization of the last clustering result.

        Returns:
            Base64 encoded PNG image string.

        Usage in HTML:
            <img src="data:image/png;base64,{returned_string}" />
        """
        return self.strategy.generate_plot(
            figsize=figsize, show_legend=show_legend, title=title
        )
