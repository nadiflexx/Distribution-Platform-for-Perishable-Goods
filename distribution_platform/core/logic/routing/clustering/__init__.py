"""
Clustering module.

Provides strategies for grouping orders into truck assignments.

Available strategies:
    - KMeansStrategy: Fast, assumes spherical clusters
    - AgglomerativeStrategy: Finds natural groupings, hierarchical
"""

from .agglomerative import AgglomerativeStrategy
from .base import ClusteringStrategy
from .kmeans import KMeansStrategy
from .manager import ClusteringManager

__all__ = [
    "ClusteringStrategy",
    "KMeansStrategy",
    "AgglomerativeStrategy",
    "ClusteringManager",
]
