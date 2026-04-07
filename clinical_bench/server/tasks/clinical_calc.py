"""
Easy task -- Clinical Calculator (MedCalcBench).

The agent reads a patient note and a clinical question, then writes Python
code that prints the computed value.  Graded by comparing the printed number
to the ground-truth lower/upper bounds supplied by the dataset.

Partial-credit reward design
-----------------------------
1.0   -- answer within [LowerLimit, UpperLimit]
0.5   -- numeric answer within 2× the tolerance band around ground truth
0.3   -- code runs without error but answer is wrong
0.1   -- code has a syntax error or runtime error (any code attempt counts)
0.0   -- no output produced at all
"""

from __future__ import annotations

from typing import Any

from .base import BaseTask
from ..sandbox import ExecutionResult


_PROMPT_TEMPLATE = """\
You are a clinical data analyst. A patient note is provided below along with a
calculation question. Write Python code that computes the answer and prints
ONLY the final numeric result (no labels, no units).

Use the variable `answer` to hold the result, then call `print(answer)`.

--- PATIENT NOTE ---
{note}

--- QUESTION ---
{question}
"""


class ClinicalCalcTask(BaseTask):
    _data_subdir = "medcalcbench"
    _test_file = "test_tasks.jsonl"
    difficulty = "easy"

    def build_prompt(self, item: dict[str, Any]) -> str:
        return _PROMPT_TEMPLATE.format(
            note=item["Patient Note"],
            question=item["Question"],
        )

    def grade(self, item: dict[str, Any], result: ExecutionResult) -> float:
        if result.syntax_error:
            return 0.1

        output = result.stdout.strip()

        if result.timed_out or not output:
            return 0.0

        if result.stderr.strip() and not output:
            return 0.1

        try:
            pred = float(output.split()[0])
        except (ValueError, IndexError):
            return 0.1

        ground_truth = float(item["Ground Truth Answer"])
        lower = float(item.get("Lower Limit") or ground_truth * 0.95)
        upper = float(item.get("Upper Limit") or ground_truth * 1.05)

        if lower <= pred <= upper:
            return 1.0

        # Partial credit: within 2× the tolerance band
        tolerance = (upper - lower) / 2.0
        if tolerance > 0 and abs(pred - ground_truth) <= 2 * tolerance:
            return 0.5

        # Code ran but answer is numerically wrong
        return 0.3
