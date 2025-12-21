import pandas as pd
import pytest

from distribution_platform.core.logic.routing.strategies.base import RoutingStrategy
from distribution_platform.core.models.optimization import (
    LaborRules,
    RouteOptimizationResult,
    SimulationConfig,
)


# Implementación concreta mínima para testear la clase abstracta
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
        velocidad_constante=100.0,  # 100 km/h para facilitar cálculos
        reglas_laborales=LaborRules(
            max_conduccion_seguida=2.0,  # 2 horas seguidas
            tiempo_descanso_corto=0.5,  # 30 min descanso
            max_conduccion_dia=8.0,
            tiempo_descanso_diario=10.0,
        ),
    )
    return ConcreteStrategy(matrix, config, "Madrid")


class TestBaseStrategy:
    def test_get_distance_safe(self, base_strategy):
        """Busca distancias en la matriz."""
        assert base_strategy._get_distance("Madrid", "Barcelona") == 100.0
        # Caso no existe (penalización)
        assert base_strategy._get_distance("Madrid", "Mars") == 10000.0

    def test_simulate_schedule_simple(self, base_strategy):
        """Viaje corto sin descansos."""
        # 100 km a 100 km/h = 1 hora
        # No llega al límite de 2h seguidas
        elapsed, paid = base_strategy._simulate_schedule(100.0)
        assert paid == 1.0
        assert elapsed == 1.0

    def test_simulate_schedule_with_break(self, base_strategy):
        """Viaje que fuerza un descanso corto."""
        # 250 km a 100 km/h = 2.5 horas conduciendo
        # Regla: Max 2h seguidas -> Descanso 0.5h -> 0.5h conduciendo
        # Total: 2h + 0.5h(descanso) + 0.5h = 3.0 horas
        elapsed, paid = base_strategy._simulate_schedule(250.0)

        assert paid == 2.5  # Solo se paga conducción
        assert elapsed == 3.0  # Tiempo real incluye descanso

    def test_simulate_schedule_zero_distance(self, base_strategy):
        e, p = base_strategy._simulate_schedule(0)
        assert e == 0
        assert p == 0

    def test_simulate_schedule_infinite_loop_protection(self, base_strategy):
        """Prueba que el bucle while tiene un corte de seguridad."""
        # Velocidad absurda para generar infinitos pasos pequeños
        base_strategy.config.velocidad_constante = 0.0001
        # Distancia enorme
        elapsed, paid = base_strategy._simulate_schedule(10000.0)
        # No debería colgarse el test
        assert elapsed > 0
