"""
UI-specific constants and configuration.
"""

# Supported file types for data upload
SUPPORTED_FILE_TYPES = ["csv", "txt", "xlsx"]


# Application phases
class AppPhase:
    SPLASH = "SPLASH"
    FORM = "FORM"
    PROCESSING = "PROCESSING"
    RESULTS = "RESULTS"


# Vehicle categories
class VehicleCategory:
    HEAVY = "Heavy Duty"
    MEDIUM = "Medium Duty"
    CUSTOM = "Custom Prototype"

    @classmethod
    def all(cls):
        """Get all vehicle categories."""
        return [cls.HEAVY, cls.MEDIUM, cls.CUSTOM]

    @classmethod
    def to_key(cls, category: str) -> str:
        """Convert vehicle category to a key string."""
        return "large" if "Heavy" in category else "medium"
