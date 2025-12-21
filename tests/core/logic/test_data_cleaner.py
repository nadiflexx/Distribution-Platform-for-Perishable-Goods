import pandas as pd

from distribution_platform.core.logic.data_cleaner import DataCleaner


class TestDataCleaner:
    def test_to_snake_case(self):
        df = pd.DataFrame(columns=["Nombre Completo", "FechaPedido", "ID"])
        res = DataCleaner.to_snake_case(df)
        assert list(res.columns) == ["nombre_completo", "fecha_pedido", "id"]

    def test_normalize_destinations(self):
        df = pd.DataFrame(
            {"destino": ["Destino Madrid", "Barcelona", "Destino  Soria "]}
        )
        res = DataCleaner.normalize_destinations(df, "destino")
        assert res.iloc[0]["destino"] == "Madrid"
        assert res.iloc[1]["destino"] == "Barcelona"
        assert res.iloc[2]["destino"] == "Soria"

    def test_clean_numeric_commas(self):
        df = pd.DataFrame(
            {
                "precio": ["10,5", "20.0", 30],  # Mix types
                "otro": ["a", "b", "c"],
            }
        )
        res = DataCleaner.clean_numeric_commas(df, ["precio"])

        assert res["precio"].dtype == "float64" or res["precio"].dtype == "int64"
        assert res.iloc[0]["precio"] == 10.5
        assert res.iloc[1]["precio"] == 20.0
