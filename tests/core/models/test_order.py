from datetime import date

from pydantic import ValidationError
import pytest

from distribution_platform.core.models.order import Order


class TestOrderModel:
    @pytest.fixture
    def valid_order_data(self):
        return {
            "pedido_id": 1,
            "fecha_pedido": "2023-10-01",
            "producto": "Manzanas",
            "cantidad_producto": 100,
            "precio_venta": "10,50",  # Test comma
            "tiempo_fabricacion_medio": 2,
            "caducidad": 10,
            "destino": "Madrid",
            "distancia_km": 500.5,
            "email_cliente": "test@example.com",
            "dias_totales_caducidad": 13,
            "fecha_caducidad_final": "2023-10-14",
        }

    def test_create_valid_order(self, valid_order_data):
        """Prueba creación exitosa y conversión de tipos."""
        order = Order(**valid_order_data)

        # Validadores
        assert order.precio_venta == 10.50
        assert isinstance(order.fecha_pedido, date)
        assert order.fecha_pedido.year == 2023
        assert isinstance(order.fecha_caducidad_final, date)

    def test_decimal_conversion(self, valid_order_data):
        """Prueba conversiones de float/string con comas y puntos."""
        # Case 1: Float directo
        valid_order_data["precio_venta"] = 20.0
        order = Order(**valid_order_data)
        assert order.precio_venta == 20.0

        # Case 2: String con punto
        valid_order_data["precio_venta"] = "30.5"
        order = Order(**valid_order_data)
        assert order.precio_venta == 30.5

        # Case 3: String con coma
        valid_order_data["precio_venta"] = "40,5"
        order = Order(**valid_order_data)
        assert order.precio_venta == 40.5

    def test_date_validator_formats(self, valid_order_data):
        """Prueba distintos formatos de fecha."""
        # Case 1: Date Object
        valid_order_data["fecha_pedido"] = date(2023, 12, 25)
        order = Order(**valid_order_data)
        assert order.fecha_pedido == date(2023, 12, 25)

        # Case 2: Invalid String Format
        valid_order_data["fecha_pedido"] = (
            "01-10-2023"  # DD-MM-YYYY (Incorrecto para el validador)
        )
        with pytest.raises(ValidationError) as exc:
            Order(**valid_order_data)
        assert "Date must be in YYYY-MM-DD format" in str(exc.value)

    def test_email_validation(self, valid_order_data):
        """Prueba validación de email nativa de Pydantic."""
        valid_order_data["email_cliente"] = "bad-email"
        with pytest.raises(ValidationError):
            Order(**valid_order_data)

    def test_fecha_caducidad_final_validator(self, valid_order_data):
        """Prueba validador específico de fecha caducidad."""
        # Case: Date object input
        valid_order_data["fecha_caducidad_final"] = date(2024, 1, 1)
        order = Order(**valid_order_data)
        assert order.fecha_caducidad_final == date(2024, 1, 1)
