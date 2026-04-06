# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

"""Data models for the Database Cleaning Environment."""

from openenv.core.env_server.types import Action, Observation
from pydantic import Field


class DatabaseCleaningAction(Action):
    """A cleanup command targeting a specific issue in a table."""

    operation: str = Field(
        ...,
        description="Cleanup operation to perform. Expected values: deduplicate, fill_nulls, remove_orphans.",
    )
    table_name: str = Field(..., description="Table to clean.")
    issue_type: str = Field(
        ...,
        description="Issue category the agent believes it is addressing.",
    )
    rows_to_fix: int = Field(
        ...,
        ge=1,
        description="Number of rows to clean in this step.",
    )


class DatabaseCleaningObservation(Observation):
    """Observation describing the current cleanup state."""

    task_summary: str = Field(default="", description="Short description of the current task.")
    available_tables: list[str] = Field(
        default_factory=list,
        description="Tables available in the current scenario.",
    )
    remaining_issues: dict[str, dict[str, int]] = Field(
        default_factory=dict,
        description="Per-table issue counts that still need cleanup.",
    )
    last_result: str = Field(
        default="",
        description="Human-readable result from the last action.",
    )
    cleaned_rows: int = Field(
        default=0,
        description="Rows cleaned by the last action.",
    )
    total_cleaned_rows: int = Field(
        default=0,
        description="Total rows cleaned in the current episode.",
    )
