import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

load_dotenv()


def get_sql_engine() -> Engine:
    """
    Creates and returns a SQLAlchemy connection engine for a SQL Server database.

    Use environment variables to obtain credentials and connection parameters.
    The spaces in the ODBC driver number are replaced by '+' to be compatible
    in the format of the SQLAlchemy connection URL.

    Returns:
    sqlalchemy.engine.Engine: An Engine object configured to connect to the database.

    Raises:
    KeyError: If any of the required environment variables is not defined.
    """
    host = os.getenv("DB_HOST")
    port = os.getenv("DB_PORT")
    db = os.getenv("DB_NAME")
    user = os.getenv("DB_USER")
    password = os.getenv("DB_PASSWORD")
    driver = os.getenv("DB_DRIVER")

    if driver is None:
        raise ValueError("La variable de entorno DB_DRIVER no está definida.")

    driver_encoded = driver.replace(" ", "+")

    connection_string = (
        f"mssql+pyodbc://{user}:{password}@{host}:{port}/{db}?driver={driver_encoded}"
    )

    return create_engine(connection_string)
