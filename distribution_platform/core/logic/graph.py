"""
Graph Logic.
Handles distance matrix calculations.
"""

import contextlib
import math

import pandas as pd

from distribution_platform.infrastructure.persistence.coordinates import (
    CoordinateCache,
)


class GraphManager:
    """
    Manager for Geographical Graph calculations.
    (Formerly GestorGrafo)
    """

    def __init__(self, coord_cache: CoordinateCache):
        self.coord_cache = coord_cache
        self.coords: dict[str, tuple[float, float]] = {}
        self._load_coords()

    def _load_coords(self):
        """Loads coordinates into memory map."""
        for city, c_str in self.coord_cache.cache.items():
            if c_str:
                with contextlib.suppress(ValueError):
                    self.coords[city] = tuple(map(float, c_str.split(",")))

    def get_coords(self, city: str) -> tuple[float | None, float | None]:
        """Returns (lat, lon) or (None, None)."""
        # Alias for obtaining coordinates (for compatibility/ease of use)
        return self.coords.get(city, (None, None))

    # Alias para mantener compatibilidad si lo necesitas en GeneticStrategy
    def obtener_coordenadas(self, city: str):
        return self.get_coords(city)

    def _haversine(self, lat1, lon1, lat2, lon2):
        R = 6371  # km
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = (
            math.sin(dlat / 2) ** 2
            + math.cos(math.radians(lat1))
            * math.cos(math.radians(lat2))
            * math.sin(dlon / 2) ** 2
        )
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return R * c

    def generate_distance_matrix(self) -> pd.DataFrame:
        """
        Creates the NxN distance matrix for all cached cities.
        """
        self._load_coords()  # Refresh in case of updates
        cities = list(self.coords.keys())
        matrix = pd.DataFrame(index=cities, columns=cities, dtype=float)

        for o in cities:
            for d in cities:
                if o == d:
                    matrix.at[o, d] = 0.0
                else:
                    l1 = self.coords[o]
                    l2 = self.coords[d]
                    matrix.at[o, d] = self._haversine(l1[0], l1[1], l2[0], l2[1])
        return matrix
