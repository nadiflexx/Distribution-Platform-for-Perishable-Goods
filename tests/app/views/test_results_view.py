from unittest.mock import MagicMock, patch

import pytest

from distribution_platform.app.views.results_view import ResultsView


class FakeOrder:
    """Mock Order object for testing."""

    def __init__(self, pid, dest, qty, email="e@mail.com"):
        self.pedido_id = pid
        self.destino = dest
        self.cantidad_producto = qty
        self.email_cliente = email
        self.precio_venta = 100.0
        self.precio = 100.0
        self.prioridad = "Normal"
        self.fecha_pedido = "2023-01-01"
        self.productos = [{"nombre": "P1", "cantidad": 1, "precio": 10}]
        self.lineas = None
        self.items = None
        self.producto_nombre = "P1"
        self.cantidad = 1
        self.precio_unitario = 10.0


@pytest.fixture
def mock_deps():
    with (
        patch("distribution_platform.app.views.results_view.SessionManager") as sm,
        patch("distribution_platform.app.views.results_view.LoaderOverlay") as loader,
        patch(
            "distribution_platform.app.views.results_view.SpainMapRoutes"
        ) as map_routes,
        patch("distribution_platform.app.views.results_view.st") as st,
        patch(
            "distribution_platform.app.views.results_view.AlgorithmVisualizer"
        ) as algo_viz,
        patch("distribution_platform.app.views.results_view.ExportHub") as export_hub,
        # ELIMINADO: patch("distribution_platform.app.views.results_view.OptimizationService")
    ):
        # Mocking st.columns
        def columns_side_effect(spec, **kwargs):
            if isinstance(spec, (list, tuple)):
                count = len(spec)
            elif isinstance(spec, int):
                count = spec
            else:
                count = 1
            return [MagicMock() for _ in range(count)]

        st.columns.side_effect = columns_side_effect
        st.tabs.side_effect = lambda tabs: [MagicMock() for _ in tabs]

        # Default st return values
        st.text_input.return_value = ""
        st.selectbox.return_value = None
        st.multiselect.return_value = []

        yield sm, loader, map_routes, st, algo_viz, export_hub


@pytest.fixture
def complex_result():
    order = FakeOrder(1, "Madrid", 100)
    truck = MagicMock()
    truck.camion_id = 1
    truck.lista_pedidos_ordenada = [order]
    truck.tiempos_llegada = ["10:00"]
    truck.distancia_total_km = 100.0
    truck.coste_total_ruta = 50.0
    truck.beneficio_neto = 200.0
    truck.valida = True
    truck.ruta_coordenadas = [(0, 0), (1, 1)]

    # Financial fields
    truck.tiempo_total_viaje_horas = 10.0
    truck.tiempo_conduccion_pura_horas = 8.0
    truck.consumo_litros = 30.0
    truck.coste_combustible = 40.0
    truck.coste_conductor = 10.0

    return {
        "num_trucks": 1,
        "total_distancia": 100.0,
        "total_coste": 50.0,
        "total_beneficio": 200.0,
        "total_ingresos": 250.0,
        "routes": [{"color": "red", "camion_id": 1, "pedidos": []}],
        "resultados_detallados": {"t1": truck},
        "assignments": MagicMock(),
        "pedidos_imposibles": MagicMock(empty=False),
        "algorithm_trace": {"truck_1": "trace"},
        "plots": {"clustering": "base64img", "routes": "base64img"},
    }, order


# --- TESTS ---


def test_header_calls_export_hub(mock_deps, complex_result):
    sm, _, _, st, _, export_hub = mock_deps
    result, _ = complex_result

    view = ResultsView()
    view._render_header(result)

    export_hub.render.assert_called_once_with(result)


def test_render_algorithm_tab(mock_deps, complex_result):
    sm, _, _, st, algo_viz, _ = mock_deps
    result, _ = complex_result

    st.selectbox.return_value = "truck_1"

    view = ResultsView()
    view._render_algorithm_tab(result)

    algo_viz.render_graph_animation.assert_called_once()
    assert st.image.call_count >= 2


def test_render_orders_tab_product_extraction_list(mock_deps, complex_result):
    sm, _, _, st, _, _ = mock_deps
    result, order = complex_result

    order.productos = [{"nombre": "A", "cantidad": 2, "precio": 5}]

    st.text_input.return_value = "1"
    st.selectbox.return_value = 1

    sm.get.side_effect = lambda k: result if k == "ia_result" else [[order]]

    view = ResultsView()
    view._render_orders_tab(result)

    assert st.dataframe.call_count >= 1


def test_render_orders_tab_product_extraction_master_map(mock_deps, complex_result):
    sm, _, _, st, _, _ = mock_deps
    result, order = complex_result

    order.productos = None
    order.lineas = None

    original_item = FakeOrder(1, "Madrid", 5)
    original_item.producto_nombre = "MasterProduct"
    original_item.cantidad_producto = 5
    original_item.precio_unitario = 20.0

    sm.get.side_effect = lambda k: result if k == "ia_result" else [[original_item]]

    st.selectbox.return_value = 1

    view = ResultsView()
    view._render_orders_tab(result)

    assert st.columns.call_count > 0


def test_render_route_inspector_tab(mock_deps, complex_result):
    _, _, map_routes, st, _, _ = mock_deps
    result, _ = complex_result

    st.selectbox.return_value = 1

    view = ResultsView()
    view._render_route_inspector_tab(result)

    map_routes.return_value.render.assert_called_once()
    assert st.dataframe.call_count >= 1


def test_render_main_integration(mock_deps, complex_result):
    sm, loader, _, st, _, _ = mock_deps
    result, order = complex_result

    sm.get.side_effect = lambda k: result if k == "ia_result" else [[order]]

    view = ResultsView()
    view.render()

    assert st.tabs.call_count == 1
    loader.persistent_map_loader.assert_called()
