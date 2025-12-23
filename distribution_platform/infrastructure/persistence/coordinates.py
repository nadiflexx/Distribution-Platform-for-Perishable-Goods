"""
Persistent Cache for Geolocation.
Handles reading/writing coordinates to a JSON file to minimize API calls.
"""

import json
from pathlib import Path

from distribution_platform.config.logging_config import log as logger


class CoordinateCache:
    """
    JSON-based Key-Value store for 'Destination -> Lat,Lon'.
    """

    def __init__(self, cache_path: Path | None = None):
        if cache_path is None:
            base = Path(__file__).resolve().parents[3]
            self.cache_path = base / "data" / "storage" / "coordinates.json"
        else:
            self.cache_path = cache_path

        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        self.cache: dict[str, str | None] = {}
        self._load()

    def _load(self) -> None:
        """Loads cache from disk safely."""
        if not self.cache_path.exists():
            return
        try:
            with open(self.cache_path, encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    self.cache = data
        except Exception as e:
            logger.error(f"Failed to load coordinate cache: {e}")
            self.cache = {}

    def save(self) -> None:
        """Persists cache to disk."""
        try:
            with open(self.cache_path, "w", encoding="utf-8") as f:
                json.dump(self.cache, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Failed to save coordinate cache: {e}")

    def get(self, destination: str) -> str | None:
        return self.cache.get(destination)

    def set(self, destination: str, coord: str | None) -> None:
        self.cache[destination] = coord
