"""Abstract base class for all ClinicalBench tasks."""

from __future__ import annotations

import json
import os
from abc import ABC, abstractmethod
from typing import Any

from ..sandbox import ExecutionResult


class BaseTask(ABC):
    """
    A task loads problems from a JSONL file and grades code submissions.

    Subclasses implement:
      - ``_data_subdir``: subdirectory name under the env ``data_path``
      - ``_load_item(idx)``: return a single problem dict
      - ``build_prompt(item)``: return the problem text shown to the agent
      - ``grade(item, result)``: return a reward float in [0.0, 1.0]
    """

    #: Relative data subdirectory (e.g. "medcalcbench")
    _data_subdir: str = ""
    #: JSONL filename inside the subdirectory
    _test_file: str = "test_tasks.jsonl"
    #: Human-readable difficulty label
    difficulty: str = "medium"

    def __init__(self, data_path: str) -> None:
        self._data_path = data_path
        self._items: list[dict[str, Any]] | None = None

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------

    @property
    def size(self) -> int:
        return len(self._load_all())

    def get_item(self, idx: int) -> dict[str, Any]:
        items = self._load_all()
        return items[idx % len(items)]

    def build_prompt(self, item: dict[str, Any]) -> str:  # pragma: no cover
        raise NotImplementedError

    def grade(self, item: dict[str, Any], result: ExecutionResult) -> float:
        """Return reward in [0.0, 1.0] for the given execution result."""
        raise NotImplementedError

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _load_all(self) -> list[dict[str, Any]]:
        if self._items is not None:
            return self._items
        path = os.path.join(self._data_path, self._data_subdir, self._test_file)
        items: list[dict[str, Any]] = []
        with open(path, "r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    items.append(json.loads(line))
        self._items = items
        return self._items
