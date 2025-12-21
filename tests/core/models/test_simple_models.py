from pydantic import ValidationError
import pytest

from distribution_platform.core.models.result_validation import ResultValidation
from distribution_platform.core.models.truck import Truck


class TestSimpleModels:
    # --- Truck ---

    def test_truck_creation(self):
        truck = Truck(
            nombre="Volvo",
            velocidad_constante=90.0,
            consumo_combustible=30.0,
            capacidad_carga=1000.0,
            precio_conductor_hora=20.0,
            imagen="volvo.png",
        )
        assert truck.nombre == "Volvo"
        assert truck.capacidad_carga == 1000.0

    def test_truck_types(self):
        """Pydantic intenta convertir tipos (str -> float)."""
        truck = Truck(
            nombre="Volvo",
            velocidad_constante="90",  # String
            consumo_combustible=30,
            capacidad_carga=1000,
            precio_conductor_hora=20,
            imagen="img",
        )
        assert truck.velocidad_constante == 90.0  # Convertido a float

    def test_truck_missing_field(self):
        with pytest.raises(ValidationError):
            Truck(nombre="Volvo")  # Faltan campos

    # --- ResultValidation ---

    def test_result_validation(self):
        res = ResultValidation(is_valid=True, reasoning=["Ok", "Perfect"])
        assert res.is_valid is True
        assert len(res.reasoning) == 2

    def test_result_validation_types(self):
        with pytest.raises(ValidationError):
            ResultValidation(is_valid="not_bool", reasoning="not_list")
