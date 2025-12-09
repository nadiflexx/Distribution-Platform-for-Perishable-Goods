import pandas as pd

from .connection import get_sql_engine
from .queries import GET_FULL_DATA, GET_PROVINCES

engine = get_sql_engine()


def load_full_dataset():
    """Executes a single SQL query that returns the entire merged dataset."""
    return pd.read_sql(GET_FULL_DATA, engine)


def load_provinces():
    """Executes a SQL query that returns the list of distinct provinces."""
    return pd.read_sql(GET_PROVINCES, engine)
