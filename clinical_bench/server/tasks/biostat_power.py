"""
Medium task -- Biostatistical Power Analysis (NPowerAI).

The agent reads a study design description and writes Python code that
calculates either the required sample size (integer) or the statistical
power (float in [0, 1]).

Partial-credit reward design
-----------------------------
1.0  -- exact correct answer (size: exact int; power: within ±1 %)
0.5  -- correct answer type but off by ≤10 % (size: within 10 %; power: within 10 %)
0.3  -- code runs, produces a number, but answer is wrong
0.1  -- code has a syntax error or runtime error
0.0  -- no output / timeout
"""

from __future__ import annotations

from typing import Any

from .base import BaseTask
from ..sandbox import ExecutionResult


_PROMPT_TEMPLATE = """\
You are a biostatistician. Solve the following statistical problem by writing
Python code. Print ONLY the final numeric answer (no labels, no units).

For sample-size questions print an integer.
For power questions print a float rounded to 4 decimal places.

Use `answer` to store the result, then call `print(answer)`.

--- PROBLEM ---
{question}
"""


class BiostatPowerTask(BaseTask):
    _data_subdir = "npowerai"
    _test_file = "test_tasks.jsonl"
    difficulty = "medium"

    def build_prompt(self, item: dict[str, Any]) -> str:
        return _PROMPT_TEMPLATE.format(question=item["question"])

    def grade(self, item: dict[str, Any], result: ExecutionResult) -> float:
        if result.syntax_error:
            return 0.1

        output = result.stdout.strip()

        if result.timed_out or not output:
            return 0.0

        if result.stderr.strip() and not output:
            return 0.1

        estimate_target = item.get("estimate_target", "size")
        answer = item["answer"]

        try:
            raw = output.split()[0]
            if estimate_target == "size":
                pred = int(float(raw))
                gt = int(answer)
                if pred == gt:
                    return 1.0
                if gt != 0 and abs(pred - gt) / gt <= 0.10:
                    return 0.5
                return 0.3
            else:
                pred = float(raw)
                gt = float(answer)
                if gt == 0:
                    return 1.0 if pred == 0 else 0.3
                if abs(pred - gt) / gt <= 0.01:
                    return 1.0
                if abs(pred - gt) / gt <= 0.10:
                    return 0.5
                return 0.3
        except (ValueError, ZeroDivisionError):
            return 0.1
