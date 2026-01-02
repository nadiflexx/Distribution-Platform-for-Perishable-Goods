from distribution_platform.core.knowledge_base.rules import (
    obtain_format_validation_rules,
    obtain_rules,
    parse_truck_data,
    print_rules,
    validate_capacidad_format,
    validate_consumo_format,
    validate_nombre_format,
    validate_precio_conductor_hora_format,
    validate_velocidad_format,
)
from distribution_platform.core.models.truck import Truck


class TestHelperFunctions:
    """Covers lines 20-49: Rule getters."""

    def test_print_rules(self):
        rules = print_rules()
        assert isinstance(rules, list)
        assert len(rules) > 0
        assert isinstance(rules[0], str)

    def test_obtain_rules(self):
        rules = obtain_rules()
        assert isinstance(rules, list)
        assert len(rules) > 0
        assert callable(rules[0])

    def test_obtain_format_validation_rules(self):
        rules = obtain_format_validation_rules()
        assert isinstance(rules, list)
        assert len(rules) > 0
        assert callable(rules[0])


class TestFormatValidators:
    """Covers the individual validations (Lines 112-276)."""

    def test_validate_nombre(self):
        assert "[SUCCESS]" in validate_nombre_format({"nombre": "Volvo FH"})

        assert "[ERROR]" in validate_nombre_format({})
        assert "[ERROR]" in validate_nombre_format({"nombre": ""})
        assert "[ERROR]" in validate_nombre_format({"nombre": "A"})
        assert "[ERROR]" in validate_nombre_format({"nombre": "A" * 55})
        assert "[ERROR]" in validate_nombre_format({"nombre": "Camión@Bad"})

    def test_validate_capacidad(self):
        assert "[SUCCESS]" in validate_capacidad_format({"capacidad": 100})
        assert "[SUCCESS]" in validate_capacidad_format({"capacidad": "100"})

        assert "[ERROR]" in validate_capacidad_format({})
        assert "[ERROR]" in validate_capacidad_format({"capacidad": "texto"})
        assert "[ERROR]" in validate_capacidad_format({"capacidad": 5})
        assert "[ERROR]" in validate_capacidad_format({"capacidad": 250})

    def test_validate_consumo(self):
        assert "[SUCCESS]" in validate_consumo_format({"consumo": 30.5})
        assert "[SUCCESS]" in validate_consumo_format({"consumo": "30.5"})
        assert "[ERROR]" in validate_consumo_format({})
        assert "[ERROR]" in validate_consumo_format({"consumo": "litros"})
        assert "[ERROR]" in validate_consumo_format({"consumo": 5})
        assert "[ERROR]" in validate_consumo_format({"consumo": 60})

    def test_validate_velocidad(self):
        assert "[SUCCESS]" in validate_velocidad_format({"velocidad_constante": 90})

        assert "[ERROR]" in validate_velocidad_format({})
        assert "[ERROR]" in validate_velocidad_format(
            {"velocidad_constante": "rápido"}
        )  # ValueError
        assert "[ERROR]" in validate_velocidad_format({"velocidad_constante": 20})
        assert "[ERROR]" in validate_velocidad_format({"velocidad_constante": 130})

    def test_validate_precio(self):
        assert "[SUCCESS]" in validate_precio_conductor_hora_format(
            {"precio_conductor_hora": 25}
        )

        # Ede cases
        assert "[ERROR]" in validate_precio_conductor_hora_format({})
        assert "[ERROR]" in validate_precio_conductor_hora_format(
            {"precio_conductor_hora": "caro"}
        )  # ValueError
        assert "[ERROR]" in validate_precio_conductor_hora_format(
            {"precio_conductor_hora": 5}
        )  # < 10
        assert "[ERROR]" in validate_precio_conductor_hora_format(
            {"precio_conductor_hora": 60}
        )  # > 50


class TestParseTruckData:
    """Covers parse_truck_data (LLines 292-313)."""

    def test_parse_success(self):
        """Prueba la conversión exitosa a objeto Truck."""
        data = {
            "nombre": "Test Truck",
            "capacidad": "100",
            "consumo": "30",
            "velocidad_constante": "90",
            "precio_conductor_hora": "20",
            "imagen": "test.png",
        }
        valid, result = parse_truck_data(data)

        assert valid is True
        assert isinstance(result, Truck)
        assert result.capacidad_carga == 100
        assert result.velocidad_constante == 90.0

    def test_parse_exception(self):
        """
        Covers the 'except Exception as e' block (Lines 310-313).
        We send a data that passes as string but fails to convert to float/int
        inside the function.
        """
        data = {
            "nombre": "Bad Truck",
            "capacidad": "no_es_numero",
        }

        valid, result = parse_truck_data(data)

        assert valid is False
        assert isinstance(result, dict)
        assert "error" in result
        assert "could not convert" in result["error"].lower()
