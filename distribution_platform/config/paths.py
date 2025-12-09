import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
"""General settings for the application."""

DATA_RAW = ROOT / "data" / "raw"
DATA_PROCESSED = ROOT / "data" / "processed"
"""Application-wide settings and constants."""

# Application metadata
APP_CONFIG = {
    "title": "🚛 IA Delivery - Smart Route Optimizer",
    "page_icon": "🚛",
    "layout": "wide",
    "initial_sidebar_state": "collapsed",
}

# Page identifiers
PAGES = {
    "FORM": "form_page",
    "ROUTES": "routes_page",
}

# Session state keys
SESSION_KEYS = {
    "page": "current_page",
    "dataframe": "loaded_dataframe",
    "selected_trucks": "selected_trucks_data",
    "connection_type": "data_connection_type",
    "routes_result": "ai_routes_result",
    "validation_result": "truck_validation_result",
    "form_submitted": "form_was_submitted",
}

# File upload settings
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

# Media paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MEDIA_PATH = os.path.join(BASE_DIR, "dashboard", "front", "user_interface", "media")

TRUCK_IMAGES = {
    "large": os.path.join(MEDIA_PATH, "large_trucks"),
    "medium": os.path.join(MEDIA_PATH, "medium_trucks"),
    "custom": os.path.join(MEDIA_PATH, "custom_trucks"),
}

# Animation settings
ANIMATION_CONFIG = {
    "spinner_text": "🤖 AI is calculating optimal routes...",
    "loading_time": 2,  # seconds for demo
    "transition_time": 0.3,  # seconds
}

# Validation rules display
RULES_INFO = [
    "📋 The CSV file must contain all required fields",
    "📦 The truck must have sufficient capacity for all deliveries",
    "⛽ The truck must have acceptable fuel consumption rates",
    "🚗 The truck must maintain constant velocity during routes",
    "📍 All delivery locations must be within service area",
]
