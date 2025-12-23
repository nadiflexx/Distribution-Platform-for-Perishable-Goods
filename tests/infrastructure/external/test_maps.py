from unittest.mock import MagicMock, patch

from distribution_platform.infrastructure.external.maps import SpainMapRoutes


class TestSpainMapRoutes:
    @patch("requests.get")
    def test_get_osrm_route_success(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "routes": [{"geometry": {"coordinates": [[2.1, 41.3], [2.2, 41.4]]}}]
        }
        mock_get.return_value = mock_response

        mapper = SpainMapRoutes()
        route = mapper.get_osrm_route([41.3, 2.1], [41.4, 2.2])
        assert route == [[41.3, 2.1], [41.4, 2.2]]

    @patch("requests.get")
    def test_get_osrm_route_failure(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_get.return_value = mock_response

        mapper = SpainMapRoutes()
        route = mapper.get_osrm_route([41.3, 2.1], [41.4, 2.2])
        assert route is None

    @patch("distribution_platform.infrastructure.external.maps.st")
    @patch("distribution_platform.infrastructure.external.maps.st_folium")
    @patch("distribution_platform.infrastructure.external.maps.folium.Map")
    @patch.object(SpainMapRoutes, "get_osrm_route")
    def test_render_logic(
        self, mock_get_route, mock_folium_map, mock_st_folium, mock_st
    ):
        mock_st.session_state = {}
        test_routes = [
            {
                "path": [[40, -3], [41, -3]],
                "color": "red",
                "camion_id": 1,
                "pedidos": [],
            }
        ]
        mock_get_route.return_value = [[40, -3], [40.5, -3], [41, -3]]

        mapper = SpainMapRoutes()
        mapper.render(test_routes)

        mock_st_folium.assert_called_once()
        keys = [k for k in mock_st.session_state if k.startswith("map_")]
        assert len(keys) == 1

    @patch("distribution_platform.infrastructure.external.maps.st")
    @patch("distribution_platform.infrastructure.external.maps.st_folium")
    def test_render_cached(self, mock_st_folium, mock_st):
        routes = []
        mock_st.session_state = {"empty_map": "CACHED_MAP_OBJECT"}

        mapper = SpainMapRoutes()
        mapper.render(routes)

        mock_st_folium.assert_called_with(
            "CACHED_MAP_OBJECT", width=None, height=520, returned_objects=[]
        )

    @patch("distribution_platform.infrastructure.external.maps.folium.Map")
    @patch("distribution_platform.infrastructure.external.maps.folium.PolyLine")
    @patch("distribution_platform.infrastructure.external.maps.folium.Marker")
    @patch("distribution_platform.infrastructure.external.maps.st_folium")
    def test_render_elements(self, mock_st, mock_marker, mock_poly, mock_map):
        mapper = SpainMapRoutes()

        p1 = MagicMock()
        p1.dias_totales_caducidad = 10
        p1.caducidad = 10
        p1.pedido_id = 1
        p1.destino = "A"
        p1.cantidad_producto = 10.0

        routes = [
            {
                "path": [[0, 0], [1, 1]],
                "color": "red",
                "camion_id": 1,
                "pedidos": [p1],
                "tiempos_llegada": [1.0],
            }
        ]

        with patch.object(
            mapper, "get_osrm_route", return_value=[[0, 0], [0.5, 0.5], [1, 1]]
        ):
            mapper.render(routes)
            mock_poly.assert_called()
            assert mock_marker.call_count >= 2

    @patch("distribution_platform.infrastructure.external.maps.folium.Marker")
    @patch("distribution_platform.infrastructure.external.maps.folium.Popup")
    @patch("distribution_platform.infrastructure.external.maps.folium.PolyLine")
    @patch("distribution_platform.infrastructure.external.maps.st_folium")
    def test_map_popups_logic(self, mock_st, mock_poly, mock_popup, mock_marker):
        mapper = SpainMapRoutes()

        p1 = MagicMock(pedido_id=1, destino="A", cantidad_producto=10.0)
        p1.caducidad = 10
        p1.dias_totales_caducidad = 10

        p2 = MagicMock(pedido_id=2, destino="B", cantidad_producto=10.0)
        p2.caducidad = 1
        p2.dias_totales_caducidad = 1

        p3 = MagicMock(pedido_id=3, destino="C", cantidad_producto=10.0)
        p3.caducidad = 5
        p3.dias_totales_caducidad = 5

        routes = [
            {
                "path": [[0, 0], [1, 1], [2, 2], [3, 3]],
                "color": "red",
                "camion_id": 1,
                "pedidos": [p1, p2, p3],
                "tiempos_llegada": [24.0, 48.0, 120.0],
            }
        ]

        with patch.object(mapper, "get_osrm_route", return_value=[[0, 0], [1, 1]]):
            mapper.render(routes)

            assert mock_popup.call_count == 4
            popups_html = [call.args[0] for call in mock_popup.call_args_list]

            html_text = " ".join(str(p) for p in popups_html)

            assert "A TIEMPO" in html_text
            assert "CADUCADO" in html_text
            assert "Última Entrega" in html_text
