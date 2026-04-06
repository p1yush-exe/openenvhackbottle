"""
MedAgent Environment Implementation.

Implements the OpenEnv Environment interface for medical clinical assessment tasks.
Three difficulty levels cycle deterministically across episodes:
  Episode 1 → vital_triage   (easy)
  Episode 2 → news2_score    (medium)
  Episode 3 → medication_dosing (hard)
  Episode 4 → vital_triage   … and so on
"""

import ast
import operator
import random
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
# Safe arithmetic evaluator (no exec/eval with arbitrary code)
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
    """Evaluate a simple arithmetic expression safely."""
    try:
        tree = ast.parse(expr, mode="eval")
    except SyntaxError as e:
        raise ValueError(f"Syntax error in expression: {e}")

    def _eval(node):
        if isinstance(node, ast.Expression):
            return _eval(node.body)
        elif isinstance(node, ast.Constant):
            return float(node.value)
        elif isinstance(node, ast.BinOp):
            op_type = type(node.op)
            if op_type not in _SAFE_OPS:
                raise ValueError(f"Unsupported operator: {op_type.__name__}")
            return _SAFE_OPS[op_type](_eval(node.left), _eval(node.right))
        elif isinstance(node, ast.UnaryOp):
            op_type = type(node.op)
            if op_type not in _SAFE_OPS:
                raise ValueError(f"Unsupported operator: {op_type.__name__}")
            return _SAFE_OPS[op_type](_eval(node.operand))
        else:
            raise ValueError(f"Unsupported AST node: {type(node).__name__}")

    return _eval(tree)


# ---------------------------------------------------------------------------
# Environment
# ---------------------------------------------------------------------------

class MedAgentEnvironment(Environment):
    """
    Medical clinical assessment environment.

    The agent interacts with a simulated patient scenario through structured
    actions (query fields, calculate values, submit final answer).
    Three task types of increasing difficulty cycle across episodes.
    """

    SUPPORTS_CONCURRENT_SESSIONS: bool = True

    # Internal episode counter used to cycle through tasks deterministically.
    _global_episode_count: int = 0

    def __init__(self):
        self._state = State(episode_id=str(uuid4()), step_count=0)
        self._task_type: str = ""
        self._task_cfg: dict = {}
        self._case: dict = {}
        self._queried: dict = {}
        self._score: float = 0.0
        self._done: bool = False

    # ------------------------------------------------------------------
    # OpenEnv interface
    # ------------------------------------------------------------------

    def reset(self) -> MedAgentObservation:
        # Advance global counter and pick next task type in cycle
        MedAgentEnvironment._global_episode_count += 1
        idx = (MedAgentEnvironment._global_episode_count - 1) % len(TASK_CYCLE)
        self._task_type = TASK_CYCLE[idx]
        self._task_cfg = TASK_REGISTRY[self._task_type]

        # Pick a random case from the task's case list
        self._case = random.choice(self._task_cfg["cases"])

        # Reset episode state
        self._state = State(
            episode_id=str(uuid4()),
            step_count=0,
        )
        self._queried = {}
        self._score = 0.0
        self._done = False

        return self._build_obs(
            last_result=(
                "New episode started. Read the patient scenario, query the fields "
                "you need, then submit your answer."
            ),
            reward=0.0,
        )

    def step(self, action: MedAgentAction) -> MedAgentObservation:  # type: ignore[override]
        self._state.step_count += 1
        max_steps = self._task_cfg["max_steps"]

        if self._done:
            return self._build_obs(
                last_result="Episode already finished. Call reset() to start a new episode.",
                reward=0.0,
            )

        # -- Handle each action type -----------------------------------
        if action.action_type == "query":
            return self._handle_query(action, max_steps)

        elif action.action_type == "calculate":
            return self._handle_calculate(action, max_steps)

        elif action.action_type == "submit":
            return self._handle_submit(action)

        else:
            # Should be caught by Pydantic Literal validation, but just in case
            return self._build_obs(
                last_result=f"Unknown action_type '{action.action_type}'. "
                            "Use 'query', 'calculate', or 'submit'.",
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
        self._queried[action.field] = value

        # Small positive reward for querying relevant fields
        reward = 0.05
        remaining = max_steps - self._state.step_count
        last_result = f"{action.field} = {value}  (steps remaining: {remaining})"
        return self._build_obs(last_result=last_result, reward=reward)

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
                last_result=f"{action.expression} = {result:.4g}  (steps remaining: {remaining})",
                reward=0.0,
            )
        except Exception as e:
            return self._build_obs(
                last_result=f"Calculation error: {e}",
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
    # Helper
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
        # Auto-terminate if step limit reached
        if self._state.step_count >= max_steps and not self._done:
            self._done = True
            last_result += f" [Max steps ({max_steps}) reached — episode ended.]"

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
            },
        )
