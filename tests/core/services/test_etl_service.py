from unittest.mock import patch

import pandas as pd
import pytest

from distribution_platform.core.models.order import Order
from distribution_platform.core.services.etl_service import ETLService, run_etl


@pytest.fixture
def sample_df():
    """DataFrame que simula datos COMPLETOS listos para procesar."""
    return pd.DataFrame(
        {
            "pedido_id": [1, 1, 2],
            "fecha_pedido": ["2023-01-01", "2023-01-01", "2023-01-02"],
            "producto": ["A", "B", "C"],
            "cantidad_producto": [10, 20, 30],
            "precio_venta": [100, 200, 300],
            "tiempo_fabricacion_medio": [1, 1, 2],
            "caducidad": [10, 10, 5],
            "destino": ["Madrid", "Madrid", "Barcelona"],
            "distancia_km": [500, 500, 600],
            "email_cliente": ["a@a.com", "a@a.com", "b@b.com"],
            "dias_totales_caducidad": [12, 12, 8],
            "fecha_caducidad_final": ["2023-01-13", "2023-01-13", "2023-01-10"],
        }
    )


@patch("distribution_platform.core.services.etl_service.Paths")
@patch("distribution_platform.core.services.etl_service.CoordinateCache")
class TestETLService:
    @patch("distribution_platform.core.services.etl_service.FileReader")
    def test_pipeline_files_cached(
        self, mock_file_reader, mock_cache, mock_paths, sample_df
    ):
        mock_paths.return_value.DATA_PROCESSED.__truediv__.return_value.exists.return_value = True

        mock_file_reader.load_data.return_value = sample_df

        service = ETLService()
        result = service.run(use_database=False)

        mock_file_reader.load_data.assert_called_once()
        assert len(result) == 2
        assert isinstance(result[0][0], Order)

    @patch("distribution_platform.core.services.etl_service.FileReader")
    @patch("distribution_platform.core.services.etl_service.DataCleaner")
    def test_pipeline_files_raw(
        self, mock_cleaner, mock_file_reader, mock_cache, mock_paths, sample_df
    ):
        mock_paths.return_value.DATA_PROCESSED.__truediv__.return_value.exists.return_value = False

        mock_file_reader.load_data.return_value = pd.DataFrame()
        mock_file_reader.safe_concat.return_value = pd.DataFrame()
        mock_file_reader.load_uploaded_file.return_value = pd.DataFrame()

        with patch.object(ETLService, "_merge_datasets") as mock_merge:

            def side_effect_merge():
                service.df_final = sample_df

            mock_merge.side_effect = side_effect_merge

            service = ETLService()
            result = service.run(uploaded_files={"pedidos": []}, use_database=False)

            mock_merge.assert_called()
            assert len(result) == 2

    @patch("distribution_platform.core.services.etl_service.load_full_dataset")
    @patch("distribution_platform.core.services.etl_service.load_provinces_names")
    def test_pipeline_database(
        self, mock_provinces, mock_load_full, mock_cache, mock_paths, sample_df
    ):
        sql_df = sample_df.rename(
            columns={
                "producto": "nombre",
                "cantidad_producto": "cantidad",
                "email_cliente": "email",
                "destino": "nombre_completo",
            }
        ).drop(columns=["dias_totales_caducidad", "fecha_caducidad_final"])

        sql_df["coordenadas_gps"] = "0,0"

        mock_load_full.return_value = sql_df
        mock_provinces.return_value = pd.DataFrame({"nombre": ["Madrid", "Barcelona"]})

        service = ETLService()
        result = service.run(use_database=True)

        mock_load_full.assert_called_once()
        first_order = result[0][0]
        assert first_order.dias_totales_caducidad > 0

    @patch("distribution_platform.core.services.etl_service.fetch_coordinates")
    def test_build_geo_cache(self, mock_fetch, mock_cache, mock_paths):
        service = ETLService()
        cache_instance = mock_cache.return_value
        cache_instance.get.side_effect = lambda x: "cached" if x == "Madrid" else None
        df = pd.DataFrame({"nombre": ["Madrid", "Soria"]})
        service._build_geo_cache(df, "nombre")
        assert mock_fetch.call_count >= 1

    def test_load_uploads(self, mock_cache, mock_paths):
        files = {"pedidos": ["file1"]}
        with patch(
            "distribution_platform.core.services.etl_service.FileReader"
        ) as mock_reader:
            mock_reader.load_uploaded_file.return_value = pd.DataFrame()
            mock_reader.safe_concat.return_value = pd.DataFrame()
            service = ETLService()
            service._load_uploads(files)
            assert mock_reader.safe_concat.called

    def test_wrapper_run_etl(self, mock_cache, mock_paths):
        with patch(
            "distribution_platform.core.services.etl_service.ETLService"
        ) as MockService:
            run_etl(use_database=True)
            MockService.return_value.run.assert_called_with(None, True)

    def test_merge_datasets_logic(self, mock_cache, mock_paths):
        """Prueba la lógica interna de mergeo de tablas."""
        service = ETLService()

        service.df_pedidos = pd.DataFrame(
            {
                "pedido_id": [1],
                "cliente_id": [10],
                "destino_entrega_id": [100],
                "fecha_pedido": ["2023-01-01"],
                "caducidad": [10],
            }
        )
        service.df_clientes = pd.DataFrame({"cliente_id": [10], "email": ["a@a.com"]})
        service.df_destinos = pd.DataFrame(
            {
                "destino_id": [100],
                "nombre_completo": "Destino Madrid",
                "distancia_km": [500],
            }
        )
        service.df_lineas = pd.DataFrame(
            {
                "pedido_id": [1],
                "producto_id": [50],
                "cantidad": [5],
                "linea_pedido_id": [999],
            }
        )
        service.df_productos = pd.DataFrame(
            {
                "producto_id": [50],
                "nombre": "Manzana",
                "precio_venta": [2.5],
                "tiempo_fabricacion_medio": [1],
            }
        )

        service._merge_datasets()

        df = service.df_final
        assert not df.empty
        assert "email_cliente" in df.columns
        assert df.iloc[0]["producto"] == "Manzana"
        assert df.iloc[0]["destino"] == "Madrid"
        assert "fecha_caducidad_final" in df.columns

    def test_load_uploads_real_logic(self, mock_cache, mock_paths):
        """Prueba la lógica de _load_uploads con diccionarios."""
        service = ETLService()

        with patch(
            "distribution_platform.core.services.etl_service.FileReader"
        ) as mock_reader:
            mock_reader.load_uploaded_file.return_value = pd.DataFrame({"id": [1]})
            mock_reader.safe_concat.side_effect = (
                lambda x: pd.concat(x) if x else pd.DataFrame()
            )

            files_dict = {"clientes": ["file_c"], "pedidos": ["file_p"]}

            service._load_uploads(files_dict)

            assert not service.df_clientes.empty
            assert not service.df_pedidos.empty
            assert service.df_productos.empty

    def test_transform_to_orders_empty(self, mock_cache, mock_paths):
        """Cubre el caso de df vacío."""
        service = ETLService()
        res = service._transform_to_orders(pd.DataFrame())
        assert res == []
        res = service._transform_to_orders(None)
        assert res == []
