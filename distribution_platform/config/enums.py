"""
Application Enumerations.
Central source of truth for types and constants.
"""

from enum import Enum, auto


class DataTypesEnum(Enum):
    """Supported data types for ingestion."""

    CSV = auto()
    JSON = auto()
    SQL = auto()
    EXCEL = auto()
    TXT = auto()
    OTHER = auto()
