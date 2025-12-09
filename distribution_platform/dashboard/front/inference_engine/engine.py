from __future__ import annotations

from collections.abc import Callable, Iterable

from data_models.result_validation import ResultValidation
from data_models.truck import Truck

"""Inference motor for the expert system.

This module exposes the `MotorInferencia` class which receives a collection of
rules-functions. Each rule receives a `Truck` object and returns a
message string. The engine executes the rules in order and builds
a list of messages that form the reasoning chain.
"""


class InferenceMotor:
    """Simple rule-based inference engine.

    Args:
        reglas: Iterable of callables with the signature (Truck) -> str.
    """

    def __init__(self, rules: Iterable[Callable[[Truck], str]]):
        self.rules = list(rules)

    def evaluate(self, truck: Truck) -> ResultValidation:
        """Evaluates a truck by applying all the rules and returns the
        `ResultValidation`.

        The representation of the reasoning is a list of strings. The
        criterion for validity is that no rule returns a message that
        starts with "✘".
        """

        reasoning: list[str] = []

        for rule in self.rules:
            message = rule(truck)
            reasoning.append(message)

        is_valid = all(not message.startswith("✘") for message in reasoning)

        return ResultValidation(is_valid=is_valid, reasoning=reasoning)
