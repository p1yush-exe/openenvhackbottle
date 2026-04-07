"""
MedAgent Environment — OpenEnv Environment implementation.

Three task families cycle deterministically across episodes:
  Episode 1 → vital_triage      (easy)
  Episode 2 → news2_score       (medium)
  Episode 3 → medication_dosing (hard)
  Episode 4 → vital_triage      … and so on

Reward shaping follows the MedAgentGym pattern:
  - Relevant-field query  → +0.10 (first query of a critical field)
  - Duplicate query       → +0.00
  - Irrelevant field query → +0.03
  - Missing field name    → -0.05
  - Unknown field         → -0.10
  - Calculation success   → +0.00 (neutral; agent does its own arithmetic)
  - Calculation error     → -0.05
  - Coverage bonus        → +0.10  once >= 60% of critical fields queried
  - Submit correct        → 1.0
  - Submit partial        → grader-assigned (0.0–<1.0)
"""

import ast
import operator
import random
from typing import Optional
from uuid import uuid4

from openenv.core.env_server.interfaces import Environment
from openenv.core.env_server.types import State

try:
    from ..models import MedAgentAction, MedAgentObservation
    from .tasks import TASK_REGISTRY, TASK_CYCLE
except ImportError:
    from models import MedAgentAction, MedAgentObservation
    from server.tasks import TASK_REGISTRY, TASK_CYCLE


# ---------------------------------------------------------------------------
# Safe arithmetic evaluator
# ---------------------------------------------------------------------------

_SAFE_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
}


def _safe_eval(expr: str) -> float:
    try:
        tree = ast.parse(expr, mode="eval")
    except SyntaxError as exc:
        raise ValueError(f"Syntax error in expression: {exc}") from exc

    def _eval(node):
        if isinstance(node, ast.Expression):
            return _eval(node.body)
        if isinstance(node, ast.Constant):
            return float(node.value)
        if isinstance(node, ast.BinOp):
            op_type = type(node.op)
            if op_type not in _SAFE_OPS:
                raise ValueError(f"Unsupported operator: {op_type.__name__}")
            return _SAFE_OPS[op_type](_eval(node.left), _eval(node.right))
        if isinstance(node, ast.UnaryOp):
            op_type = type(node.op)
            if op_type not in _SAFE_OPS:
                raise ValueError(f"Unsupported operator: {op_type.__name__}")
            return _SAFE_OPS[op_type](_eval(node.operand))
        raise ValueError(f"Unsupported AST node: {type(node).__name__}")

    return _eval(tree)


# ---------------------------------------------------------------------------
# Environment
# ---------------------------------------------------------------------------

_COVERAGE_THRESHOLD = 0.6   # fraction of critical fields needed for bonus
_COVERAGE_BONUS = 0.10       # one-time bonus when threshold is crossed
_CRITICAL_FIELD_REWARD = 0.10
_IRRELEVANT_FIELD_REWARD = 0.03


class MedAgentEnvironment(Environment):
    """
    Medical clinical assessment environment (OpenEnv-compliant).

    Exposes /reset, /step, /state, /schema, and /ws endpoints via openenv-core.
    """

    SUPPORTS_CONCURRENT_SESSIONS: bool = True
    _global_episode_count: int = 0

    def __init__(self):
        self._state = State(episode_id=str(uuid4()), step_count=0)
        self._task_type: str = ""
        self._task_cfg: dict = {}
        self._case: dict = {}
        self._queried: dict = {}
        self._score: float = 0.0
        self._done: bool = False
        self._coverage_bonus_given: bool = False
        self._cumulative_reward: float = 0.0

    # ------------------------------------------------------------------
    # OpenEnv interface
    # ------------------------------------------------------------------

    def reset(
        self,
        seed: Optional[int] = None,
        episode_id: Optional[str] = None,
        **kwargs,
    ) -> MedAgentObservation:
        if seed is not None:
            random.seed(seed)

        MedAgentEnvironment._global_episode_count += 1
        idx = (MedAgentEnvironment._global_episode_count - 1) % len(TASK_CYCLE)
        self._task_type = TASK_CYCLE[idx]
        self._task_cfg = TASK_REGISTRY[self._task_type]

        cases = self._task_cfg["get_cases"]()
        self._case = random.choice(cases)

        self._state = State(episode_id=episode_id or str(uuid4()), step_count=0)
        self._queried = {}
        self._score = 0.0
        self._done = False
        self._coverage_bonus_given = False
        self._cumulative_reward = 0.0

        return self._build_obs(
            last_result=(
                "New episode started. Read the patient scenario, query the fields "
                "you need, then submit your answer."
            ),
            reward=0.0,
        )

    def step(
        self,
        action: MedAgentAction,
        timeout_s: Optional[float] = None,
        **kwargs,
    ) -> MedAgentObservation:  # type: ignore[override]
        if not self._task_cfg:
            self.reset()

        self._state.step_count += 1
        max_steps = self._task_cfg["max_steps"]

        if self._done:
            return self._build_obs(
                last_result="Episode already finished. Call reset() to start a new episode.",
                reward=0.0,
            )

        if action.action_type == "query":
            return self._handle_query(action, max_steps)
        if action.action_type == "calculate":
            return self._handle_calculate(action, max_steps)
        if action.action_type == "submit":
            return self._handle_submit(action)

        return self._build_obs(
            last_result=(
                f"Unknown action_type '{action.action_type}'. "
                "Use 'query', 'calculate', or 'submit'."
            ),
            reward=-0.1,
        )

    @property
    def state(self) -> State:
        return self._state

    # ------------------------------------------------------------------
    # Action handlers
    # ------------------------------------------------------------------

    def _handle_query(self, action: MedAgentAction, max_steps: int) -> MedAgentObservation:
        if not action.field:
            return self._build_obs(
                last_result="'query' action requires a 'field' name.",
                reward=-0.05,
            )

        fields = self._case["fields"]
        if action.field not in fields:
            avail = ", ".join(sorted(fields.keys()))
            return self._build_obs(
                last_result=(
                    f"Field '{action.field}' not found. "
                    f"Available fields: {avail}."
                ),
                reward=-0.1,
            )

        value = fields[action.field]
        already_queried = action.field in self._queried
        self._queried[action.field] = value

        # Progressive reward: critical field first time > irrelevant > duplicate
        critical_fields = self._task_cfg.get("critical_fields", [])
        if already_queried:
            reward = 0.0
        elif action.field in critical_fields:
            reward = _CRITICAL_FIELD_REWARD
        else:
            reward = _IRRELEVANT_FIELD_REWARD

        # Coverage bonus: once agent has queried >= 60% of critical fields
        coverage_bonus = 0.0
        if not self._coverage_bonus_given and critical_fields:
            queried_critical = sum(
                1 for f in critical_fields if f in self._queried
            )
            coverage = queried_critical / len(critical_fields)
            if coverage >= _COVERAGE_THRESHOLD:
                coverage_bonus = _COVERAGE_BONUS
                self._coverage_bonus_given = True

        total_reward = reward + coverage_bonus
        self._cumulative_reward += total_reward

        remaining = max_steps - self._state.step_count
        coverage_note = (
            f"  [Coverage bonus +{coverage_bonus:.2f}! Ready to submit.]"
            if coverage_bonus > 0 else ""
        )
        last_result = (
            f"{action.field} = {value}  "
            f"(steps remaining: {remaining}){coverage_note}"
        )
        return self._build_obs(last_result=last_result, reward=total_reward)

    def _handle_calculate(self, action: MedAgentAction, max_steps: int) -> MedAgentObservation:
        if not action.expression:
            return self._build_obs(
                last_result="'calculate' action requires an 'expression' string.",
                reward=-0.05,
            )
        try:
            result = _safe_eval(action.expression)
            remaining = max_steps - self._state.step_count
            return self._build_obs(
                last_result=(
                    f"{action.expression} = {result:.4g}  "
                    f"(steps remaining: {remaining})"
                ),
                reward=0.0,
            )
        except Exception as exc:
            return self._build_obs(
                last_result=f"Calculation error: {exc}",
                reward=-0.05,
            )

    def _handle_submit(self, action: MedAgentAction) -> MedAgentObservation:
        if action.answer is None:
            return self._build_obs(
                last_result="'submit' action requires an 'answer' value.",
                reward=-0.1,
            )

        grader = self._task_cfg["grader"]
        score, feedback = grader(action.answer, self._case)

        self._score = score
        self._done = True

        return self._build_obs(last_result=feedback, reward=score, done=True)

    # ------------------------------------------------------------------
    # Step-level task validation (MedAgentGym-style intermediate check)
    # ------------------------------------------------------------------

    def _task_validate(self) -> dict:
        """
        Returns a progress snapshot after each step.

        Keys:
          information_coverage  – fraction of critical fields already queried (0.0–1.0)
          efficiency_score      – 1 - (steps_used / max_steps) clamped to [0, 1]
          ready_to_submit       – True when coverage >= threshold
          suggestion            – human-readable hint
        """
        critical = self._task_cfg.get("critical_fields", [])
        max_steps = self._task_cfg.get("max_steps", 10)

        if not critical:
            coverage = 1.0
        else:
            queried_critical = sum(1 for f in critical if f in self._queried)
            coverage = queried_critical / len(critical)

        steps_used = self._state.step_count
        efficiency = max(0.0, 1.0 - steps_used / max_steps)
        ready = coverage >= _COVERAGE_THRESHOLD

        if ready:
            suggestion = "You have enough information to submit your answer."
        elif coverage > 0:
            missing = [f for f in critical if f not in self._queried]
            suggestion = f"Still need: {', '.join(missing[:3])}."
        else:
            suggestion = "Start by querying the critical fields for this task."

        return {
            "information_coverage": round(coverage, 3),
            "efficiency_score": round(efficiency, 3),
            "ready_to_submit": ready,
            "suggestion": suggestion,
        }

    # ------------------------------------------------------------------
    # Observation builder
    # ------------------------------------------------------------------

    def _build_obs(
        self,
        last_result: str,
        reward: float = 0.0,
        done: bool = False,
    ) -> MedAgentObservation:
        if done:
            self._done = True

        max_steps = self._task_cfg.get("max_steps", 10) if self._task_cfg else 10
        if self._state.step_count >= max_steps and not self._done:
            self._done = True
            last_result += f" [Max steps ({max_steps}) reached — episode ended.]"

        progress = self._task_validate() if self._task_cfg else {}

        return MedAgentObservation(
            task_id=self._state.episode_id,
            task_type=self._task_type,
            difficulty=self._task_cfg.get("difficulty", ""),
            scenario_description=self._case.get("scenario", ""),
            available_fields=sorted(self._case.get("fields", {}).keys()),
            queried_fields=dict(self._queried),
            last_result=last_result,
            score=self._score,
            done=self._done,
            reward=reward,
            metadata={
                "step": self._state.step_count,
                "max_steps": max_steps,
                "task_description": self._task_cfg.get("description", ""),
                "valid_answers": self._task_cfg.get("valid_answers"),
                "case_id": self._case.get("case_id"),
                "information_coverage": progress.get("information_coverage", 0.0),
                "efficiency_score": progress.get("efficiency_score", 1.0),
                "ready_to_submit": progress.get("ready_to_submit", False),
                "suggestion": progress.get("suggestion", ""),
                "cumulative_reward": round(self._cumulative_reward, 4),
            },
        )
