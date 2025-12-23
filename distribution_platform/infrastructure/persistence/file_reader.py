"""
File I/O Adapter.
Handles reading from CSV, Excel, and Streamlit Buffers.
"""

from pathlib import Path
from typing import Any

import pandas as pd

from distribution_platform.config.enums import DataTypesEnum
from distribution_platform.config.logging_config import log as logger


class FileReader:
    """Utilities for reading dataframes from various sources."""

    @staticmethod
    def load_data(mode: DataTypesEnum, path: Path | str) -> pd.DataFrame:
        """Loads data from a physical path."""
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Data file not found: {path}")

        try:
            if mode == DataTypesEnum.CSV:
                return FileReader._read_csv_smart(path)
            elif mode == DataTypesEnum.EXCEL:
                return pd.read_excel(path)
            else:
                raise ValueError(f"Unsupported mode: {mode}")
        except Exception as e:
            logger.error(f"Error reading file {path}: {e}")
            raise

    @staticmethod
    def load_uploaded_file(uploaded_file: Any) -> pd.DataFrame:
        """Loads data from a Streamlit UploadedFile (buffer)."""
        filename = getattr(uploaded_file, "name", "").lower()

        try:
            if filename.endswith(".csv"):
                try:
                    return pd.read_csv(uploaded_file, sep=";", engine="python")
                except Exception:
                    uploaded_file.seek(0)
                    return pd.read_csv(uploaded_file, sep=",", engine="python")

            elif filename.endswith((".xls", ".xlsx")):
                return pd.read_excel(uploaded_file)

            else:
                raise ValueError(f"Unsupported file extension: {filename}")
        except Exception as e:
            logger.error(f"Error processing upload {filename}: {e}")
            raise

    @staticmethod
    def safe_concat(dfs: list[pd.DataFrame]) -> pd.DataFrame:
        """Concatenates a list of dataframes safely."""
        if not dfs:
            return pd.DataFrame()
        return pd.concat(dfs, ignore_index=True)

    @staticmethod
    def save_csv(df: pd.DataFrame, path: Path) -> None:
        """Saves dataframe to CSV."""
        path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(path, index=False)
        logger.info(f"Saved processed data to {path}")

    @staticmethod
    def _read_csv_smart(path: Path) -> pd.DataFrame:
        """Detects separator and reads CSV."""
        sep = ","
        try:
            with open(path, encoding="utf-8", errors="ignore") as f:
                line = f.readline()
                if ";" in line:
                    sep = ";"
        except Exception:
            pass
        return pd.read_csv(path, sep=sep, engine="python")
