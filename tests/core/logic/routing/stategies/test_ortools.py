from unittest.mock import MagicMock, patch

import pytest

from distribution_platform.core.logic.routing.strategies.ortools import ORToolsStrategy
from distribution_platform.core.models.optimization import SimulationConfig
from distribution_platform.core.models.order import Order


@pytest.fixture
def mock_orders():
    return [
        Order(
            pedido_id=1,
            destino="A",
            precio_venta=10,
            cantidad_producto=1,
            caducidad=10,
            fecha_pedido="2023-01-01",
            producto="P",
            tiempo_fabricacion_medio=1,
            distancia_km=10,
            email_cliente="valid@email.com",
            dias_totales_caducidad=10,
            fecha_caducidad_final="2023-01-10",
        )
    ]


class TestORToolsStrategy:
    @patch("distribution_platform.core.logic.routing.strategies.ortools.pywrapcp")
    def test_optimize_success(self, mock_pywrapcp, mock_orders):
        strat = ORToolsStrategy(MagicMock(), SimulationConfig(), "Origin")
        strat._get_distance = lambda x, y: 10.0

        routing = mock_pywrapcp.RoutingModel.return_value
        manager = mock_pywrapcp.RoutingIndexManager.return_value

        solution = MagicMock()
        routing.SolveWithParameters.return_value = solution

        routing.Start.return_value = 0
        routing.IsEnd.side_effect = [False, True]
        solution.Value.return_value = 1
        manager.IndexToNode.side_effect = lambda x: x

        result = strat.optimize(mock_orders)

        assert result is not None
        assert len(result.lista_pedidos_ordenada) == 1
        assert result.valida is True

    @patch("distribution_platform.core.logic.routing.strategies.ortools.pywrapcp")
    def test_optimize_no_solution(self, mock_pywrapcp, mock_orders):
        strat = ORToolsStrategy(MagicMock(), SimulationConfig(), "Origin")
        mock_pywrapcp.RoutingModel.return_value.SolveWithParameters.return_value = None

        result = strat.optimize(mock_orders)
        assert result is None

    def test_optimize_exception(self, mock_orders):
        """Prueba que captura excepciones críticas (bloque try-except)."""
        strat = ORToolsStrategy(MagicMock(), SimulationConfig(), "Origin")
        with patch(
            "distribution_platform.core.logic.routing.strategies.ortools.pywrapcp"
        ) as mock_lib:
            mock_lib.RoutingIndexManager.side_effect = Exception("Critical Crash")

            result = strat.optimize(mock_orders)
            assert result is None

    def test_build_result_ortools(self, mock_orders):
        strat = ORToolsStrategy(MagicMock(), SimulationConfig(), "Origin")
        strat._get_distance = lambda x, y: 100.0
        strat._simulate_schedule = lambda x: (1.0, 1.0)

        result = strat._build_result_ortools(mock_orders)

        assert result.distancia_total_km == 200.0
        assert result.camion_id == 0
        assert len(result.tiempos_llegada) == 1
