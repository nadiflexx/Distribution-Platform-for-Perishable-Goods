from __future__ import annotations

from pydantic import BaseModel
from typing import List

"""Model of the result returned by the inference engine.

Contains the decision (`is_valid`) and the reasoning chain as a
list of messages produced by each applied rule.
"""


class ResultValidation(BaseModel):
    is_valid: bool
    reasoning: List[str]
