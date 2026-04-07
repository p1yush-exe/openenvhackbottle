"""
ClinicalBench typed models.

Action, Observation, and State classes extend the openenv-core base types
so the environment is fully compatible with openenv validate, HTTPEnvServer,
and the openenv Python client.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from openenv.core.env_server.types import Action, Observation, State
from pydantic import Field


class ClinicalAction(Action):
    """Action submitted by the agent: a block of Python code to execute."""

    code: str = Field(..., description="Python code to run in the sandbox")

    model_config = {  # type: ignore[assignment]
        "arbitrary_types_allowed": True,
        "extra": "forbid",
        "validate_assignment": True,
    }


class ClinicalObservation(Observation):
    """Observation returned to the agent after each step or reset."""

    task_description: str = Field(
        ..., description="Full problem text the agent must solve"
    )
    execution_result: str = Field(
        default="", description="stdout captured from the last code execution"
    )
    error: Optional[str] = Field(
        default=None, description="Error message if the last execution failed"
    )
    step_number: int = Field(default=0, description="Current step index (1-based)")
    max_steps: int = Field(default=8, description="Maximum steps per episode")

    # `reward`, `done`, and `metadata` are inherited from Observation

    model_config = {  # type: ignore[assignment]
        "arbitrary_types_allowed": True,
        "extra": "forbid",
        "validate_assignment": True,
    }


class ClinicalState(State):
    """Episode-level state metadata."""

    task_name: str = Field(..., description="One of: clinical_calc, biostat_power, biocoder")
    task_index: int = Field(..., description="Index of the problem within the task dataset")
    total_reward: float = Field(default=0.0, description="Cumulative reward this episode")
    done: bool = Field(default=False, description="True when the episode is over")

    # `episode_id` and `step_count` are inherited from State

    model_config = {  # type: ignore[assignment]
        "arbitrary_types_allowed": True,
        "extra": "allow",
        "validate_assignment": True,
    }
