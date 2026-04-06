# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

"""Database Cleaning Environment Implementation."""

from uuid import uuid4

from openenv.core.env_server.interfaces import Environment
from openenv.core.env_server.types import State

try:
    from ..models import DatabaseCleaningAction, DatabaseCleaningObservation
except ImportError:
    from models import DatabaseCleaningAction, DatabaseCleaningObservation


class DatabaseCleaningEnvironment(Environment):
    """A small simulated environment for database hygiene tasks."""

    SUPPORTS_CONCURRENT_SESSIONS: bool = True
    MAX_STEPS: int = 6
    EXPECTED_OPERATIONS: dict[str, str] = {
        "duplicate_rows": "deduplicate",
        "null_emails": "fill_nulls",
        "orphaned_payments": "remove_orphans",
        "stale_sessions": "deduplicate",
    }
    INITIAL_ISSUES: dict[str, dict[str, int]] = {
        "customers": {"duplicate_rows": 7, "null_emails": 4},
        "payments": {"orphaned_payments": 5},
        "sessions": {"stale_sessions": 6},
    }

    def __init__(self):
        self._state = State(episode_id=str(uuid4()), step_count=0)
        self._issues = {}
        self._total_cleaned_rows = 0

    def _task_summary(self) -> str:
        return (
            "Clean all table issues with the fewest mistakes possible. "
            "Match each issue to the right operation and avoid over-cleaning."
        )

    def _remaining_issue_total(self) -> int:
        return sum(count for table in self._issues.values() for count in table.values())

    def _snapshot(self) -> dict[str, dict[str, int]]:
        return {
            table: {issue: count for issue, count in issues.items() if count > 0}
            for table, issues in self._issues.items()
            if any(count > 0 for count in issues.values())
        }

    def _observation(
        self,
        last_result: str,
        cleaned_rows: int,
        reward: float,
        done: bool,
    ) -> DatabaseCleaningObservation:
        return DatabaseCleaningObservation(
            task_summary=self._task_summary(),
            available_tables=sorted(self._issues.keys()),
            remaining_issues=self._snapshot(),
            last_result=last_result,
            cleaned_rows=cleaned_rows,
            total_cleaned_rows=self._total_cleaned_rows,
            done=done,
            reward=reward,
            metadata={
                "step": self._state.step_count,
                "remaining_issue_total": self._remaining_issue_total(),
                "max_steps": self.MAX_STEPS,
            },
        )

    def reset(self) -> DatabaseCleaningObservation:
        self._state = State(episode_id=str(uuid4()), step_count=0)
        self._issues = {
            table: issues.copy() for table, issues in self.INITIAL_ISSUES.items()
        }
        self._total_cleaned_rows = 0
        return self._observation(
            last_result=(
                "New database loaded. Review remaining issues and choose targeted cleanup operations."
            ),
            cleaned_rows=0,
            reward=0.0,
            done=False,
        )

    def step(self, action: DatabaseCleaningAction) -> DatabaseCleaningObservation:  # type: ignore[override]
        self._state.step_count += 1
        table_issues = self._issues.get(action.table_name)
        if table_issues is None:
            return self._observation(
                last_result=f"Unknown table '{action.table_name}'.",
                cleaned_rows=0,
                reward=-2.0,
                done=self._state.step_count >= self.MAX_STEPS,
            )

        if action.issue_type not in table_issues:
            return self._observation(
                last_result=(
                    f"Issue '{action.issue_type}' is not present on table '{action.table_name}'."
                ),
                cleaned_rows=0,
                reward=-1.5,
                done=self._state.step_count >= self.MAX_STEPS,
            )

        remaining = table_issues[action.issue_type]
        expected_operation = self.EXPECTED_OPERATIONS.get(action.issue_type)
        if action.operation != expected_operation:
            return self._observation(
                last_result=(
                    f"Wrong operation '{action.operation}' for issue '{action.issue_type}'. "
                    f"Expected '{expected_operation}'."
                ),
                cleaned_rows=0,
                reward=-1.0,
                done=self._state.step_count >= self.MAX_STEPS,
            )

        cleaned_rows = min(action.rows_to_fix, remaining)
        overreach = max(action.rows_to_fix - remaining, 0)
        table_issues[action.issue_type] = max(remaining - action.rows_to_fix, 0)
        self._total_cleaned_rows += cleaned_rows

        reward = float(cleaned_rows) - (0.5 * overreach)
        done = self._remaining_issue_total() == 0 or self._state.step_count >= self.MAX_STEPS
        if overreach:
            last_result = (
                f"Cleaned {cleaned_rows} rows in {action.table_name}.{action.issue_type}, "
                f"but attempted {overreach} extra rows."
            )
        else:
            last_result = (
                f"Cleaned {cleaned_rows} rows in {action.table_name}.{action.issue_type} "
                f"using {action.operation}."
            )

        if done and self._remaining_issue_total() == 0:
            reward += 5.0
            last_result += " All issues resolved."

        return self._observation(
            last_result=last_result,
            cleaned_rows=cleaned_rows,
            reward=reward,
            done=done,
        )

    @property
    def state(self) -> State:
        return self._state
