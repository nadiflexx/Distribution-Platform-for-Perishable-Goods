"""Carga y gestión de datos de camiones desde archivos JSON."""

import json
from pathlib import Path

from distribution_platform.config.paths import STORAGE_DIR, TRUCK_IMAGES

# ============================================
#  HELPERS DE RUTAS
# ============================================


def _get_data_dir() -> Path:
    """Directorio donde están los JSON de camiones."""
    return STORAGE_DIR


def _load_json_file(filename: str) -> dict:
    filepath = _get_data_dir() / filename

    if not filepath.exists():
        print(f"⚠️ JSON no encontrado: {filepath}")
        return {}

    try:
        return json.loads(filepath.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"⚠️ Error leyendo {filepath}: {e}")
        return {}


def _save_json_file(filename: str, data: dict) -> bool:
    filepath = _get_data_dir() / filename

    try:
        filepath.write_text(
            json.dumps(data, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
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
        assets/images/custom_trucks/<nombre>.<ext>
    """

    custom_dir: Path = TRUCK_IMAGES["custom"]
    custom_dir.mkdir(parents=True, exist_ok=True)

    # Si no sube imagen → default
    if uploaded_file is None:
        return "truck_default.png"

    ext = uploaded_file.name.split(".")[-1].lower()
    safe_name = "".join(c for c in truck_name if c.isalnum() or c in (" ", "-", "_"))
    filename = f"{safe_name}.{ext}"

    filepath = custom_dir / filename

    try:
        filepath.write_bytes(uploaded_file.getbuffer())
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
    camiones = get_camiones_personalizados() or {}

    camiones[nombre] = {
        "capacidad": capacidad,
        "consumo": consumo,
        "velocidad_constante": velocidad_constante,
        "precio_conductor_hora": precio_conductor_hora,
        "imagen": imagen,
    }

    return _save_json_file("camiones_personalizados.json", camiones)


# ============================================
#  EXPORTACIÓN DE DATOS GLOBALES
# ============================================

CAMIONES_GRANDES = get_camiones_grandes()
CAMIONES_MEDIANOS = get_camiones_medianos()
CAMIONES_PERSONALIZADOS = get_camiones_personalizados()
