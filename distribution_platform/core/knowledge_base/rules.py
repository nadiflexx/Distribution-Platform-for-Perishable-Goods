"""Rules of the expert system for truck validation.

Every rule is a function that receives a `Truck` object or raw data and returns a
message with the validation result. Messages start with
"[SUCCESS]" for conditions met or "[ERROR]" for failures; this is consumed by
the `InferenceEngine` to generate the final decision.
"""

from collections.abc import Callable
import re

from distribution_platform.core.models.truck import Truck


def obtain_rules() -> list[Callable[[Truck], str]]:
    """Returns the list of rule functions to be executed by the engine.

    Maintain the order of the rules for predictable output.
    """
    return [
        velocity_rule,
        consumption_rule,
        capacity_rule,
        precio_conductor_hora_rule,
    ]


def obtain_format_validation_rules() -> list[Callable[[dict], str]]:
    """Returns the format validation rules for custom trucks.

    These rules validate that the data is valid before converting it
    to a Truck object.
    """
    return [
        validate_nombre_format,
        validate_capacidad_format,
        validate_consumo_format,
        validate_velocidad_format,
        validate_precio_conductor_hora_format,
    ]


# ==================== EXISTING VALIDATION RULES ====================


def velocity_rule(truck: Truck) -> str:
    """R1: The truck's velocity must be constant and valid during the route."""
    min_vel = 30.0
    max_vel = 120.0

    if min_vel <= truck.velocidad_constante <= max_vel:
        return f"[SUCCESS] (R1) The truck's velocity ({truck.velocidad_constante} km/h) is valid."

    return f"[ERROR] (R1) The truck's velocity ({truck.velocidad_constante} km/h) is outside valid range ({min_vel}-{max_vel} km/h)."


def consumption_rule(truck: Truck) -> str:
    """R2: The truck's fuel consumption must be within acceptable limits."""
    min_consumo = 5.0  # Nadie gasta 1L a los 100km
    max_consumo = 50.0

    if min_consumo <= truck.consumo_combustible <= max_consumo:
        return f"[SUCCESS] (R2) The truck's fuel consumption ({truck.consumo_combustible} L/100km) is valid."

    return f"[ERROR] (R2) The truck's fuel consumption ({truck.consumo_combustible} L/100km) is outside valid range ({min_consumo}-{max_consumo} L/100km)."


def capacity_rule(truck: Truck) -> str:
    """R3: The truck must have sufficient capacity (in product units)."""
    min_cap = 100  # Un camión de menos de 100kg no es útil

    if truck.capacidad_carga >= min_cap:
        return f"[SUCCESS] (R3) The truck has sufficient capacity ({truck.capacidad_carga} products)."

    return f"[ERROR] (R3) The truck capacity ({truck.capacidad_carga} kg) is too low (min: {min_cap} kg)."


def precio_conductor_hora_rule(truck: Truck) -> str:
    """R4: The truck must have a valid driver hourly rate."""
    precio_min = 10.0
    precio_max = 50.0

    if precio_min <= truck.precio_conductor_hora <= precio_max:
        return f"[SUCCESS] (R4) The truck's driver rate (€{truck.precio_conductor_hora}/h) is within acceptable range."

    return f"[ERROR] (R4) The truck's driver rate (€{truck.precio_conductor_hora}/h) is outside acceptable range (€{precio_min}-€{precio_max})."


# ==================== FORMAT VALIDATION RULES ====================


def validate_nombre_format(data: dict) -> str:
    """Validates the format of the truck's name.

    Args:
        data: Dictionary with the custom truck's data

    Returns
    -------
        Validation message ([SUCCESS] or [ERROR])
    """
    nombre = data.get("nombre", "").strip()

    if not nombre:
        return "[ERROR] (Nombre) The truck's name cannot be empty."

    if len(nombre) < 3:
        return "[ERROR] (Nombre) The name must have at least 3 characters."

    if len(nombre) > 50:
        return "[ERROR] (Nombre) The name cannot exceed 50 characters."

    if not re.match(r"^[a-zA-Z0-9\s\-áéíóúÁÉÍÓÚñÑ]+$", nombre):
        return (
            "[ERROR] (Nombre) The name contains invalid characters. "
            "Only letters, numbers, spaces and hyphens are allowed."
        )

    return f"[SUCCESS] (Nombre) Valid name format: '{nombre}'."


def validate_capacidad_format(data: dict) -> str:
    """Validates the format and range of the truck's capacity (in product units).
    Args:
        data: Dictionary with the custom truck's data

    Returns
    -------
        Validation message ([SUCCESS] or [ERROR])
    """
    capacidad = data.get("capacidad", "")

    if capacidad == "" or capacidad is None:
        return "[ERROR] (Capacidad) The capacity cannot be empty."

    try:
        numero = int(float(capacidad))
    except (ValueError, TypeError):
        return (
            "[ERROR] (Capacidad) Invalid capacity format. "
            "Enter only integers (e.g., 100 for 100 products)."
        )

    if numero < 10:
        return "[ERROR] (Capacidad) The capacity must be at least 10 products."

    if numero > 200:
        return "[ERROR] (Capacidad) The capacity cannot exceed 200 products."

    return f"[SUCCESS] (Capacidad) Valid capacity format: {numero} products."


def validate_consumo_format(data: dict) -> str:
    """Validates the format and range of the truck's fuel consumption.

    Args:
        data: Dictionary with the custom truck's data

    Returns
    -------
        Validation message ([SUCCESS] or [ERROR])
    """
    consumo = data.get("consumo", "")

    if consumo == "" or consumo is None:
        return "[ERROR] (Consumo) The fuel consumption cannot be empty."

    try:
        numero = float(consumo) if isinstance(consumo, str) else consumo
    except (ValueError, TypeError):
        return (
            "[ERROR] (Consumo) Invalid fuel consumption format. "
            "Enter only numbers (e.g., 30 for 30 L/100km)."
        )

    if numero < 10:
        return "[ERROR] (Consumo) The fuel consumption cannot be less than 10 L/100km."

    if numero > 50:
        return "[ERROR] (Consumo) The fuel consumption cannot exceed 50 L/100km."

    return f"[SUCCESS] (Consumo) Valid fuel consumption format: {numero} L/100km."


def validate_velocidad_format(data: dict) -> str:
    """Validates the format and range of the truck's constant speed.

    Args:
        data: Dictionary with the custom truck's data

    Returns
    -------
        Validation message ([SUCCESS] or [ERROR])
    """
    velocidad = data.get("velocidad_constante", "")

    if velocidad == "" or velocidad is None:
        return "[ERROR] (Velocidad) The constant speed cannot be empty."

    try:
        numero = float(velocidad) if isinstance(velocidad, str) else velocidad
    except (ValueError, TypeError):
        return (
            "[ERROR] (Velocidad) Invalid speed format. "
            "Enter only numbers (e.g., 75 for 75 km/h)."
        )

    if numero < 30:
        return "[ERROR] (Velocidad) The speed must be at least 30 km/h."

    if numero > 120:
        return "[ERROR] (Velocidad) The speed cannot exceed 120 km/h."

    return f"[SUCCESS] (Velocidad) Valid speed format: {numero} km/h."


def validate_precio_conductor_hora_format(data: dict) -> str:
    """Validates the format and range of the driver's hourly rate.

    Args:
        data: Dictionary with the custom truck's data

    Returns
    -------
        Validation message ([SUCCESS] or [ERROR])
    """
    precio_conductor = data.get("precio_conductor_hora", "")

    if precio_conductor == "" or precio_conductor is None:
        return "[ERROR] (Precio Conductor) The driver's hourly rate cannot be empty."

    try:
        numero = (
            float(precio_conductor)
            if isinstance(precio_conductor, str)
            else precio_conductor
        )
    except (ValueError, TypeError):
        return (
            "[ERROR] (Precio Conductor) Invalid price format. "
            "Enter only numbers (e.g., 15.0 for €15.00/h)."
        )

    if numero < 10.0:
        return "[ERROR] (Precio Conductor) The price must be at least €10.00/h."

    if numero > 50.0:
        return "[ERROR] (Precio Conductor) The price cannot exceed €50.00/h."

    return f"[SUCCESS] (Precio Conductor) Valid price format: €{numero}/h."


def parse_truck_data(data: dict) -> tuple[bool | Truck, dict | Truck]:
    """Transforms numerical data into a Truck object.

    The data is already validated, it only needs to be converted to the correct types
    and create an instance of Truck.

    Args:
        data: Dictionary with truck data (validated numerical values)

    Returns
    -------
        Tuple (is_valid, Truck_object_or_error)
    """
    try:
        capacidad_num = int(float(data.get("capacidad", 0)))
        consumo_num = float(data.get("consumo", 0))
        velocidad_num = float(data.get("velocidad_constante", 0))
        precio_conductor_num = float(data.get("precio_conductor_hora", 12.0))
        nombre = str(data.get("nombre", ""))
        imagen = data.get("imagen", "truck_default.png")

        truck = Truck(
            nombre=nombre,
            velocidad_constante=velocidad_num,
            consumo_combustible=consumo_num,
            capacidad_carga=capacidad_num,
            precio_conductor_hora=precio_conductor_num,
            imagen=imagen,
        )

        return True, truck
    except Exception as e:
        return False, {"error": str(e)}
