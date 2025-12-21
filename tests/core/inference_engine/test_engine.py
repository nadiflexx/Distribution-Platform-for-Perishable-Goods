from unittest.mock import Mock

import pytest

from distribution_platform.core.inference_engine.engine import InferenceMotor
from distribution_platform.core.models.truck import Truck


class TestInferenceMotor:
    @pytest.fixture
    def sample_truck(self):
        return Truck(
            nombre="TestTruck",
            velocidad_constante=80.0,
            consumo_combustible=30.0,
            capacidad_carga=1000,
            precio_conductor_hora=20.0,
            imagen="test.png",
        )

    def test_evaluate_all_rules_pass(self, sample_truck):
        """Verifica que si todas las reglas pasan, el resultado es válido."""
        # Reglas que devuelven mensaje de éxito
        rule1 = Mock(return_value="✔ Rule 1 Passed")
        rule2 = Mock(return_value="✔ Rule 2 Passed")

        motor = InferenceMotor([rule1, rule2])
        result = motor.evaluate(sample_truck)

        assert result.is_valid is True
        assert len(result.reasoning) == 2
        assert "✔ Rule 1 Passed" in result.reasoning

        # Verificar que se llamó a las reglas con el camión
        rule1.assert_called_with(sample_truck)

    def test_evaluate_one_rule_fails(self, sample_truck):
        """Verifica que si una regla falla, el resultado es inválido."""
        rule1 = Mock(return_value="✔ Rule 1 Passed")
        rule2 = Mock(return_value="✘ Rule 2 Failed")

        motor = InferenceMotor([rule1, rule2])
        result = motor.evaluate(sample_truck)

        assert result.is_valid is False
        assert len(result.reasoning) == 2
        assert "✘ Rule 2 Failed" in result.reasoning

    def test_empty_rules(self, sample_truck):
        """Verifica comportamiento sin reglas (debería ser válido por defecto)."""
        motor = InferenceMotor([])
        result = motor.evaluate(sample_truck)

        assert result.is_valid is True
        assert result.reasoning == []
