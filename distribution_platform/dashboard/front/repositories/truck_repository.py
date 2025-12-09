"""Carga y gestión de datos de camiones desde archivos JSON."""

import json
import os

from distribution_platform.config.paths import TRUCK_IMAGES

# ============================================
#  HELPERS DE RUTAS
# ============================================


def _get_data_dir() -> str:
    """Directorio donde están los JSON de camiones."""
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data_models"))


def _load_json_file(filename: str) -> dict:
    """Carga un archivo JSON y devuelve un diccionario seguro."""
    filepath = os.path.join(_get_data_dir(), filename)

    if not os.path.exists(filepath):
        print(f"⚠️ JSON no encontrado: {filepath}")
        return {}

    try:
        with open(filepath, encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"⚠️ Error leyendo {filepath}: {e}")
        return {}


def _save_json_file(filename: str, data: dict) -> bool:
    """Guarda un diccionario en JSON."""
    filepath = os.path.join(_get_data_dir(), filename)

    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"❌ Error guardando JSON {filepath}: {e}")
        return False


# ============================================
#  CARGA DE CAMIONES
# ============================================


def get_camiones_grandes() -> dict:
    data = _load_json_file("camiones.json")
    return data.get("camiones_grandes", {})


def get_camiones_medianos() -> dict:
    data = _load_json_file("camiones.json")
    return data.get("camiones_medianos", {})


def get_camiones_personalizados() -> dict:
    return _load_json_file("camiones_personalizados.json")


# ============================================
#  GUARDAR IMÁGENES DE CAMIONES PERSONALIZADOS
# ============================================


def save_custom_truck_image(uploaded_file, truck_name: str) -> str:
    """
    Guarda imágenes en:
        media/custom_trucks/<nombre>.png
    """

    custom_dir = TRUCK_IMAGES["custom"]  # viene directo desde paths.py
    os.makedirs(custom_dir, exist_ok=True)

    # Si no sube imagen → default
    if uploaded_file is None:
        return "truck_default.png"

    # Safe filename
    ext = uploaded_file.name.split(".")[-1].lower()
    safe_name = "".join(c for c in truck_name if c.isalnum() or c in (" ", "-", "_"))
    filename = f"{safe_name}.{ext}"

    filepath = os.path.join(custom_dir, filename)

    try:
        with open(filepath, "wb") as f:
            f.write(uploaded_file.getbuffer())
        return filename
    except Exception as e:
        print(f"❌ Error guardando imagen personalizada: {e}")
        return "truck_default.png"


# ============================================
#  GUARDAR CAMIONES PERSONALIZADOS
# ============================================


def add_camion_personalizado(
    nombre: str,
    capacidad: str,
    consumo: str,
    velocidad_constante: str,
    precio_conductor_hora: str,
    imagen: str = "truck_default.png",
) -> bool:
    """
    Añade un camión personalizado sin sobrescribir los existentes.
    Guarda en camiones_personalizados.json.
    """

    camiones = get_camiones_personalizados()
    if not isinstance(camiones, dict):
        camiones = {}

    camiones[nombre] = {
        "capacidad": capacidad,
        "consumo": consumo,
        "velocidad_constante": velocidad_constante,
        "precio_conductor_hora": precio_conductor_hora,
        "imagen": imagen,  # solo el nombre del archivo
    }

    return _save_json_file("camiones_personalizados.json", camiones)


# ============================================
#  EXPORTACIÓN DE DATOS GLOBALES
# ============================================

CAMIONES_GRANDES = get_camiones_grandes()
CAMIONES_MEDIANOS = get_camiones_medianos()
CAMIONES_PERSONALIZADOS = get_camiones_personalizados()
