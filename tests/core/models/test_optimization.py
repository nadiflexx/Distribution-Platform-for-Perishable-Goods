from pydantic import ValidationError
import pytest

from distribution_platform.core.models.optimization import (
    LaborRules,
    RouteOptimizationResult,
    SimulationConfig,
)
from distribution_platform.core.models.order import Order


class TestOptimizationModels:
    # --- LaborRules ---

    def test_labor_rules_defaults(self):
        rules = LaborRules()
        assert rules.max_conduccion_seguida == 2.0
        assert rules.tiempo_descanso_diario == 12.0

    def test_labor_rules_custom(self):
        rules = LaborRules(max_conduccion_seguida=4.0)
        assert rules.max_conduccion_seguida == 4.0

    # --- SimulationConfig ---

    def test_simulation_config_defaults(self):
        config = SimulationConfig()
        assert config.velocidad_constante == 90.0
        assert isinstance(config.reglas_laborales, LaborRules)
        assert config.peso_unitario_default == 1.0

    def test_simulation_config_nested(self):
        """Prueba inyección de reglas anidadas."""
        custom_rules = LaborRules(max_conduccion_dia=10.0)
        config = SimulationConfig(
            velocidad_constante=80.0, reglas_laborales=custom_rules
        )
        assert config.reglas_laborales.max_conduccion_dia == 10.0
        assert config.velocidad_constante == 80.0

    # --- RouteOptimizationResult ---

    @pytest.fixture
    def dummy_order(self):
        return Order(
            pedido_id=1,
            fecha_pedido="2023-01-01",
            producto="A",
            cantidad_producto=10,
            precio_venta=100,
            tiempo_fabricacion_medio=1,
            caducidad=10,
            destino="Bcn",
            distancia_km=100,
            email_cliente="a@a.com",
            dias_totales_caducidad=12,
            fecha_caducidad_final="2023-01-13",
        )

    def test_route_result_creation(self, dummy_order):
        """Prueba instanciación completa del resultado."""
        result = RouteOptimizationResult(
            camion_id=1,
            lista_pedidos_ordenada=[dummy_order],
            ciudades_ordenadas=["Mataró", "Bcn"],
            ruta_coordenadas=[(41.0, 2.0)],
            distancia_total_km=150.5,
            tiempo_total_viaje_horas=2.5,
            tiempo_conduccion_pura_horas=2.0,
            consumo_litros=15.0,
            coste_combustible=20.0,
            coste_conductor=30.0,
            coste_total_ruta=50.0,
            ingresos_totales=1000.0,
            beneficio_neto=950.0,
            valida=True,
            mensaje="OK",
        )

        assert result.camion_id == 1
        assert len(result.lista_pedidos_ordenada) == 1
        # Verifica default de tiempos_llegada (list factory)
        assert result.tiempos_llegada == []

    def test_route_result_validation_error(self):
        """Falta de campos requeridos."""
        with pytest.raises(ValidationError):
            RouteOptimizationResult(camion_id=1)  # Faltan muchos campos
