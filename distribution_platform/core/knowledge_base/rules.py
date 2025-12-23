"""Rules of the expert system for truck validation.

Every rule is a function that receives a `Truck` object or raw data and returns a
message with the validation result. Messages start with
"✔" for conditions met or "✘" for failures; this is consumed by
the `InferenceEngine` to generate the final decision.
"""

from collections.abc import Callable
import re

from distribution_platform.core.models.truck import Truck


def print_rules() -> list[str]:
    """Returns the human-readable list of business rules.

    Used by the UI to display the available rules.
    """
    return [
        "- The csv file must contain all required fields.",
        "- The truck must have enough capacity for deliveries (in product units).",
        "- The truck must have an acceptable fuel consumption rate.",
        "- The truck must have a constant velocity during the route.",
        "- The truck must have a valid operational cost per kilometer.",
        "- The truck must have a valid driver hourly rate.",
    ]


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
    """Retorna las reglas de validación de formato para camiones personalizados.

    Estas reglas validan que los datos sean válidos antes de convertirlos
    a objeto Truck.
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
    if truck.velocidad_constante > 0:
        return (
            f"✔ (R1) The truck's velocity ({truck.velocidad_constante} km/h) is valid."
        )

    return "✘ (R1) The truck's velocity is not valid."


def consumption_rule(truck: Truck) -> str:
    """R2: The truck's fuel consumption must be within acceptable limits."""
    limite_consumo = 50.0
    if truck.consumo_combustible <= limite_consumo:
        return f"✔ (R2) The truck's fuel consumption ({truck.consumo_combustible} L/100km) is within acceptable limits (max: {limite_consumo})."

    return f"✘ (R2) The truck's fuel consumption ({truck.consumo_combustible} L/100km) exceeds acceptable limits (max: {limite_consumo})."


def capacity_rule(truck: Truck) -> str:
    """R3: The truck must have sufficient capacity (in product units)."""
    if truck.capacidad_carga > 0:
        return f"✔ (R3) The truck has sufficient capacity ({truck.capacidad_carga} products)."

    return "✘ (R3) The truck does not have sufficient capacity."


def precio_conductor_hora_rule(truck: Truck) -> str:
    """R5: The truck must have a valid driver hourly rate."""
    precio_min = 10.0
    precio_max = 50.0

    if precio_min <= truck.precio_conductor_hora <= precio_max:
        return f"✔ (R5) The truck's driver rate (€{truck.precio_conductor_hora}/h) is within acceptable range (€{precio_min}-€{precio_max})."

    return f"✘ (R5) The truck's driver rate (€{truck.precio_conductor_hora}/h) is outside acceptable range (€{precio_min}-€{precio_max})."


# ==================== FORMAT VALIDATION RULES ====================


def validate_nombre_format(data: dict) -> str:
    """Valida el formato del nombre del camión.

    Args:
        data: Diccionario con los datos del camión personalizado

    Returns
    -------
        Mensaje de validación (✔ o ✘)
    """
    nombre = data.get("nombre", "").strip()

    if not nombre:
        return "✘ (Nombre) El nombre del camión no puede estar vacío."

    if len(nombre) < 3:
        return "✘ (Nombre) El nombre debe tener al menos 3 caracteres."

    if len(nombre) > 50:
        return "✘ (Nombre) El nombre no puede exceder 50 caracteres."

    if not re.match(r"^[a-zA-Z0-9\s\-áéíóúÁÉÍÓÚñÑ]+$", nombre):
        return (
            "✘ (Nombre) El nombre contiene caracteres inválidos. "
            "Solo se permiten letras, números, espacios y guiones."
        )

    return f"✔ (Nombre) Formato de nombre válido: '{nombre}'."


def validate_capacidad_format(data: dict) -> str:
    """Valida el formato y rango de la capacidad del camión (en unidades de productos).

    Args:
        data: Diccionario con los datos del camión personalizado

    Returns
    -------
        Mensaje de validación (✔ o ✘)
    """
    capacidad = data.get("capacidad", "")

    if capacidad == "" or capacidad is None:
        return "✘ (Capacidad) La capacidad no puede estar vacía."

    try:
        numero = int(float(capacidad))
    except (ValueError, TypeError):
        return (
            "✘ (Capacidad) Formato de capacidad inválido. "
            "Ingresa solo números enteros (ej: 100 para 100 productos)."
        )

    if numero < 10:
        return "✘ (Capacidad) La capacidad debe ser al menos 10 productos."

    if numero > 200:
        return "✘ (Capacidad) La capacidad no puede exceder 200 productos."

    return f"✔ (Capacidad) Formato de capacidad válido: {numero} productos."


def validate_consumo_format(data: dict) -> str:
    """Valida el formato y rango del consumo del camión.

    Args:
        data: Diccionario con los datos del camión personalizado

    Returns
    -------
        Mensaje de validación (✔ o ✘)
    """
    consumo = data.get("consumo", "")

    if consumo == "" or consumo is None:
        return "✘ (Consumo) El consumo no puede estar vacío."

    try:
        numero = float(consumo) if isinstance(consumo, str) else consumo
    except (ValueError, TypeError):
        return (
            "✘ (Consumo) Formato de consumo inválido. "
            "Ingresa solo números (ej: 30 para 30 L/100km)."
        )

    if numero < 10:
        return "✘ (Consumo) El consumo no puede ser menor a 10 L/100km."

    if numero > 50:
        return "✘ (Consumo) El consumo no puede exceder 50 L/100km."

    return f"✔ (Consumo) Formato de consumo válido: {numero} L/100km."


def validate_velocidad_format(data: dict) -> str:
    """Valida el formato y rango de la velocidad constante del camión.

    Args:
        data: Diccionario con los datos del camión personalizado

    Returns
    -------
        Mensaje de validación (✔ o ✘)
    """
    velocidad = data.get("velocidad_constante", "")

    if velocidad == "" or velocidad is None:
        return "✘ (Velocidad) La velocidad constante no puede estar vacía."

    try:
        numero = float(velocidad) if isinstance(velocidad, str) else velocidad
    except (ValueError, TypeError):
        return (
            "✘ (Velocidad) Formato de velocidad inválido. "
            "Ingresa solo números (ej: 75 para 75 km/h)."
        )

    if numero < 30:
        return "✘ (Velocidad) La velocidad debe ser al menos 30 km/h."

    if numero > 120:
        return "✘ (Velocidad) La velocidad no puede exceder 120 km/h."

    return f"✔ (Velocidad) Formato de velocidad válido: {numero} km/h."


def validate_precio_conductor_hora_format(data: dict) -> str:
    """Valida el formato y rango del precio del conductor por hora.

    Args:
        data: Diccionario con los datos del camión personalizado

    Returns
    -------
        Mensaje de validación (✔ o ✘)
    """
    precio_conductor = data.get("precio_conductor_hora", "")

    if precio_conductor == "" or precio_conductor is None:
        return "✘ (Precio Conductor) El precio del conductor por hora no puede estar vacío."

    try:
        numero = (
            float(precio_conductor)
            if isinstance(precio_conductor, str)
            else precio_conductor
        )
    except (ValueError, TypeError):
        return (
            "✘ (Precio Conductor) Formato de precio inválido. "
            "Ingresa solo números (ej: 15.0 para €15.00/h)."
        )

    if numero < 10.0:
        return "✘ (Precio Conductor) El precio debe ser al menos €10.00/h."

    if numero > 50.0:
        return "✘ (Precio Conductor) El precio no puede exceder €50.00/h."

    return f"✔ (Precio Conductor) Formato de precio válido: €{numero}/h."


def parse_truck_data(data: dict) -> tuple[bool | Truck, dict | Truck]:
    """Transforma datos numéricos a objeto Truck.

    Los datos ya vienen validados, solo necesita convertir a los tipos
    correctos y crear una instancia de Truck.

    Args:
        data: Diccionario con datos del camión (valores numéricos validados)

    Returns
    -------
        Tupla (es_válido, objeto_Truck_o_error)
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
