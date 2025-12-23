from unittest.mock import MagicMock

import pandas as pd
import pytest

from distribution_platform.core.logic.graph import GraphManager


@pytest.fixture
def mock_cache():
    cache = MagicMock()
    cache.cache = {
        "A": "0,0",
        "B": "0,1",
        "C": "bad_data",
    }
    return cache


class TestGraphManager:
    def test_load_coords(self, mock_cache):
        graph = GraphManager(mock_cache)
        assert "A" in graph.coords
        assert graph.coords["A"] == (0.0, 0.0)
        assert "C" not in graph.coords

    def test_haversine(self, mock_cache):
        graph = GraphManager(mock_cache)
        graph._haversine(0, 0, 0, 1)

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
