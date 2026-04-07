"""Pydantic models for the MedAgent Environment."""

from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field


class MedAgentAction(BaseModel):
    """
    Action the agent takes in the medical assessment environment.

    action_type:
        "query"     – request a specific patient data field (set `field`)
        "calculate" – evaluate a simple arithmetic expression (set `expression`)
        "submit"    – submit the final answer (set `answer`)
    """

    action_type: Literal["query", "calculate", "submit"]
    field: Optional[str] = None         # for "query"     – name of field to retrieve
    expression: Optional[str] = None    # for "calculate" – arithmetic string, e.g. "3+2"
    answer: Optional[str] = None        # for "submit"    – final answer string
    reasoning: Optional[str] = None     # chain-of-thought (optional, unscored)


class MedAgentObservation(BaseModel):
    """
    Observation returned after each /reset or /step call.

    metadata keys:
        step                  – current step count (int)
        max_steps             – episode step budget (int)
        task_description      – plain-English task instructions (str)
        valid_answers         – list of valid answer strings, or null (list|null)
        case_id               – database case identifier (int)
        information_coverage  – fraction of critical fields queried  (float 0–1)
        efficiency_score      – 1 – (steps_used / max_steps), clamped  (float 0–1)
        ready_to_submit       – True once coverage >= 60% of critical fields (bool)
        suggestion            – hint from the environment on what to query next (str)
        cumulative_reward     – sum of step-level rewards so far (float)
    """

    task_id: str                              # unique episode identifier
    task_type: str                            # "vital_triage"|"news2_score"|"medication_dosing"
    difficulty: str                           # "easy"|"medium"|"hard"
    scenario_description: str                # brief patient scenario text
    available_fields: List[str]              # field names the agent may query
    queried_fields: Dict[str, Any]           # field values retrieved this episode
    last_result: str                          # feedback from the last action
    score: float                              # final episode score 0.0–1.0 (set on submit)
    done: bool                                # True when the episode has ended
    reward: Optional[float] = None           # step-level reward signal
    metadata: Dict[str, Any] = Field(default_factory=dict)  # extended context
