import os

from dotenv import load_dotenv
from sqlalchemy import create_engine

# Cargar variables de entorno desde .env
load_dotenv()


def get_sql_engine():
    host = os.getenv("DB_HOST")
    port = os.getenv("DB_PORT")
    db = os.getenv("DB_NAME")
    user = os.getenv("DB_USER")
    password = os.getenv("DB_PASSWORD")
    driver = os.getenv("DB_DRIVER")

    # SQLAlchemy requiere "+" en drivers con espacios
    driver_encoded = driver.replace(" ", "+")

    connection_string = (
        f"mssql+pyodbc://{user}:{password}@{host}:{port}/{db}?driver={driver_encoded}"
    )

    return create_engine(connection_string)
