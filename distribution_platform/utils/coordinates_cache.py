import json
from pathlib import Path


class CoordinateCache:
    """
    Simple persistent cache for destination → GPS coordinates.

    Stored as JSON:
    {
        "Guadalajara": "40.63,-3.16",
        "Madrid": "40.41,-3.70"
    }
    """

    def __init__(self, cache_path: str | Path | None = None):
        if cache_path is None:
            # Ruta por defecto dentro de /data/cache/
            base = Path(__file__).resolve().parent.parent.parent
            cache_dir = base / "data" / "cache"
            cache_dir.mkdir(parents=True, exist_ok=True)
            self.cache_path = cache_dir / "coordinates.json"
        else:
            self.cache_path = Path(cache_path)

        self.cache: dict[str, str | None] = {}
        self._load()

    # ---------------------------------------------------
    # LOAD
    # ---------------------------------------------------
    def _load(self):
        """Load the JSON cache file safely."""
        if not self.cache_path.exists():
            self.cache = {}
            return

        try:
            with open(self.cache_path, encoding="utf-8") as f:
                self.cache = json.load(f)

            if not isinstance(self.cache, dict):
                self.cache = {}

        except Exception:
            # Si el archivo está corrupto → reset
            self.cache = {}

    # ---------------------------------------------------
    # SAVE
    # ---------------------------------------------------
    def save(self):
        """Persist cache to disk safely."""
        try:
            with open(self.cache_path, "w", encoding="utf-8") as f:
                json.dump(self.cache, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"⚠️ Error saving coordinate cache: {e}")

    # ---------------------------------------------------
    # PUBLIC API
    # ---------------------------------------------------
    def get(self, destino: str):
        """Return cached coordinate or None."""
        return self.cache.get(destino)

    def set(self, destino: str, coord: str | None):
        """Store a coordinate in memory cache (not saved yet)."""
        self.cache[destino] = coord

    def exists(self, destino: str):
        """Check if destination exists in cache."""
        return destino in self.cache

    def clear(self):
        """Delete all cached data."""
        self.cache = {}
        self.save()

    def __len__(self):
        """Number of cached entries."""
        return len(self.cache)

    def __repr__(self):
        """String representation of the cache."""
        return f"CoordinateCache({len(self.cache)} entries)"
