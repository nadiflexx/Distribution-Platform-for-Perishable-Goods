"""
Application Enumerations.
Central source of truth for types and constants.
"""

from enum import Enum, StrEnum, auto


class DataTypesEnum(Enum):
    """Supported data types for ingestion."""

    CSV = auto()
    JSON = auto()
    SQL = auto()
    EXCEL = auto()
    OTHER = auto()


class WorkflowError(StrEnum):
    """Application error codes."""

    FILE_ERROR = "FILE_ERROR"
    DB_ERROR = "DB_ERROR"
    ETL_ERROR = "ETL_ERROR"
    VALIDATION_ERROR = "VALIDATION_ERROR"
