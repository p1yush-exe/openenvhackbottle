"""
Baseline inference script for the MedAgent Environment.

Runs one episode per task type (easy / medium / hard) using an LLM agent
that interacts with the environment through the OpenEnv WebSocket client.

Required environment variables:
    API_BASE_URL     – OpenAI-compatible API base URL
    MODEL_NAME       – Model identifier, e.g. "gpt-4o-mini"
    HF_TOKEN         – HuggingFace token  (or set OPENAI_API_KEY as a fallback)

Usage:
    python inference.py --base_url http://localhost:8000 --episodes 3

Output:
    Structured stdout logs in [START] / [STEP] / [END] format, followed by a
    final JSON summary printed to stdout.
"""

import argparse
import json
import os
import sys

from openai import OpenAI

try:
    from .client import MedAgentEnv
    from .models import MedAgentAction
except ImportError:
    from client import MedAgentEnv
    from models import MedAgentAction


API_BASE_URL = os.getenv("API_BASE_URL", "https://api.openai.com/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4o-mini")
HF_TOKEN = os.getenv("HF_TOKEN", os.getenv("OPENAI_API_KEY", ""))
LLM_ENABLED = bool(HF_TOKEN)

TASK_INSTRUCTIONS = {
    "vital_triage": (
        "Assess vital signs and submit one of: stable, concerning, critical."
    ),
    "news2_score": (
        "Calculate the NEWS2 total and submit it as an integer string."
    ),
    "medication_dosing": (
        "Determine renal dose adjustment and submit one of: normal_dose, "
        "dose_75, dose_50, contraindicated."
    ),
}

VALID_ANSWERS = {
    "vital_triage": ["stable", "concerning", "critical"],
    "medication_dosing": ["normal_dose", "dose_75", "dose_50", "contraindicated"],
}

CRITICAL_FIELDS = {
    "vital_triage": [
        "spo2_percent", "systolic_bp", "heart_rate",
        "respiratory_rate", "consciousness",
    ],
    "news2_score": [
        "respiratory_rate", "spo2_percent", "on_supplemental_oxygen",
        "systolic_bp", "heart_rate", "consciousness", "temperature_celsius",
    ],
    "medication_dosing": ["egfr_ml_min", "drug", "dialysis"],
}


SYSTEM_PROMPT = """\
You are a clinical decision-support AI agent working inside a medical assessment environment.

Each episode presents a patient scenario. You interact through structured JSON actions:
  {"action_type": "query",     "field": "<field_name>"}
  {"action_type": "calculate", "expression": "<arithmetic>"}
  {"action_type": "submit",    "answer": "<your_answer>", "reasoning": "<brief reasoning>"}

Strategy:
1. Read the scenario and available_fields from the observation.
2. Query the fields you need (heart_rate, spo2_percent, egfr_ml_min, etc.).
3. Use "calculate" for arithmetic if needed (e.g. "3 + 2 + 1").
4. When the metadata.ready_to_submit flag is true (or you are confident), submit.

Always output ONLY a valid JSON object — no markdown, no extra text.
"""


def _build_user_message(obs: dict) -> str:
    metadata = obs.get("metadata") or {}
    task_type = obs["task_type"]
    coverage = _coverage_from_obs(obs)
    lines = [
        f"Task type: {task_type} ({obs['difficulty']})",
        f"Scenario: {obs['scenario_description']}",
        f"Available fields: {', '.join(obs['available_fields'])}",
        f"Queried so far: {json.dumps(obs['queried_fields'])}",
        f"Last result: {obs['last_result']}",
        f"Task instructions: {metadata.get('task_description') or TASK_INSTRUCTIONS.get(task_type, '')}",
    ]
    valid_answers = metadata.get("valid_answers") or VALID_ANSWERS.get(task_type)
    if valid_answers:
        lines.append(f"Valid answers: {valid_answers}")
    lines.append(
        f"Steps used: {metadata.get('step', 0)} / {metadata.get('max_steps', '?')}"
    )
    lines.append(
        f"Information coverage: {coverage:.0%}  "
        f"ready_to_submit: {metadata.get('ready_to_submit', coverage >= 0.6)}"
    )
    hint = metadata.get("suggestion", "")
    if hint:
        lines.append(f"Hint: {hint}")
    return "\n".join(lines)


def _coverage_from_obs(obs: dict) -> float:
    task_type = obs.get("task_type")
    critical = CRITICAL_FIELDS.get(task_type, [])
    queried = obs.get("queried_fields", {})
    if not critical:
        return 0.0
    return sum(1 for field in critical if field in queried) / len(critical)


def _call_llm(client: OpenAI, messages: list) -> dict:
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=messages,
        temperature=0.0,
        max_tokens=256,
    )
    text = response.choices[0].message.content.strip()
    # Strip markdown code fences if present
    if text.startswith("```"):
        parts = text.split("```")
        text = parts[1] if len(parts) > 1 else parts[0]
        if text.startswith("json"):
            text = text[4:]
    return json.loads(text)


def _news2_component_scores(fields: dict) -> int:
    rr = int(fields["respiratory_rate"])
    spo2 = int(fields["spo2_percent"])
    sbp = int(fields["systolic_bp"])
    hr = int(fields["heart_rate"])
    temp = float(fields["temperature_celsius"])
    consciousness = str(fields["consciousness"]).lower()
    on_oxygen = bool(fields["on_supplemental_oxygen"])

    score = 0
    score += 3 if rr <= 8 else 1 if 9 <= rr <= 11 else 0 if 12 <= rr <= 20 else 2 if 21 <= rr <= 24 else 3
    score += 3 if spo2 <= 91 else 2 if 92 <= spo2 <= 93 else 1 if 94 <= spo2 <= 95 else 0
    score += 2 if on_oxygen else 0
    score += 3 if sbp <= 90 else 2 if 91 <= sbp <= 100 else 1 if 101 <= sbp <= 110 else 0 if 111 <= sbp <= 219 else 3
    score += 3 if hr <= 40 else 1 if 41 <= hr <= 50 else 0 if 51 <= hr <= 90 else 1 if 91 <= hr <= 110 else 2 if 111 <= hr <= 130 else 3
    score += 3 if consciousness != "alert" else 0
    score += 3 if temp <= 35.0 else 1 if 35.1 <= temp <= 36.0 else 0 if 36.1 <= temp <= 38.0 else 1 if 38.1 <= temp <= 39.0 else 2
    return score


def _dose_adjustment(fields: dict) -> str:
    drug = str(fields["drug"]).lower()
    egfr = float(fields["egfr_ml_min"])
    dialysis = bool(fields.get("dialysis", False))

    if "metronidazole" in drug:
        return "normal_dose"
    if "piperacillin" in drug or "tazobactam" in drug:
        if egfr >= 40:
            return "normal_dose"
        if egfr >= 20:
            return "dose_75"
        return "dose_50"
    if "vancomycin" in drug:
        if egfr < 10 and not dialysis:
            return "contraindicated"
        if egfr < 30:
            return "dose_50"
        return "normal_dose"
    if "meropenem" in drug:
        if egfr >= 50:
            return "normal_dose"
        return "dose_50"
    if "ciprofloxacin" in drug:
        if egfr < 30:
            return "dose_50"
        return "normal_dose"
    return "normal_dose"


def _fallback_action(obs: dict) -> dict:
    """Deterministic baseline policy used when the configured LLM is unavailable."""
    task_type = obs.get("task_type")
    queried = obs.get("queried_fields", {})
    available = obs.get("available_fields", [])
    metadata = obs.get("metadata") or {}

    for field in CRITICAL_FIELDS.get(task_type, available):
        if field in available and field not in queried:
            return {
                "action_type": "query",
                "field": field,
                "reasoning": "Deterministic baseline querying required field.",
            }

    if task_type == "vital_triage":
        spo2 = int(queried["spo2_percent"])
        sbp = int(queried["systolic_bp"])
        hr = int(queried["heart_rate"])
        rr = int(queried["respiratory_rate"])
        consciousness = str(queried["consciousness"]).lower()
        if spo2 < 90 or sbp < 90 or hr < 50 or hr > 120 or rr < 10 or rr > 25 or consciousness == "unresponsive":
            answer = "critical"
        elif spo2 < 95 or sbp < 105 or hr > 100 or rr > 20 or consciousness != "alert":
            answer = "concerning"
        else:
            answer = "stable"
    elif task_type == "news2_score":
        answer = str(_news2_component_scores(queried))
    elif task_type == "medication_dosing":
        answer = _dose_adjustment(queried)
    else:
        valid_answers = metadata.get("valid_answers") or ["stable"]
        answer = valid_answers[0]

    return {
        "action_type": "submit",
        "answer": answer,
        "reasoning": "Deterministic baseline rule-based answer.",
    }


def run_episode(env_url: str, client: OpenAI, episode_num: int) -> dict:
    """Run one full episode and return a result dict."""
    with MedAgentEnv(base_url=env_url).sync() as env:
        result = env.reset()
        obs = result.observation.model_dump()

        task_type = obs.get("task_type", "unknown")
        difficulty = obs.get("difficulty", "unknown")

        print(f"[START] episode={episode_num} task={task_type} difficulty={difficulty}")

        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        done = result.done
        final_score = float(result.reward or 0.0)
        step = 0

        while not done:
            step += 1
            messages.append({"role": "user", "content": _build_user_message(obs)})

            try:
                if not LLM_ENABLED:
                    raise RuntimeError("HF_TOKEN / OPENAI_API_KEY not set")
                action_dict = _call_llm(client, messages)
            except Exception as exc:
                print(f"[STEP] episode={episode_num} step={step} llm_error={exc!r} using_fallback=true")
                action_dict = _fallback_action(obs)

            messages.append({"role": "assistant", "content": json.dumps(action_dict)})

            step_result = env.step(MedAgentAction.model_validate(action_dict))
            obs = step_result.observation.model_dump()
            done = step_result.done or obs.get("done", False)
            step_reward = float(step_result.reward or 0.0)
            if step_result.reward is not None:
                final_score = max(final_score, step_reward)

            print(
                f"[STEP] episode={episode_num} step={step} "
                f"action_type={action_dict.get('action_type')} "
                f"reward={step_reward:.3f} done={done} "
                f"result={obs.get('last_result', '')[:80]!r}"
            )

        final_score = obs.get("score", final_score)
        meta = obs.get("metadata", {})
        coverage = meta.get("information_coverage", _coverage_from_obs(obs))

        print(
            f"[END] episode={episode_num} task={task_type} difficulty={difficulty} "
            f"score={final_score:.3f} steps={step} "
            f"coverage={coverage:.0%}"
        )

        return {
            "episode": episode_num,
            "task_type": task_type,
            "difficulty": difficulty,
            "steps": step,
            "score": final_score,
            "information_coverage": coverage,
            "cumulative_reward": meta.get("cumulative_reward", 0.0),
        }


def main():
    parser = argparse.ArgumentParser(
        description="Run baseline MedAgent inference episodes."
    )
    parser.add_argument(
        "--base_url",
        default=os.getenv("ENV_BASE_URL", "http://localhost:8000"),
        help="MedAgent environment server URL",
    )
    parser.add_argument(
        "--episodes",
        type=int,
        default=3,
        help="Number of episodes to run (3 covers all task types once)",
    )
    args = parser.parse_args()

    if not HF_TOKEN:
        print("WARNING: HF_TOKEN / OPENAI_API_KEY not set. LLM calls will fail.", file=sys.stderr)

    client = OpenAI(base_url=API_BASE_URL, api_key=HF_TOKEN or "placeholder")

    print(f"Running {args.episodes} episode(s) against {args.base_url}")
    print(f"Model: {MODEL_NAME}")
    print()

    results = []
    for ep in range(1, args.episodes + 1):
        try:
            ep_result = run_episode(args.base_url, client, ep)
            results.append(ep_result)
        except Exception as exc:
            print(f"[END] episode={ep} error={exc!r}", file=sys.stderr)

    if not results:
        print(json.dumps({"error": "No episodes completed successfully."}))
        sys.exit(1)

    avg_score = sum(r["score"] for r in results) / len(results)
    summary = {
        "episodes_completed": len(results),
        "average_score": round(avg_score, 4),
        "model": MODEL_NAME,
        "env_url": args.base_url,
        "results": results,
    }
    print()
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
