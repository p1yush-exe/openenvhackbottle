"""MedAgent Environment Client."""

from typing import Dict

from openenv.core import EnvClient
from openenv.core.client_types import StepResult
from openenv.core.env_server.types import State

try:
    from .models import MedAgentAction, MedAgentObservation
except ImportError:
    from models import MedAgentAction, MedAgentObservation


class MedAgentEnv(EnvClient[MedAgentAction, MedAgentObservation, State]):
    """HTTP client for the MedAgent Environment."""

    def _step_payload(self, action: MedAgentAction) -> Dict:
        return {
            "action_type": action.action_type,
            "field": action.field,
            "expression": action.expression,
            "answer": action.answer,
            "reasoning": action.reasoning,
        }

    def _parse_result(self, payload: Dict) -> StepResult[MedAgentObservation]:
        obs_data = payload.get("observation", {})
        observation = MedAgentObservation(
            task_id=obs_data.get("task_id", ""),
            task_type=obs_data.get("task_type", ""),
            difficulty=obs_data.get("difficulty", ""),
            scenario_description=obs_data.get("scenario_description", ""),
            available_fields=obs_data.get("available_fields", []),
            queried_fields=obs_data.get("queried_fields", {}),
            last_result=obs_data.get("last_result", ""),
            score=obs_data.get("score", 0.0),
            done=payload.get("done", False),
            reward=payload.get("reward"),
            metadata=obs_data.get("metadata", {}),
        )
        return StepResult(
            observation=observation,
            reward=payload.get("reward"),
            done=payload.get("done", False),
        )

    def _parse_state(self, payload: Dict) -> State:
        return State(
            episode_id=payload.get("episode_id"),
            step_count=payload.get("step_count", 0),
        )
