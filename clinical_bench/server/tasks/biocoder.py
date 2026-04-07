"""
Hard task -- Bioinformatics Function Implementation (BioCoder).

The agent receives a function specification, a function signature, and
surrounding context code.  It must implement the function body.  Grading
runs the full file (context + solution + main()) and compares stdout to
the reference output from the original solution.

Partial-credit reward design
-----------------------------
1.0  -- stdout matches reference output exactly (after stripping whitespace)
0.6  -- stdout non-empty, ≥ 80 % token overlap with reference output
0.3  -- code runs without error but output doesn't match
0.1  -- syntax error or runtime error
0.0  -- timeout / no output
"""

from __future__ import annotations

import re
from typing import Any

from .base import BaseTask
from ..sandbox import ExecutionResult, run_code_with_preamble


_PROMPT_TEMPLATE = """\
You are a bioinformatics software engineer.

Implement the Python function described below.  Return ONLY the function
body (starting from `def {signature}:`).  Do NOT include import statements
or any code outside the function definition.

--- CONTEXT (do not reproduce this) ---
{context_snippet}

--- FUNCTION SIGNATURE ---
{signature}

--- DESCRIPTION ---
{problem}
"""

_MAX_CONTEXT_CHARS = 3000


def _token_overlap(a: str, b: str) -> float:
    """Jaccard-like token overlap between two strings."""
    tok_a = set(re.split(r"\s+", a.strip()))
    tok_b = set(re.split(r"\s+", b.strip()))
    if not tok_a and not tok_b:
        return 1.0
    if not tok_a or not tok_b:
        return 0.0
    return len(tok_a & tok_b) / len(tok_a | tok_b)


class BiocoderTask(BaseTask):
    _data_subdir = "biocoder"
    _test_file = "test_tasks.jsonl"
    difficulty = "hard"

    def build_prompt(self, item: dict[str, Any]) -> str:
        context = item.get("context", "")
        # Truncate very long context to keep prompts manageable
        if len(context) > _MAX_CONTEXT_CHARS:
            context = context[:_MAX_CONTEXT_CHARS] + "\n... (truncated)"
        return _PROMPT_TEMPLATE.format(
            signature=item["signature"],
            context_snippet=context,
            problem=item["problem"],
        )

    def grade(self, item: dict[str, Any], result: ExecutionResult) -> float:
        if result.syntax_error:
            return 0.1

        if result.timed_out:
            return 0.0

        if not result.stdout.strip():
            return 0.0 if not result.stderr.strip() else 0.1

        # Get the reference output by running the reference solution
        ref_result = run_code_with_preamble(
            preamble=item["context"],
            solution_code=item["solution"],
            timeout=30,
        )
        ref_output = ref_result.stdout.strip()

        pred_output = result.stdout.strip()

        if pred_output == ref_output:
            return 1.0

        overlap = _token_overlap(pred_output, ref_output)
        if overlap >= 0.80:
            return 0.6

        # Code ran but output doesn't match
        return 0.3

    def run_with_context(
        self, item: dict[str, Any], agent_solution: str
    ) -> ExecutionResult:
        """Run agent_solution embedded in the task's context code."""
        return run_code_with_preamble(
            preamble=item["context"],
            solution_code=agent_solution,
            timeout=30,
        )
