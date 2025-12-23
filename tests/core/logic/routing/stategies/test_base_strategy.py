import pandas as pd
import pytest

from distribution_platform.core.logic.routing.strategies.base import RoutingStrategy
from distribution_platform.core.models.optimization import (
    LaborRules,
    RouteOptimizationResult,
    SimulationConfig,
)


class ConcreteStrategy(RoutingStrategy):
    def optimize(self, orders, **kwargs):
        return RouteOptimizationResult(
            camion_id=1,
            lista_pedidos_ordenada=[],
            ciudades_ordenadas=[],
            ruta_coordenadas=[],
            distancia_total_km=0,
            tiempo_total_viaje_horas=0,
            tiempo_conduccion_pura_horas=0,
            consumo_litros=0,
            coste_combustible=0,
            coste_conductor=0,
            coste_total_ruta=0,
            ingresos_totales=0,
            beneficio_neto=0,
            valida=True,
            mensaje="Test",
        )


@pytest.fixture
def base_strategy():
    matrix = pd.DataFrame(
        {"Madrid": [0, 100], "Barcelona": [100, 0]}, index=["Madrid", "Barcelona"]
    )
    config = SimulationConfig(
        velocidad_constante=100.0,
        reglas_laborales=LaborRules(
            max_conduccion_seguida=2.0,
            tiempo_descanso_corto=0.5,
            max_conduccion_dia=8.0,
            tiempo_descanso_diario=10.0,
        ),
    )
    return ConcreteStrategy(matrix, config, "Madrid")


class TestBaseStrategy:
    def test_get_distance_safe(self, base_strategy):
        """Busca distancias en la matriz."""
        assert base_strategy._get_distance("Madrid", "Barcelona") == 100.0
        assert base_strategy._get_distance("Madrid", "Mars") == 10000.0

    def test_simulate_schedule_simple(self, base_strategy):
        """Viaje corto sin descansos."""
        elapsed, paid = base_strategy._simulate_schedule(100.0)
        assert paid == 1.0
        assert elapsed == 1.0

    def test_simulate_schedule_with_break(self, base_strategy):
        """Viaje que fuerza un descanso corto."""
        elapsed, paid = base_strategy._simulate_schedule(250.0)

        assert paid == 2.5
        assert elapsed == 3.0

    def test_simulate_schedule_zero_distance(self, base_strategy):
        e, p = base_strategy._simulate_schedule(0)
        assert e == 0
        assert p == 0

    def test_simulate_schedule_infinite_loop_protection(self, base_strategy):
        """Prueba que el bucle while tiene un corte de seguridad."""
        base_strategy.config.velocidad_constante = 0.0001
        elapsed, paid = base_strategy._simulate_schedule(10000.0)
        assert elapsed > 0
