"""
UI-specific constants and configuration.
"""


class UploadConfig:
    """Constraints for File Uploads."""

    MAX_FILE_SIZE_MB = 200
    SUPPORTED_FILE_TYPES = ["csv", "txt", "xlsx"]
    REQUIRED_FILES = {
        "pedidos": ("📦", "Orders (Pedidos)"),
        "clientes": ("👥", "Clients (Clientes)"),
        "lineas_pedido": ("📋", "Order Lines (Líneas de Pedido)"),
        "productos": ("🏷️", "Products (Productos)"),
        "destinos": ("📍", "Destinations (Destinos)"),
        "provincias": ("🗺️", "Provinces (Provincias)"),
    }


class Printer:
    @staticmethod
    def print_rules() -> str:
        """Prints the rules for vehicle parameters."""
        rules = [
            "**Prototype ID:** Must be unique, 3-50 characters, alphanumeric, spaces, hyphens.",
            "**Capacity (kg):**  The truck must have enough capacity for deliveries (in product units).",
            "**Fuel Consumption (L/100km):** The truck must have an acceptable fuel consumption rate.",
            "**Cruise Speed (km/h):** The truck must have a constant velocity during the route.",
            "**Driver Cost (€/h):** The truck must have a valid driver hourly rate.",
        ]
        return "\n".join([f"- {rule}" for rule in rules])


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


LOGO = "logo.png"
