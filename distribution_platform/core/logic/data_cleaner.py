"""
Data Cleaning Logic.
Pure functions for DataFrame transformation and sanitization.
"""

import re

import pandas as pd


class DataCleaner:
    """Service for dataframe sanitization."""

    # Pre-compile regex for performance
    _NON_ALPHANUM = re.compile(r"[^0-9a-zA-Z]+")
    _CAMEL_TO_SNAKE = re.compile(r"([a-z0-9])([A-Z])")

    @classmethod
    def to_snake_case(cls, df: pd.DataFrame) -> pd.DataFrame:
        """Converts column names to snake_case."""
        df = df.copy()
        new_cols = []
        for col in df.columns:
            name = str(col)
            name = cls._NON_ALPHANUM.sub(" ", name)
            name = cls._CAMEL_TO_SNAKE.sub(r"\1_\2", name)
            new_cols.append(name.strip().lower().replace(" ", "_"))

        df.columns = new_cols
        return df

    @staticmethod
    def normalize_destinations(
        df: pd.DataFrame, col_name: str = "nombre_completo"
    ) -> pd.DataFrame:
        """Removes prefix 'Destino ' from the specified column."""
        if col_name in df.columns:
            df[col_name] = (
                df[col_name]
                .astype(str)
                .str.replace("Destino ", "", regex=False)
                .str.strip()
            )
        return df

    @staticmethod
    def clean_numeric_commas(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
        """Converts '10,5' strings to 10.5 floats."""
        for col in cols:
            if col in df.columns and df[col].dtype == "object":
                df[col] = (
                    df[col].str.replace(",", ".").apply(pd.to_numeric, errors="coerce")
                )
        return df
