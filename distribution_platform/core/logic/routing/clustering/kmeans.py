"""
K-Means Clustering Strategy.

Uses K-Means algorithm to group orders based on geographical proximity and urgency.
"""

from sklearn.cluster import KMeans

from .base import ClusteringStrategy


class KMeansStrategy(ClusteringStrategy):
    """
    K-Means implementation for order clustering.

    How it works:
        1. Assign K random centroids (one per truck)
        2. Assign each order to the nearest centroid
        3. Recalculate centroids as the average of their orders
        4. Repeat until centroids don't change
    """

    @property
    def name(self) -> str:
        return "K-Means"

    @property
    def description(self) -> str:
        return "Groups orders by assigning them to the nearest centroid (truck)"

    def _perform_clustering(self, scaled_data, n_clusters: int) -> list[int]:
        """
        Execute K-Means clustering algorithm.
        """
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        return kmeans.fit_predict(scaled_data).tolist()
