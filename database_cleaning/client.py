# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

"""Database Cleaning Environment Client."""

from typing import Dict

from openenv.core import EnvClient
from openenv.core.client_types import StepResult
from openenv.core.env_server.types import State

from .models import DatabaseCleaningAction, DatabaseCleaningObservation


class DatabaseCleaningEnv(
    EnvClient[DatabaseCleaningAction, DatabaseCleaningObservation, State]
):
    """Client for the Database Cleaning Environment."""

    def _step_payload(self, action: DatabaseCleaningAction) -> Dict:
        return {
            "operation": action.operation,
            "table_name": action.table_name,
            "issue_type": action.issue_type,
            "rows_to_fix": action.rows_to_fix,
        }

    def _parse_result(self, payload: Dict) -> StepResult[DatabaseCleaningObservation]:
        obs_data = payload.get("observation", {})
        observation = DatabaseCleaningObservation(
            task_summary=obs_data.get("task_summary", ""),
            available_tables=obs_data.get("available_tables", []),
            remaining_issues=obs_data.get("remaining_issues", {}),
            last_result=obs_data.get("last_result", ""),
            cleaned_rows=obs_data.get("cleaned_rows", 0),
            total_cleaned_rows=obs_data.get("total_cleaned_rows", 0),
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
