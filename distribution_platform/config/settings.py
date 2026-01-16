"""
Global Configuration Settings.
Single Source of Truth (SSOT) for the entire project.
Combines paths, UI settings, Map configurations and Business Rules.
"""

from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


class Paths:
    """Centralized management of project file paths."""

    ROOT = Path(__file__).resolve().parents[2]

    # Backend / Data Paths
    DATA = ROOT / "data"
    DATA_RAW = DATA / "raw"
    DATA_PROCESSED = DATA / "processed"
    STORAGE = DATA / "storage"
    LOGS = ROOT / "logs"

    # App Source Paths
    MAIN_DIR = ROOT / "distribution_platform"
    ASSETS = MAIN_DIR / "assets"
    MEDIA = ASSETS / "images"
    STYLES = ASSETS / "styles"

    # Specific Files
    CSS_FILE = STYLES / "components.css"

    # Dynamic Image Paths
    TRUCK_IMAGES = {
        "large": MEDIA / "large_trucks",
        "medium": MEDIA / "medium_trucks",
        "custom": MEDIA / "custom_trucks",
    }

    @classmethod
    def make_dirs(cls):
        """Creates critical directories if they don't exist."""
        dirs_to_create = [
            cls.DATA_RAW,
            cls.DATA_PROCESSED,
            cls.STORAGE,
            cls.MEDIA,
            cls.TRUCK_IMAGES["large"],
            cls.TRUCK_IMAGES["medium"],
            cls.TRUCK_IMAGES["custom"],
        ]
        for path in dirs_to_create:
            path.mkdir(parents=True, exist_ok=True)


Paths.make_dirs()


class ExternalServices:
    """Configuration for external services."""

    OSRM_SERVER = "https://routing.openstreetmap.de/routed-car"
    SCOPES = ["https://www.googleapis.com/auth/drive"]


class MapConfig:
    """Mapping and Routing Configuration."""

    DEFAULTS = {
        "center": [40.2, -3.5],
        "zoom_start": 6,
        "tiles": "CartoDB positron",
    }

    ROUTE_STYLE = {
        "weight": 4,
        "opacity": 0.9,
        "dash_array": None,
    }

    ROUTE_COLORS = [
        "#FF6B6B",
        "#4ECDC4",
        "#FFD166",
        "#1B9AAA",
        "#9B5DE5",
        "#06D6A0",
        "#F4A261",
        "#E76F51",
        "#8AC926",
        "#FF9F1C",
        "#2A9D8F",
        "#E63946",
        "#F72585",
        "#3A0CA3",
        "#4361EE",
        "#4CC9F0",
        "#720026",
        "#FF5733",
        "#C70039",
        "#900C3F",
        "#581845",
        "#1F51FF",
        "#FF6F61",
        "#6B5B95",
        "#88B04B",
        "#F7CAC9",
        "#92A8D1",
        "#955251",
        "#B565A7",
        "#009B77",
        "#DD4124",
        "#45B8AC",
        "#EFC050",
        "#5B5EA6",
        "#9E1030",
        "#3B3B98",
        "#F08A5D",
        "#B83B5E",
        "#6A2C70",
        "#F2545B",
        "#72DDF7",
        "#F5DD90",
        "#D81159",
        "#8F2D56",
        "#218380",
        "#73D2DE",
        "#F46036",
        "#2E86AB",
        "#F4D35E",
        "#EE6C4D",
        "#3D5A80",
        "#98C1D9",
    ]
