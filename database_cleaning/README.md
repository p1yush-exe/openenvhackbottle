---
title: Database Cleaning Environment Server
emoji: "Database"
colorFrom: pink
colorTo: red
sdk: docker
pinned: false
app_port: 8000
base_path: /web
tags:
  - openenv
---

# Database Cleaning Environment

This OpenEnv environment simulates a small relational database with common data hygiene problems. The agent must inspect the remaining issues and choose cleanup actions that target the correct table, issue type, and number of rows.

## Scenario

The default episode includes three tables with seeded issues:

- `customers`: duplicate rows and null emails
- `payments`: orphaned payments
- `sessions`: stale session records

Episodes end when all issues are resolved or the agent reaches the step limit.

## Action Schema

`DatabaseCleaningAction` contains:

- `operation`: one of `deduplicate`, `fill_nulls`, or `remove_orphans`
- `table_name`: target table name
- `issue_type`: target issue category within that table
- `rows_to_fix`: number of rows to clean in the current step

## Observation Schema

`DatabaseCleaningObservation` contains:

- `task_summary`: objective for the episode
- `available_tables`: tables present in the scenario
- `remaining_issues`: unresolved issue counts per table
- `last_result`: result of the previous action
- `cleaned_rows`: rows cleaned by the previous action
- `total_cleaned_rows`: cumulative rows cleaned in the episode

## Reward Logic

- Valid cleanup earns reward equal to rows cleaned.
- Over-cleaning applies a penalty for extra rows attempted.
- Wrong operations, missing tables, and missing issues produce negative reward.
- Resolving all issues grants a completion bonus.

## Example

```python
from database_cleaning import DatabaseCleaningAction, DatabaseCleaningEnv

with DatabaseCleaningEnv(base_url="http://localhost:8000") as env:
    result = env.reset()
    print(result.observation.remaining_issues)

    result = env.step(
        DatabaseCleaningAction(
            operation="deduplicate",
            table_name="customers",
            issue_type="duplicate_rows",
            rows_to_fix=4,
        )
    )

    print(result.observation.last_result)
    print(result.reward)
```

## Local Development

Validate the environment:

```bash
openenv validate
```

Run the API locally:

```bash
uvicorn server.app:app --reload
```

Build the Docker image:

```bash
docker build -t database_cleaning-env:latest -f server/Dockerfile .
```
