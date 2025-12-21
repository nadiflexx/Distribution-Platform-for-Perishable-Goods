import pandas as pd

from .connection import get_sql_engine
from .queries import (
    GET_CLIENTS,
    GET_DESTINATIONS,
    GET_FULL_DATA,
    GET_FULL_DATA_BY_DATE,
    GET_LINE_ITEMS,
    GET_ORDERS,
    GET_PRODUCTS,
    GET_PROVINCES,
    GET_PROVINCES_NAME,
)

engine = get_sql_engine()


def load_full_dataset():
    """Executes a single SQL query that returns the entire merged dataset."""
    return pd.read_sql(GET_FULL_DATA, engine)


def load_full_dataset_between_dates(start_date, end_date):
    """
    Executes a SQL query that returns the merged dataset filtered by date.

    Args:
        start_date (str or datetime): Fecha de inicio (inclusive).
        end_date (str or datetime): Fecha de fin (inclusive).
    """
    # Usamos un diccionario de parámetros para seguridad y formato
    params = {"start_date": start_date, "end_date": end_date}

    return pd.read_sql(GET_FULL_DATA_BY_DATE, engine, params=params)


def load_provinces_names():
    """Executes a SQL query that returns the list of distinct provinces names."""
    return pd.read_sql(GET_PROVINCES_NAME, engine)


def load_clients():
    """Executes a SQL query that returns the list of distinct clients."""
    return pd.read_sql(GET_CLIENTS, engine)


def load_products():
    """Executes a SQL query that returns the list of distinct products."""
    return pd.read_sql(GET_PRODUCTS, engine)


def load_orders():
    """Executes a SQL query that returns the list of distinct orders."""
    return pd.read_sql(GET_ORDERS, engine)


def load_provinces():
    """Executes a SQL query that returns the list of distinct provinces."""
    return pd.read_sql(GET_PROVINCES, engine)


def load_destinations():
    """Executes a SQL query that returns the list of distinct destinations."""
    return pd.read_sql(GET_DESTINATIONS, engine)


def load_order_lines():
    """Executes a SQL query that returns the list of distinct order lines."""
    return pd.read_sql(GET_LINE_ITEMS, engine)
