from pathlib import Path

"""General settings for the application."""

# =========================================================
# BASE PATHS
# =========================================================

ROOT = Path(__file__).resolve().parents[2]

DATA_DIR = ROOT / "data"
DATA_RAW = DATA_DIR / "raw"
DATA_PROCESSED = DATA_DIR / "processed"
STORAGE_DIR = DATA_DIR / "storage"
MAIN_DIR = ROOT / "distribution_platform"
ASSETS_DIR = MAIN_DIR / "assets"
MEDIA_PATH = ASSETS_DIR / "images"
CSS_PATH = ASSETS_DIR / "styles" / "components.css"

TRUCK_IMAGES = {
    "large": MEDIA_PATH / "large_trucks",
    "medium": MEDIA_PATH / "medium_trucks",
    "custom": MEDIA_PATH / "custom_trucks",
}

# =========================================================
# APPLICATION METADATA
# =========================================================

APP_CONFIG = {
    "title": "🚛 IA Delivery - Smart Route Optimizer",
    "page_icon": "🚛",
    "layout": "wide",
    "initial_sidebar_state": "collapsed",
}

# =========================================================
# PAGE IDENTIFIERS
# =========================================================

PAGES = {
    "FORM": "form_page",
    "ROUTES": "routes_page",
}

# =========================================================
# SESSION STATE KEYS
# =========================================================

SESSION_KEYS = {
    "page": "current_page",
    "dataframe": "loaded_dataframe",
    "selected_trucks": "selected_trucks_data",
    "connection_type": "data_connection_type",
    "routes_result": "ai_routes_result",
    "validation_result": "truck_validation_result",
    "form_submitted": "form_was_submitted",
}

# =========================================================
# FILE UPLOAD SETTINGS
# =========================================================

UPLOAD_CONFIG = {
    "max_file_size": 200,  # MB
    "allowed_extensions": ["csv"],
    "required_files": [
        "clientes",
        "lineas_pedido",
        "pedidos",
        "productos",
        "provincias",
        "destinos",
    ],
}

# =========================================================
# UI / ANIMATION SETTINGS
# =========================================================

ANIMATION_CONFIG = {
    "spinner_text": "🤖 AI is calculating optimal routes...",
    "loading_time": 2,  # seconds (demo)
    "transition_time": 0.3,  # seconds
}

# =========================================================
# VALIDATION RULES DISPLAY
# =========================================================

RULES_INFO = [
    "📋 The CSV file must contain all required fields",
    "📦 The truck must have sufficient capacity for all deliveries",
    "⛽ The truck must have acceptable fuel consumption rates",
    "🚗 The truck must maintain constant velocity during routes",
    "📍 All delivery locations must be within service area",
]

# =========================================================
# DRIVE AUTH
# =========================================================
SCOPES = ["https://www.googleapis.com/auth/drive"]
