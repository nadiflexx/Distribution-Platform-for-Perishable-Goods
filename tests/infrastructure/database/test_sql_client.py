from unittest.mock import patch

import pandas as pd

from distribution_platform.infrastructure.database.sql_client import (
    load_clients,
    load_destinations,
    load_full_dataset,
    load_order_lines,
    load_orders,
    load_products,
    load_provinces,
    load_provinces_names,
)


@patch("distribution_platform.infrastructure.database.sql_client.get_sql_engine")
@patch("pandas.read_sql")
class TestSqlClient:
    def test_all_loaders(self, mock_read_sql, mock_engine):
        mock_read_sql.return_value = pd.DataFrame({"id": [1]})

        assert not load_clients().empty
        assert not load_orders().empty
        assert not load_products().empty
        assert not load_destinations().empty
        assert not load_order_lines().empty
        assert not load_provinces().empty
        assert not load_provinces_names().empty
        assert not load_full_dataset().empty

    def test_load_functions(self, mock_read_sql, mock_engine):
        """Prueba que las funciones de carga llaman a pandas con la query correcta."""
        mock_read_sql.return_value = pd.DataFrame({"id": [1]})

        df = load_clients()
        assert not df.empty

        query_arg = mock_read_sql.call_args[0][0]
        assert "dbo.Clientes" in query_arg
