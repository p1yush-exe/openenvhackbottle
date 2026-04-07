"""
Core ClinicalBench environment.

Implements the OpenEnv interface:
  - reset(seed, episode_id, **kwargs)  -> ClinicalObservation
  - step(action, **kwargs)             -> ClinicalObservation
  - state (property)                   -> ClinicalState
"""

from __future__ import annotations

import os
import random
import uuid
from typing import Any, Optional

from openenv.core.env_server.interfaces import Environment

from ..models import ClinicalAction, ClinicalObservation, ClinicalState
from .sandbox import ExecutionResult, run_code, run_code_with_preamble
from .tasks import TASK_REGISTRY, BaseTask, BiocoderTask

MAX_STEPS = int(os.getenv("MAX_STEPS", "8"))

_CONSEC_FAIL_THRESHOLD = 3
_CONSEC_FAIL_PENALTY = 0.1

TASK_NAMES = ["clinical_calc", "biostat_power", "biocoder"]

DATA_PATH = os.getenv("DATA_PATH", "/app/data")


class ClinicalBenchEnvironment(Environment[ClinicalAction, ClinicalObservation, ClinicalState]):
    """
    OpenEnv environment for biomedical code-generation tasks.

    Three tasks of increasing difficulty:
      clinical_calc   (easy)   -- clinical calculator from patient notes
      biostat_power   (medium) -- statistical power / sample-size problems
      biocoder        (hard)   -- bioinformatics function implementation

    The agent submits Python code; the environment executes it and returns
    a graded observation.  The agent may retry up to MAX_STEPS times.
    """

    SUPPORTS_CONCURRENT_SESSIONS = True

    def __init__(self, data_path: str = DATA_PATH, max_steps: int = MAX_STEPS) -> None:
        super().__init__()
        self._data_path = data_path
        self._max_steps = max_steps

        self._tasks: dict[str, BaseTask] = {
            name: cls(data_path) for name, cls in TASK_REGISTRY.items()
        }

        # Episode state (populated on reset)
        self._episode_id: str = ""
        self._task_name: str = ""
        self._task_index: int = 0
        self._current_item: dict = {}
        self._step_count: int = 0
        self._total_reward: float = 0.0
        self._done: bool = True
        self._consecutive_errors: int = 0
        self._task_description: str = ""

    # ------------------------------------------------------------------
    # OpenEnv interface
    # ------------------------------------------------------------------

    def reset(
        self,
        seed: Optional[int] = None,
        episode_id: Optional[str] = None,
        task_name: Optional[str] = None,
        task_index: Optional[int] = None,
        **kwargs: Any,
    ) -> ClinicalObservation:
        """
        Start a new episode.

        Extra kwargs:
          task_name  (str)  : which task; random if not given.
          task_index (int)  : which problem index; random if not given.
        """
        rng = random.Random(seed)

        self._episode_id = episode_id or str(uuid.uuid4())[:12]
        self._task_name = task_name or rng.choice(TASK_NAMES)

        if self._task_name not in self._tasks:
            raise ValueError(
                f"Unknown task '{self._task_name}'. "
                f"Choose one of: {TASK_NAMES}"
            )

        task = self._tasks[self._task_name]

        if task_index is not None:
            self._task_index = int(task_index) % task.size
        else:
            self._task_index = rng.randint(0, task.size - 1)

        self._current_item = task.get_item(self._task_index)
        self._task_description = task.build_prompt(self._current_item)
        self._step_count = 0
        self._total_reward = 0.0
        self._done = False
        self._consecutive_errors = 0

        return ClinicalObservation(
            task_description=self._task_description,
            execution_result="",
            error=None,
            reward=0.0,
            done=False,
            step_number=0,
            max_steps=self._max_steps,
            metadata={
                "task_name": self._task_name,
                "task_index": self._task_index,
                "difficulty": task.difficulty,
                "episode_id": self._episode_id,
            },
        )

    def step(
        self,
        action: ClinicalAction,
        timeout_s: Optional[float] = None,
        **kwargs: Any,
    ) -> ClinicalObservation:
        """Execute the submitted code and return a graded observation."""
        if self._done:
            raise RuntimeError("Episode is over. Call reset() first.")

        self._step_count += 1
        task = self._tasks[self._task_name]
        item = self._current_item

        # Execute code (biocoder uses context preamble; others run standalone)
        if isinstance(task, BiocoderTask):
            exec_result: ExecutionResult = task.run_with_context(item, action.code)
        else:
            exec_result = run_code(action.code)

        # Grade
        raw_reward = task.grade(item, exec_result)

        # Consecutive-failure penalty
        if raw_reward <= 0.1:
            self._consecutive_errors += 1
        else:
            self._consecutive_errors = 0

        if self._consecutive_errors > _CONSEC_FAIL_THRESHOLD:
            raw_reward = max(0.0, raw_reward - _CONSEC_FAIL_PENALTY)

        self._total_reward += raw_reward

        solved = raw_reward >= 1.0
        exhausted = self._step_count >= self._max_steps
        self._done = solved or exhausted

        error_msg: Optional[str] = None
        if exec_result.syntax_error:
            error_msg = exec_result.syntax_error
        elif exec_result.timed_out:
            error_msg = "Execution timed out"
        elif exec_result.stderr.strip():
            error_msg = exec_result.stderr.strip()[:2000]

        return ClinicalObservation(
            task_description=self._task_description,
            execution_result=exec_result.stdout[:4000],
            error=error_msg,
            reward=raw_reward,
            done=self._done,
            step_number=self._step_count,
            max_steps=self._max_steps,
            metadata={
                "task_name": self._task_name,
                "task_index": self._task_index,
                "difficulty": task.difficulty,
                "episode_id": self._episode_id,
                "solved": solved,
                "consecutive_errors": self._consecutive_errors,
                "total_reward": self._total_reward,
            },
        )

    @property
    def state(self) -> ClinicalState:
        """Return current episode state metadata."""
        return ClinicalState(
            episode_id=self._episode_id,
            task_name=self._task_name,
            task_index=self._task_index,
            step_count=self._step_count,
            total_reward=self._total_reward,
            done=self._done,
        )
