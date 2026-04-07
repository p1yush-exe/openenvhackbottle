"""Sandboxed Python code execution with timeout and basic resource limits."""

from __future__ import annotations

import ast
import os
import subprocess
import sys
import tempfile
import textwrap
from dataclasses import dataclass
from typing import Optional


EXECUTION_TIMEOUT_SECONDS = 30


@dataclass
class ExecutionResult:
    stdout: str
    stderr: str
    timed_out: bool
    syntax_error: Optional[str]

    @property
    def success(self) -> bool:
        return not self.timed_out and not self.syntax_error and not self.stderr.strip()

    @property
    def has_output(self) -> bool:
        return bool(self.stdout.strip())


def check_syntax(code: str) -> Optional[str]:
    """Return None if code is syntactically valid, or an error string."""
    try:
        ast.parse(code)
        return None
    except SyntaxError as exc:
        return f"SyntaxError on line {exc.lineno}: {exc.msg}"


def run_code(
    code: str,
    timeout: int = EXECUTION_TIMEOUT_SECONDS,
    extra_env: Optional[dict] = None,
) -> ExecutionResult:
    """
    Execute `code` in a subprocess and return stdout/stderr.

    The subprocess inherits a clean environment so no credentials or
    host-system paths leak in.  We cap wall-clock time via `timeout`.
    """
    syntax_err = check_syntax(code)
    if syntax_err:
        return ExecutionResult(
            stdout="", stderr="", timed_out=False, syntax_error=syntax_err
        )

    env = {
        "PATH": "/usr/local/bin:/usr/bin:/bin",
        "PYTHONPATH": "",
        "HOME": tempfile.gettempdir(),
    }
    if extra_env:
        env.update(extra_env)

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".py", delete=False, encoding="utf-8"
    ) as fh:
        fh.write(code)
        tmp_path = fh.name

    try:
        proc = subprocess.run(
            [sys.executable, tmp_path],
            capture_output=True,
            text=True,
            timeout=timeout,
            env=env,
        )
        return ExecutionResult(
            stdout=proc.stdout,
            stderr=proc.stderr,
            timed_out=False,
            syntax_error=None,
        )
    except subprocess.TimeoutExpired:
        return ExecutionResult(
            stdout="", stderr="", timed_out=True, syntax_error=None
        )
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass


def run_code_with_preamble(
    preamble: str,
    solution_code: str,
    timeout: int = EXECUTION_TIMEOUT_SECONDS,
) -> ExecutionResult:
    """
    Prepend `preamble` (context / helper code) to `solution_code`, then run.

    The solution replaces a ``<<insert solution here>>`` marker if present,
    otherwise the solution is appended after the preamble.
    """
    MARKER = "<<insert solution here>>"
    if MARKER in preamble:
        full_code = preamble.replace(MARKER, solution_code)
    else:
        full_code = preamble + "\n\n" + solution_code
    return run_code(full_code, timeout=timeout)
