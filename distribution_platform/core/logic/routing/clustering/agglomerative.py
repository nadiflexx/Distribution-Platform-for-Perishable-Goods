"""
Agglomerative (Hierarchical) Clustering Strategy.

Uses bottom-up hierarchical clustering to group orders.
"""

from sklearn.cluster import AgglomerativeClustering

from .base import ClusteringStrategy


class AgglomerativeStrategy(ClusteringStrategy):
    """
    Agglomerative Hierarchical Clustering implementation.

    How it works:
        1. Starts with each order as its own group
        2. Finds the two closest groups and merges them
        3. Repeats until the desired number of groups (trucks) is reached
    """

    @property
    def name(self) -> str:
        return "Hierarchical (Agglomerative)"

    @property
    def description(self) -> str:
        return "Progressively merges nearby orders to form groups"

    def _perform_clustering(self, scaled_data, n_clusters: int) -> list[int]:
        """
        Execute Agglomerative clustering algorithm.

        The linkage='ward' parameter minimizes the variance within each cluster,
        producing compact and balanced groups.
        """
        clustering = AgglomerativeClustering(
            n_clusters=n_clusters,
            linkage="ward",  # Minimiza varianza intra-cluster
        )
        return clustering.fit_predict(scaled_data).tolist()
