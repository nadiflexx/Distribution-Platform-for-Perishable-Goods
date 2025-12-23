from unittest.mock import patch

import pandas as pd
import pytest

from distribution_platform.app.services.optimization_service import OptimizationService

# --- Helpers to create fake objects ---


class FakeOrder:
    def __init__(self, pid, dest, qty):
        self.pedido_id = pid
        self.destino = dest
        self.cantidad_producto = qty


class FakeTruckResult:
    def __init__(self, cid, dist, cost, profit, orders):
        self.camion_id = cid
        self.distancia_total_km = dist
        self.coste_total_ruta = cost
        self.beneficio_neto = profit
        self.lista_pedidos_ordenada = orders
        self.ruta_coordenadas = [(0, 0), (1, 1)] * len(orders)
        self.tiempos_llegada = ["10:00"] * len(orders)


@pytest.fixture
def mock_deps():
    with (
        patch(
            "distribution_platform.app.services.optimization_service.SessionManager"
        ) as sm,
        patch(
            "distribution_platform.app.services.optimization_service.OptimizationOrchestrator"
        ) as orch,
        patch("streamlit.error") as err,
    ):
        yield sm, orch, err


def test_run_missing_data(mock_deps):
    sm, _, _ = mock_deps
    sm.get.return_value = None  # Missing either truck or orders
    assert OptimizationService.run() is None


def test_run_capacity_error(mock_deps):
    sm, _, err = mock_deps

    # Truck: small capacity
    sm.get.side_effect = lambda k, default=None: {
        "selected_truck_data": {"capacidad": 10},  # 10 kg
        "df": [[FakeOrder(1, "A", 100)]],  # 100 kg load
    }.get(k, default)

    assert OptimizationService.run() is None
    err.assert_called_once()
    assert "CAPACITY ERROR" in err.call_args[0][0]


def test_run_success_genetic(mock_deps):
    sm, orch, _ = mock_deps

    # Setup Data
    truck_data = {
        "capacidad": 1000,
        "velocidad_constante": 90,
        "consumo": 30,
        "precio_conductor_hora": 20,
    }
    orders = [[FakeOrder(1, "A", 10), FakeOrder(2, "B", 20)]]

    def get_side_effect(k, default=None):
        if k == "selected_truck_data":
            return truck_data
        if k == "df":
            return orders
        if k == "algo_select":
            return "Genetic"
        return default

    sm.get.side_effect = get_side_effect

    # Setup Orchestrator Result
    fake_res = FakeTruckResult(1, 100.0, 50.0, 200.0, orders[0])
    raw_results = {"truck_1": fake_res, "pedidos_no_entregables": pd.DataFrame()}
    orch.return_value.optimize_deliveries.return_value = raw_results

    # Execution
    result = OptimizationService.run()

    # Assertions
    assert result is not None
    assert result["num_trucks"] == 1
    assert result["total_distancia"] == 100.0
    assert "algorithm_trace" in result

    # Check trace structure for Genetic
    trace = result["algorithm_trace"]["truck_1"]
    assert trace.algorithm_name == "Genetic Algorithm"
    assert len(trace.snapshots) > 0
    assert trace.total_iterations == 11  # As per logic in _simulate_genetic_trace


def test_run_success_ortools(mock_deps):
    sm, orch, _ = mock_deps

    # Setup Data (Tons heuristic check: cap < 100)
    truck_data = {"capacidad": 24}  # 24 Tons -> should convert to 24000
    orders = []
    # Create enough orders to trigger > 10000 load
    for i in range(101):
        orders.append(FakeOrder(i, "Dest", 100))  # 101 * 100 = 10100 kg

    def get_side_effect(k, default=None):
        if k == "selected_truck_data":
            return truck_data
        if k == "df":
            return [orders]  # List of lists
        if k == "algo_select":
            return "OR-Tools"
        return default

    sm.get.side_effect = get_side_effect

    fake_res = FakeTruckResult(1, 100.0, 50.0, 200.0, orders[:2])
    raw_results = {
        "truck_1": fake_res,
        "pedidos_no_entregables": None,  # Should be handled gracefully
    }
    orch.return_value.optimize_deliveries.return_value = raw_results

    result = OptimizationService.run()

    assert result is not None
    trace = result["algorithm_trace"]["truck_1"]
    assert trace.algorithm_name == "Google OR-Tools (Constraint Programming)"
    assert trace.total_iterations == 7  # As per logic in _simulate_ortools_trace


def test_exception_handling(mock_deps):
    sm, _, err = mock_deps
    sm.get.side_effect = Exception("Surprise!")

    result = OptimizationService.run()
    assert result is None
    err.assert_called_once()


def test_trace_edge_cases():
    # Test generation with no orders
    res = FakeTruckResult(1, 0, 0, 0, [])
    # _simulate_trace will return empty trace if nodes only contain origin
    # But nodes construction depends on orders
    # We call internal method to test robustness

    from distribution_platform.app.services.optimization_service import (
        OptimizationService,
    )

    trace_gen = OptimizationService._simulate_genetic_trace([{"id": "origin"}], [], res)
    assert len(trace_gen.snapshots) == 0

    trace_or = OptimizationService._simulate_ortools_trace([{"id": "origin"}], [], res)
    assert len(trace_or.snapshots) == 0
