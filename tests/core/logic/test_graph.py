from unittest.mock import MagicMock

import pandas as pd
import pytest

from distribution_platform.core.logic.graph import GraphManager


@pytest.fixture
def mock_cache():
    cache = MagicMock()
    # Cache devuelve strings "lat,lon"
    cache.cache = {
        "A": "0,0",
        "B": "0,1",  # 1 grado lon diferencia en ecuador ~111km
        "C": "bad_data",  # Debe ignorarlo
    }
    return cache


class TestGraphManager:
    def test_load_coords(self, mock_cache):
        graph = GraphManager(mock_cache)
        assert "A" in graph.coords
        assert graph.coords["A"] == (0.0, 0.0)
        assert "C" not in graph.coords  # Ignorado por error

    def test_haversine(self, mock_cache):
        graph = GraphManager(mock_cache)
        # Distancia entre (0,0) y (0,1) grados ~ 111 km
        graph._haversine(
            0, 0, 0, 1
        )  # lat1, lon1, lat2, lon2 (radianes no, la func convierte)
        # En la implementación la función recibe grados y convierte a radianes dentro.
        # Pero ojo: math.radians(1) es pequeño.
        # Vamos a probar con valores conocidos: Madrid -> Barcelona ~500km

        # Lat/Lon Aprox
        mad = (40.41, -3.7)
        bcn = (41.38, 2.17)
        dist_real = graph._haversine(mad[0], mad[1], bcn[0], bcn[1])
        assert 450 < dist_real < 550

    def test_generate_distance_matrix(self, mock_cache):
        graph = GraphManager(mock_cache)
        matrix = graph.generate_distance_matrix()

        assert isinstance(matrix, pd.DataFrame)
        assert "A" in matrix.index
        assert "B" in matrix.columns
        assert matrix.at["A", "A"] == 0.0
        assert matrix.at["A", "B"] > 0.0
