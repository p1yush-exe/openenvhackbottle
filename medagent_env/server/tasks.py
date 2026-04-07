"""
Task registry for the MedAgent Environment.

Cases are loaded from SQLite (server/data/medagent.db).  Run server/seed_db.py
once to create the database before starting the server (the Dockerfile does
this automatically at build time).

Three task families of increasing difficulty:
  1. vital_triage      (easy)   – classify patient as stable / concerning / critical
  2. news2_score       (medium) – compute National Early Warning Score 2 total
  3. medication_dosing (hard)   – determine antibiotic renal dose adjustment
"""

import json
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

DB_PATH = Path(__file__).parent / "data" / "medagent.db"


# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------

def _load_cases(table: str, db_path: Path = DB_PATH) -> List[Dict[str, Any]]:
    """Load all rows from *table* and deserialise the JSON fields blob."""
    if not db_path.exists():
        # Fall back to seeding on first access so the server is self-healing
        from server.seed_db import seed as _seed  # noqa: PLC0415
        _seed(db_path)

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute(f"SELECT * FROM {table}")  # noqa: S608
    rows = cur.fetchall()
    conn.close()

    cases = []
    for row in rows:
        record = dict(row)
        record["fields"] = json.loads(record["fields"])
        cases.append(record)
    return cases


# ---------------------------------------------------------------------------
# Graders
# ---------------------------------------------------------------------------

def grade_vital_triage(answer: str, case: Dict[str, Any]) -> Tuple[float, str]:
    """Score 0.0-1.0 for vital-triage answer."""
    correct = case["answer"]
    if answer.strip().lower() == correct:
        return 1.0, f"Correct! Triage category is '{correct}'."
    adjacents = {
        ("concerning", "critical"), ("critical", "concerning"),
        ("stable", "concerning"), ("concerning", "stable"),
    }
    if (answer.strip().lower(), correct) in adjacents:
        return 0.3, f"Partially correct. You chose '{answer}' but the answer is '{correct}'."
    return 0.0, f"Incorrect. You chose '{answer}' but the answer is '{correct}'."


def grade_news2(answer: str, case: Dict[str, Any]) -> Tuple[float, str]:
    """Score 0.0-1.0 for NEWS2 score answer."""
    correct = case["total_news2"]
    try:
        predicted = int(answer.strip())
    except ValueError:
        return 0.0, f"Answer must be an integer. Got: '{answer}'."
    diff = abs(predicted - correct)
    if diff == 0:
        return 1.0, f"Correct! NEWS2 score is {correct}."
    elif diff == 1:
        return 0.7, f"Close. You scored {predicted}, correct is {correct} (±1)."
    elif diff == 2:
        return 0.4, f"Partial. You scored {predicted}, correct is {correct} (±2)."
    return 0.0, f"Incorrect. You scored {predicted}, correct is {correct}."


VALID_DOSING_ANSWERS = ["normal_dose", "dose_75", "dose_50", "contraindicated"]


def grade_medication_dosing(answer: str, case: Dict[str, Any]) -> Tuple[float, str]:
    """Score 0.0-1.0 for renal dose-adjustment answer."""
    correct = case["answer"]
    norm = answer.strip().lower().replace("-", "_")
    if norm == correct:
        return 1.0, f"Correct! {case['rule_applied']}"
    if norm not in VALID_DOSING_ANSWERS:
        return 0.0, (
            f"Invalid answer '{answer}'. "
            f"Choose from: {', '.join(VALID_DOSING_ANSWERS)}."
        )
    order = ["normal_dose", "dose_75", "dose_50", "contraindicated"]
    if correct in order and norm in order:
        diff = abs(order.index(norm) - order.index(correct))
        if diff == 1:
            return 0.3, (
                f"Partially correct. You chose '{norm}', correct is '{correct}'. "
                f"Hint: {case['rule_applied']}"
            )
    return 0.0, (
        f"Incorrect. You chose '{norm}', correct is '{correct}'. "
        f"Hint: {case['rule_applied']}"
    )


# ---------------------------------------------------------------------------
# Critical fields per task (used for progressive reward shaping)
# ---------------------------------------------------------------------------

CRITICAL_FIELDS: Dict[str, List[str]] = {
    "vital_triage": [
        "spo2_percent", "systolic_bp", "heart_rate",
        "respiratory_rate", "consciousness",
    ],
    "news2_score": [
        "respiratory_rate", "spo2_percent", "on_supplemental_oxygen",
        "systolic_bp", "heart_rate", "consciousness", "temperature_celsius",
    ],
    "medication_dosing": [
        "egfr_ml_min", "drug", "dialysis",
    ],
}


# ---------------------------------------------------------------------------
# Lazy-loaded case lists (populated on first access)
# ---------------------------------------------------------------------------

_case_cache: Dict[str, Optional[List[Dict[str, Any]]]] = {
    "vital_triage": None,
    "news2_score": None,
    "medication_dosing": None,
}


def get_cases(task_type: str) -> List[Dict[str, Any]]:
    """Return cases for *task_type*, loading from SQLite on first call."""
    if _case_cache[task_type] is None:
        table_map = {
            "vital_triage": "vital_triage_cases",
            "news2_score": "news2_cases",
            "medication_dosing": "medication_dosing_cases",
        }
        _case_cache[task_type] = _load_cases(table_map[task_type])
    return _case_cache[task_type]  # type: ignore[return-value]


# ---------------------------------------------------------------------------
# Task registry
# ---------------------------------------------------------------------------

TASK_REGISTRY: Dict[str, Dict[str, Any]] = {
    "vital_triage": {
        "difficulty": "easy",
        "description": (
            "Assess the patient's vital signs and determine the triage category. "
            "Query individual vital fields, then submit one of: "
            "'stable', 'concerning', or 'critical'."
        ),
        "get_cases": lambda: get_cases("vital_triage"),
        "valid_answers": ["stable", "concerning", "critical"],
        "grader": grade_vital_triage,
        "critical_fields": CRITICAL_FIELDS["vital_triage"],
        "max_steps": 10,
    },
    "news2_score": {
        "difficulty": "medium",
        "description": (
            "Calculate the National Early Warning Score 2 (NEWS2) for the patient. "
            "Query all relevant vital fields, compute each component score, "
            "then submit the total as an integer string (e.g. '7')."
        ),
        "get_cases": lambda: get_cases("news2_score"),
        "valid_answers": None,
        "grader": grade_news2,
        "critical_fields": CRITICAL_FIELDS["news2_score"],
        "max_steps": 14,
    },
    "medication_dosing": {
        "difficulty": "hard",
        "description": (
            "Determine the appropriate renal dose adjustment for the prescribed antibiotic. "
            "Query eGFR, drug name, and any other relevant fields, "
            "then submit one of: 'normal_dose', 'dose_75', 'dose_50', 'contraindicated'."
        ),
        "get_cases": lambda: get_cases("medication_dosing"),
        "valid_answers": VALID_DOSING_ANSWERS,
        "grader": grade_medication_dosing,
        "critical_fields": CRITICAL_FIELDS["medication_dosing"],
        "max_steps": 14,
    },
}

# Deterministic episode task rotation
TASK_CYCLE = ["vital_triage", "news2_score", "medication_dosing"]
