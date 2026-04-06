"""Pydantic models for the MedAgent Environment."""

from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel


class MedAgentAction(BaseModel):
    """
    Action the agent takes in the medical assessment environment.

    action_type:
        - "query"   : Request a specific patient data field (use `field`)
        - "calculate": Evaluate a simple arithmetic expression (use `expression`)
        - "submit"  : Submit the final answer (use `answer`)
    """

    action_type: Literal["query", "calculate", "submit"]
    field: Optional[str] = None         # for "query"   – name of the field to retrieve
    expression: Optional[str] = None    # for "calculate" – arithmetic string, e.g. "3 + 2"
    answer: Optional[str] = None        # for "submit"  – final answer string
    reasoning: Optional[str] = None     # chain-of-thought (optional, unscored)


class MedAgentObservation(BaseModel):
    """
    Observation returned after each step / reset.
    """

    task_id: str                             # unique episode identifier
    task_type: str                           # "vital_triage" | "news2_score" | "medication_dosing"
    difficulty: str                          # "easy" | "medium" | "hard"
    scenario_description: str               # brief patient scenario text
    available_fields: List[str]             # fields the agent may query
    queried_fields: Dict[str, Any]          # fields retrieved so far this episode
    last_result: str                         # feedback from the last action
    score: float                             # current episode score 0.0–1.0
    done: bool
    reward: Optional[float] = None
    metadata: Dict[str, Any] = {}
