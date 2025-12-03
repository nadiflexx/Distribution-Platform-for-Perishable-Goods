"""Rules of the expert system for invoice validation.

Every rule is a function that receives a `Truck` object and returns a
ca with the validation result. Messages start with
"✔" for conditions met or "✘" for failures; this is consumed by
the `InferenceEngine` to generate the final decision.
"""

from collections.abc import Callable
from typing import List
from distribution_platform.dashboard.front.data_models.truck import Truck


def print_rules() -> List[str]:
    """Returns the human-readable list of business rules.

    Used by the UI to display the available rules.
    """
    return [
        "- The csv file must contain all required fields.",
        "- The truck selected must have enough capacity for the delivery.",
        "- The truck selected must have an acceptable fuel consumpion rate.",
        "- The truck selected must have a constant velocity during tthe route.",
    ]


def obtain_rules() -> List[Callable[[Truck], str]]:
    """Returns the list of rule functions to be executed by the engine.

    Maintain the order of the rules for predictable output.
    """
    return [
        velocity_rule,
        consumption_rule,
        capacity_rule,
    ]


def velocity_rule(truck: Truck) -> str:
    """R1: The truck's velocity must be constant during the route."""
    if truck.velocidad_constante:
        return "✔ (R1) The truck's velocity is constant during the route."

    return "✘ (R1) The truck's velocity is not constant during the route."


def consumption_rule(truck: Truck) -> str:
    """R2: The truck's fuel consumption must be within acceptable limits."""
    if truck.consumo_combustible <= truck.limite_consumo:
        return "✔ (R2) The truck's fuel consumption is within acceptable limits."

    return "✘ (R2) The truck's fuel consumption exceeds acceptable limits."


def capacity_rule(truck: Truck) -> str:
    """R3: The truck must have sufficient capacity for the load."""
    if truck.capacidad_carga >= truck.carga_requerida:
        return "✔ (R3) The truck has sufficient capacity for the load."

    return "✘ (R3) The truck does not have sufficient capacity for the load."
