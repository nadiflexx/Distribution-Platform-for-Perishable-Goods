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
    """Cubre las líneas 20-49: Getters de reglas."""

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
    """Cubre las validaciones individuales (Líneas 112-276)."""

    # --- NOMBRE ---
    def test_validate_nombre(self):
        # Happy path
        assert "✔" in validate_nombre_format({"nombre": "Volvo FH"})

        # Edge cases (Missing lines coverage)
        assert "✘" in validate_nombre_format({})  # None/Empty
        assert "✘" in validate_nombre_format({"nombre": ""})  # Empty string
        assert "✘" in validate_nombre_format({"nombre": "A"})  # < 3 chars
        assert "✘" in validate_nombre_format({"nombre": "A" * 55})  # > 50 chars
        assert "✘" in validate_nombre_format({"nombre": "Camión@Bad"})  # Regex fail

    # --- CAPACIDAD ---
    def test_validate_capacidad(self):
        # Happy path (int & str)
        assert "✔" in validate_capacidad_format({"capacidad": 100})
        assert "✔" in validate_capacidad_format({"capacidad": "100"})

        # Edge cases
        assert "✘" in validate_capacidad_format({})  # Missing
        assert "✘" in validate_capacidad_format({"capacidad": "texto"})  # ValueError
        assert "✘" in validate_capacidad_format({"capacidad": 5})  # < 10
        assert "✘" in validate_capacidad_format({"capacidad": 250})  # > 200

    # --- CONSUMO ---
    def test_validate_consumo(self):
        # Happy path
        assert "✔" in validate_consumo_format({"consumo": 30.5})
        assert "✔" in validate_consumo_format({"consumo": "30.5"})

        # Edge cases
        assert "✘" in validate_consumo_format({})  # Missing
        assert "✘" in validate_consumo_format({"consumo": "litros"})  # ValueError
        assert "✘" in validate_consumo_format({"consumo": 5})  # < 10
        assert "✘" in validate_consumo_format({"consumo": 60})  # > 50

    # --- VELOCIDAD ---
    def test_validate_velocidad(self):
        # Happy path
        assert "✔" in validate_velocidad_format({"velocidad_constante": 90})

        # Edge cases
        assert "✘" in validate_velocidad_format({})  # Missing
        assert "✘" in validate_velocidad_format(
            {"velocidad_constante": "rápido"}
        )  # ValueError
        assert "✘" in validate_velocidad_format({"velocidad_constante": 20})  # < 30
        assert "✘" in validate_velocidad_format({"velocidad_constante": 130})  # > 120

    # --- PRECIO CONDUCTOR ---
    def test_validate_precio(self):
        # Happy path
        assert "✔" in validate_precio_conductor_hora_format(
            {"precio_conductor_hora": 25}
        )

        # Edge cases
        assert "✘" in validate_precio_conductor_hora_format({})  # Missing
        assert "✘" in validate_precio_conductor_hora_format(
            {"precio_conductor_hora": "caro"}
        )  # ValueError
        assert "✘" in validate_precio_conductor_hora_format(
            {"precio_conductor_hora": 5}
        )  # < 10
        assert "✘" in validate_precio_conductor_hora_format(
            {"precio_conductor_hora": 60}
        )  # > 50


class TestParseTruckData:
    """Cubre parse_truck_data (Líneas 292-313)."""

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
        Cubre el bloque 'except Exception as e' (Líneas 310-313).
        Enviamos un dato que pasa como string pero falla al convertir a float/int
        dentro de la función.
        """
        data = {
            "nombre": "Bad Truck",
            # Esto causará ValueError en: int(float(data.get("capacidad")))
            "capacidad": "no_es_numero",
        }

        valid, result = parse_truck_data(data)

        assert valid is False
        assert isinstance(result, dict)
        assert "error" in result
        # Verificamos que el mensaje de error sea el esperado
        assert "could not convert" in result["error"].lower()
