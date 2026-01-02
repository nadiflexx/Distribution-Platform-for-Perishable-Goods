from dataclasses import dataclass, field

import pandas as pd
import pytest

from distribution_platform.app.services.export_service import ExportService

# --- MOCKS ---


@dataclass
class MockLine:
    """Helper object to simulate Order Lines/Products."""

    producto_nombre: str
    cantidad: float
    precio: float


@dataclass
class MockOrder:
    pedido_id: int
    destino: str
    cantidad_producto: float
    precio_venta: float
    email_cliente: str = "test@test.com"
    prioridad: str = "Alta"
    lineas: list = field(default_factory=list)
    productos: list = field(default_factory=list)
    producto_nombre: str = "Generic Product"


@dataclass
class MockTruck:
    camion_id: int
    lista_pedidos_ordenada: list
    distancia_total_km: float = 100.0
    consumo_litros: float = 30.0
    coste_combustible: float = 50.0
    coste_conductor: float = 20.0
    coste_total_ruta: float = 70.0
    beneficio_neto: float = 30.0
    ruta_coordenadas: list = field(default_factory=lambda: [(40.0, -3.0), (41.0, -3.5)])
    tiempos_llegada: list = field(default_factory=lambda: ["10:00"])


@pytest.fixture
def complex_result():
    o1 = MockOrder(1, "Madrid", 100.0, 200.0)
    o1.lineas = [MockLine(producto_nombre="Item A", cantidad=2.0, precio=50.0)]

    o2 = MockOrder(2, "Barcelona", 50.0, 100.0)

    truck = MockTruck(1, [o1, o2])
    truck.ruta_coordenadas = [(0.0, 0.0), (10.5, 10.5), (20.5, 20.5)]
    truck.tiempos_llegada = ["10:00", "11:00"]

    return {"resultados_detallados": {"t1": truck}, "pedidos_no_entregables": []}


# --- TESTS ---


def test_format_floats():
    """Verify point-to-comma conversion."""
    df = pd.DataFrame({"A": [1.56, 2.0, 0.0], "B": ["Text", "More Text", ""]})
    formatted = ExportService._format_floats(df)

    assert formatted["A"].iloc[0] == "1,56"
    assert formatted["A"].iloc[1] == "2,00"
    assert formatted["B"].iloc[0] == "Text"


def test_generate_financials_df(complex_result):
    df = ExportService.generate_financials_df(complex_result)

    assert len(df) == 1
    assert df["Truck_ID"].iloc[0] == "UNIT-001"
    # Revenue = 200 + 100 = 300
    assert df["Total_Revenue_EUR"].iloc[0] == "300,00"
    assert df["Profit_Margin_Percent"].iloc[0] == "10,00"


def test_generate_detailed_routes_df(complex_result):
    df = ExportService.generate_detailed_routes_df(complex_result)

    assert len(df) == 2  # 2 Orders -> 2 Stops
    assert df["Latitude"].iloc[0] == "10,50"
    assert df["Longitude"].iloc[1] == "20,50"


def test_generate_detailed_routes_missing_coords(complex_result):
    """Test when route coordinates run out."""
    truck = complex_result["resultados_detallados"]["t1"]
    truck.ruta_coordenadas = []  # No coords available

    df = ExportService.generate_detailed_routes_df(complex_result)
    assert df["Latitude"].iloc[0] == "0,00"


def test_generate_failed_orders_df_from_list():
    o_fail = MockOrder(99, "Moon", 10.0, 0.0)
    result = {"pedidos_no_entregables": [o_fail]}

    df = ExportService.generate_failed_orders_df(result)

    assert len(df) == 1
    assert df["Destination"].iloc[0] == "Moon"
    assert df["Reason"].iloc[0] == "Impossible Destination / No Road Access"


def test_generate_failed_orders_df_from_dataframe():
    """Sometimes the engine returns a DF directly."""
    existing_df = pd.DataFrame({"Col1": [1.5]})
    result = {"pedidos_no_entregables": existing_df}

    df = ExportService.generate_failed_orders_df(result)
    assert df["Col1"].iloc[0] == "1,50"


def test_generate_failed_orders_empty():
    result = {}
    df = ExportService.generate_failed_orders_df(result)
    assert df.empty
