import os
from unittest.mock import patch

from distribution_platform.infrastructure.database import queries
from distribution_platform.infrastructure.database.connection import get_sql_engine


class TestDatabaseConnection:
    @patch.dict(
        os.environ,
        {
            "DB_HOST": "localhost",
            "DB_PORT": "1433",
            "DB_NAME": "TestDB",
            "DB_USER": "sa",
            "DB_PASSWORD": "password123",
            "DB_DRIVER": "ODBC Driver 17 for SQL Server",
        },
    )
    @patch("distribution_platform.infrastructure.database.connection.create_engine")
    def test_get_sql_engine(self, mock_create_engine):
        """
        Verifica que se construye la URL de conexión correctamente,
        especialmente el reemplazo de espacios en el driver.
        """
        # Ejecutar
        get_sql_engine()

        # Verificar
        mock_create_engine.assert_called_once()

        # Obtenemos el argumento con el que se llamó a create_engine
        args, _ = mock_create_engine.call_args
        connection_string = args[0]

        # Verificamos que los espacios se cambiaron por +
        expected_driver = "ODBC+Driver+17+for+SQL+Server"
        assert expected_driver in connection_string
        assert "mssql+pyodbc://" in connection_string


class TestQueries:
    def test_queries_are_strings(self):
        """Verifica que las constantes SQL existen y son strings no vacíos."""
        assert isinstance(queries.GET_FULL_DATA, str)
        assert len(queries.GET_FULL_DATA) > 0
        assert "SELECT" in queries.GET_FULL_DATA

        assert isinstance(queries.GET_CLIENTS, str)
        assert "dbo.Clientes" in queries.GET_CLIENTS

    def test_date_query_parameters(self):
        """Verifica que la query por fechas tiene los placeholders correctos."""
        assert "%(start_date)s" in queries.GET_FULL_DATA_BY_DATE
        assert "%(end_date)s" in queries.GET_FULL_DATA_BY_DATE
