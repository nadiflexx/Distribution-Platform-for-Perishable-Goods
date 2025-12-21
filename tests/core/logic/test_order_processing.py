import pytest

from distribution_platform.core.logic.order_processing import consolidate_orders
from distribution_platform.core.models.order import Order


@pytest.fixture
def order_factory():
    def _create(pid, qty, cad):
        return Order(
            pedido_id=pid,
            cantidad_producto=qty,
            caducidad=cad,
            precio_venta=10,
            tiempo_fabricacion_medio=1,
            fecha_pedido="2023-01-01",
            producto="P",
            destino="D",
            distancia_km=10,
            email_cliente="a@a.com",
            dias_totales_caducidad=cad + 2,
            fecha_caducidad_final="2023-01-10",
        )

    return _create


class TestOrderProcessing:
    def test_consolidate_logic(self, order_factory):
        # Grupo 1: ID 1, dos líneas (10 ud, 20 ud)
        group1 = [
            order_factory(1, 10, 10),
            order_factory(1, 20, 5),  # Caducidad menor (5) manda
        ]

        # Grupo 2: ID 2, una línea
        group2 = [order_factory(2, 5, 20)]

        res = consolidate_orders([group1, group2])

        assert len(res) == 2

        # Verificar consolidación grupo 1
        o1 = res[0]
        assert o1.pedido_id == 1
        assert o1.cantidad_producto == 30  # Suma
        assert o1.caducidad == 5  # Mínimo
        assert "Consolidado" in o1.producto

    def test_consolidate_empty(self):
        assert consolidate_orders([]) == []
        assert consolidate_orders([[]]) == []  # Lista con grupo vacío
