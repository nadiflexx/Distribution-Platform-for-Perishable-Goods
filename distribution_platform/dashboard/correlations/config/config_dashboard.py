import sys
from pathlib import Path

# Agregar el raíz del proyecto para permitir imports absolutos
ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT))

from dataclasses import dataclass
from pathlib import Path
from typing import Literal
from predictions.config.paths import DATA_PROCESSED

@dataclass
class DashboardConfig:
    """A class to design the Dashboard."""

    title: str = "📊 Data Dashboard"
    layout: Literal["wide", "centered"] = "wide"
    default_data_path: Path = DATA_PROCESSED / "clean_dataset.csv"
    numeric_cols_only: bool = False
