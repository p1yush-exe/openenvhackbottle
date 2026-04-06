---
title: MedAgent Environment
emoji: "🏥"
colorFrom: blue
colorTo: green
sdk: docker
pinned: false
app_port: 8000
base_path: /web
tags:
  - openenv
---

# MedAgent Environment

An OpenEnv-compatible environment for medical clinical assessment tasks, inspired by
[MedAgentGym](https://github.com/wshi83/MedAgentGym).

An AI agent interacts with simulated patient scenarios through a structured
action API: query patient data fields, perform arithmetic calculations, and
submit a final clinical decision.

---

## Tasks (Easy → Medium → Hard)

| # | Task type | Difficulty | Description |
|---|-----------|------------|-------------|
| 1 | `vital_triage` | Easy | Assess vital signs → classify urgency: `stable` / `concerning` / `critical` |
| 2 | `news2_score` | Medium | Calculate the National Early Warning Score 2 (NEWS2, integer 0–20) |
| 3 | `medication_dosing` | Hard | Determine antibiotic dose adjustment based on renal function (eGFR) |

Episodes cycle deterministically: ep 1 → vital_triage, ep 2 → news2_score,
ep 3 → medication_dosing, ep 4 → vital_triage, …

---

## Action Schema

```json
{
  "action_type": "query | calculate | submit",
  "field":       "<field_name>",
  "expression":  "<arithmetic expression>",
  "answer":      "<final answer string>",
  "reasoning":   "<optional chain-of-thought>"
}
```

| `action_type` | Required field | Effect |
|---------------|---------------|--------|
| `query` | `field` | Returns the value of a patient data field |
| `calculate` | `expression` | Safely evaluates arithmetic (e.g. `"3 + 2 * 4"`) |
| `submit` | `answer` | Grades the answer and ends the episode |

---

## Observation Schema

```json
{
  "task_id":              "<episode UUID>",
  "task_type":            "vital_triage | news2_score | medication_dosing",
  "difficulty":           "easy | medium | hard",
  "scenario_description": "<patient scenario text>",
  "available_fields":     ["heart_rate", "spo2_percent", ...],
  "queried_fields":       {"heart_rate": 88, ...},
  "last_result":          "<feedback from last action>",
  "score":                0.0,
  "done":                 false,
  "reward":               0.05,
  "metadata": {
    "step":               1,
    "max_steps":          10,
    "task_description":   "...",
    "valid_answers":      ["stable", "concerning", "critical"],
    "case_id":            0
  }
}
```

---

## Reward / Scoring

| Task | Scoring rule |
|------|-------------|
| `vital_triage` | 1.0 correct, 0.3 adjacent category, 0.0 wrong |
| `news2_score` | 1.0 exact, 0.7 off-by-1, 0.4 off-by-2, 0.0 otherwise |
| `medication_dosing` | 1.0 correct, 0.3 adjacent level, 0.0 wrong |
| Any `query` | +0.05 per queried field |
| Invalid `calculate` | −0.05 |
| Invalid field `query` | −0.10 |

---

## Quick Start

### Local development

```bash
# Install project runtime dependencies
pip install -r requirements.txt

# Or install the package in editable mode from pyproject.toml
pip install -e .

# Run server
cd medagent_env
uvicorn server.app:app --reload --port 8000

# Run baseline agent (3 episodes)
export API_BASE_URL=https://api.openai.com/v1
export MODEL_NAME=gpt-4o-mini
export HF_TOKEN=<your-key>
# OPENAI_API_KEY is also accepted as a fallback to HF_TOKEN
python inference.py --base_url http://localhost:8000 --episodes 3
```

### Docker

```bash
docker build -t medagent_env:latest .
docker run -p 8000:8000 medagent_env:latest
```

### Validate with OpenEnv CLI

```bash
openenv validate
```

### Baseline scores

Local smoke test:
- `inference.py` completes all 3 tasks successfully against the live environment when pointed at an OpenAI-compatible endpoint.
- Latest local smoke test score: `1.00` average over 3 episodes using a deterministic mock OpenAI-compatible server.
- Re-run with your configured `API_BASE_URL`, `MODEL_NAME`, and `HF_TOKEN` or `OPENAI_API_KEY` to record the final model baseline you intend to submit.

---

## Example

```python
from medagent_env import MedAgentEnv, MedAgentAction

with MedAgentEnv(base_url="http://localhost:8000").sync() as env:
    result = env.reset()
    print(result.observation.scenario_description)
    print("Available:", result.observation.available_fields)

    # Query a field
    result = env.step(MedAgentAction(action_type="query", field="heart_rate"))
    print(result.observation.last_result)

    # Submit answer
    result = env.step(MedAgentAction(action_type="submit", answer="stable"))
    print("Score:", result.observation.score)
```
