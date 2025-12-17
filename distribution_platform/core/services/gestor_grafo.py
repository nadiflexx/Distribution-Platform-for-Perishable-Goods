"""
Gestor de grafos para cálculo de distancias entre ciudades.

Este módulo utiliza el sistema de caché de coordenadas existente
en distribution_platform para obtener coordenadas GPS y calcular
distancias usando la fórmula de Haversine.
"""

import math

import pandas as pd

from distribution_platform.utils.coordinates_cache import CoordinateCache


class GestorGrafo:
    """Gestor de grafos para calcular distancias entre destinos."""

    def __init__(self, coord_cache: CoordinateCache | None = None):
        """
        Inicializa el gestor de grafos.

        Parameters
        ----------
        coord_cache : CoordinateCache, optional
            Cache de coordenadas. Si no se proporciona, se crea uno nuevo.
        """
        self.coord_cache = coord_cache if coord_cache else CoordinateCache()
        self.coords: dict[str, tuple[float, float]] = {}
        self._cargar_coordenadas()

    def _cargar_coordenadas(self):
        """Carga coordenadas desde el cache en formato (lat, lon)."""
        for ciudad, coord_str in self.coord_cache.cache.items():
            if coord_str is None:
                continue
            try:
                lat_str, lon_str = coord_str.split(",")
                self.coords[ciudad] = (float(lat_str), float(lon_str))
            except (ValueError, AttributeError):
                print(f"⚠️ Formato incorrecto para {ciudad}: {coord_str}")

    def obtener_coordenadas(self, ciudad: str) -> tuple[float | None, float | None]:
        """
        Obtiene coordenadas de una ciudad.

        Parameters
        ----------
        ciudad : str
            Nombre de la ciudad.

        Returns
        -------
        tuple[float | None, float | None]
            Tupla (lat, lon) o (None, None) si no existe.
        """
        return self.coords.get(ciudad, (None, None))

    def _calcular_haversine(
        self, lat1: float, lon1: float, lat2: float, lon2: float
    ) -> float:
        """
        Calcula distancia entre dos puntos usando fórmula de Haversine.

        Parameters
        ----------
        lat1, lon1 : float
            Latitud y longitud del primer punto.
        lat2, lon2 : float
            Latitud y longitud del segundo punto.

        Returns
        -------
        float
            Distancia en kilómetros.
        """
        R = 6371  # Radio tierra km
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

    def generar_matriz_distancias(self) -> pd.DataFrame:
        """
        Crea la matriz de distancias entre todas las ciudades cargadas.

        Returns
        -------
        pd.DataFrame
            Matriz de distancias con ciudades como índice y columnas.
        """
        ciudades = list(self.coords.keys())
        matriz = pd.DataFrame(index=ciudades, columns=ciudades, dtype=float)

        for origen in ciudades:
            for destino in ciudades:
                if origen == destino:
                    matriz.at[origen, destino] = 0.0
                else:
                    lat1, lon1 = self.coords[origen]
                    lat2, lon2 = self.coords[destino]
                    dist = self._calcular_haversine(lat1, lon1, lat2, lon2)
                    matriz.at[origen, destino] = dist
        return matriz
