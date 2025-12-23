"""
Truck Persistence Repository.
Handles loading/saving truck configurations from JSON storage.
"""

import json

from distribution_platform.config.logging_config import log as logger
from distribution_platform.config.settings import Paths


class TruckRepository:
    """Repository for managing truck data JSONs."""

    def __init__(self):
        self.storage_dir = Paths.STORAGE
        self.custom_images_dir = Paths.TRUCK_IMAGES["custom"]

    def get_trucks(self, category: str = "large") -> dict:
        """
        Retrieves trucks by category (large, medium, custom).
        """
        if category == "custom":
            return self._load_json("custom_trucks.json")

        data = self._load_json("large_medium_trucks.json")
        key = "camiones_grandes" if category == "large" else "camiones_medianos"
        return data.get(key, {})

    def save_custom_truck(self, truck_name: str, truck_data: dict) -> bool:
        """Adds a new custom truck to the JSON store."""
        current = self._load_json("custom_trucks.json") or {}
        current[truck_name] = truck_data
        return self._save_json("custom_trucks.json", current)

    def save_image(self, uploaded_file, truck_name: str) -> str:
        """Saves uploaded image to assets folder."""
        if not uploaded_file:
            return "truck_default.png"

        self.custom_images_dir.mkdir(parents=True, exist_ok=True)

        ext = uploaded_file.name.split(".")[-1].lower()
        safe_name = "".join(c for c in truck_name if c.isalnum() or c in "-_")
        filename = f"{safe_name}.{ext}"

        try:
            (self.custom_images_dir / filename).write_bytes(uploaded_file.getbuffer())
            return filename
        except Exception as e:
            logger.error(f"Image save failed: {e}")
            return "truck_default.png"

    def _load_json(self, filename: str) -> dict:
        path = self.storage_dir / filename
        if not path.exists():
            return {}
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception as e:
            logger.error(f"Error reading {filename}: {e}")
            return {}

    def _save_json(self, filename: str, data: dict) -> bool:
        try:
            path = self.storage_dir / filename
            path.write_text(
                json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8"
            )
            return True
        except Exception as e:
            logger.error(f"Error saving {filename}: {e}")
            return False
