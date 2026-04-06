"""
Baseline inference script for the MedAgent Environment.

Runs one episode per task type (easy / medium / hard) using an LLM agent
that interacts with the environment through the OpenEnv WebSocket client.

Required environment variables:
    API_BASE_URL  - OpenAI-compatible API base URL
    MODEL_NAME    - Model identifier (e.g. "gpt-4o-mini")
    HF_TOKEN      - HuggingFace / API key

Usage:
    python inference.py --base_url http://localhost:8000 --episodes 3
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


SYSTEM_PROMPT = """\
You are a clinical decision-support AI agent working inside a medical assessment environment.

Each episode presents a patient scenario. You interact through structured JSON actions:
  {"action_type": "query",     "field": "<field_name>"}
  {"action_type": "calculate", "expression": "<arithmetic>"}
  {"action_type": "submit",    "answer": "<your_answer>", "reasoning": "<brief reasoning>"}

Strategy:
1. Read the scenario and available_fields from the observation.
2. Query the fields you need (heart_rate, spo2_percent, etc.).
3. Optionally use "calculate" for arithmetic (e.g. "3 + 2 + 1").
4. When confident, submit your final answer.

Always output ONLY a valid JSON object (no markdown, no extra text).
"""


def build_user_message(obs: dict) -> str:
    metadata = obs.get("metadata") or {}
    lines = [
        f"Task type: {obs['task_type']} ({obs['difficulty']})",
        f"Scenario: {obs['scenario_description']}",
        f"Available fields: {', '.join(obs['available_fields'])}",
        f"Queried so far: {json.dumps(obs['queried_fields'])}",
        f"Last result: {obs['last_result']}",
        f"Task instructions: {metadata.get('task_description', '')}",
    ]
    if metadata.get("valid_answers"):
        lines.append(f"Valid answers: {metadata['valid_answers']}")
    lines.append(
        f"Steps used: {metadata.get('step', 0)} / {metadata.get('max_steps', '?')}"
    )
    return "\n".join(lines)


def call_llm(client: OpenAI, messages: list) -> dict:
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=messages,
        temperature=0.0,
        max_tokens=256,
    )
    text = response.choices[0].message.content.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    return json.loads(text)


def run_episode(env_url: str, client: OpenAI) -> dict:
    with MedAgentEnv(base_url=env_url).sync() as env:
        result = env.reset()
        obs = result.observation.model_dump()

        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        done = result.done
        final_score = float(result.reward or 0.0)
        step = 0

        while not done:
            step += 1
            messages.append({"role": "user", "content": build_user_message(obs)})

            try:
                action_dict = call_llm(client, messages)
            except Exception as e:
                print(f"  [step {step}] LLM parse error: {e} - submitting fallback")
                action_dict = {
                    "action_type": "submit",
                    "answer": "stable",
                    "reasoning": "fallback",
                }

            messages.append({"role": "assistant", "content": json.dumps(action_dict)})
            print(f"  [step {step}] action: {action_dict}")

            result = env.step(MedAgentAction.model_validate(action_dict))
            obs = result.observation.model_dump()
            done = result.done or obs.get("done", False)
            if result.reward is not None:
                final_score = max(final_score, float(result.reward))

            print(f"         result: {obs.get('last_result', '')[:120]}")

        final_score = obs.get("score", final_score)
        return {
            "task_type": obs.get("task_type", "unknown"),
            "difficulty": obs.get("difficulty", "unknown"),
            "steps": step,
            "score": final_score,
        }


def main():
    parser = argparse.ArgumentParser()
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
        print("WARNING: HF_TOKEN / OPENAI_API_KEY not set. LLM calls will fail.")

    client = OpenAI(base_url=API_BASE_URL, api_key=HF_TOKEN or "placeholder")

    print(f"Running {args.episodes} episode(s) against {args.base_url}")
    print(f"Model: {MODEL_NAME}\n")

    results = []
    for ep in range(1, args.episodes + 1):
        print(f"=== Episode {ep} ===")
        try:
            result = run_episode(args.base_url, client)
            results.append(result)
            print(
                f"  -> task={result['task_type']}  difficulty={result['difficulty']}"
                f"  score={result['score']:.2f}  steps={result['steps']}\n"
            )
        except Exception as e:
            print(f"  Episode {ep} failed: {e}\n")

    if results:
        avg = sum(r["score"] for r in results) / len(results)
        print("=" * 40)
        print(f"Episodes completed: {len(results)}")
        print(f"Average score:      {avg:.3f}")
        for r in results:
            print(f"  {r['task_type']:25s} ({r['difficulty']:6s})  score={r['score']:.2f}")
    else:
        print("No episodes completed successfully.")
        sys.exit(1)


if __name__ == "__main__":
    main()
