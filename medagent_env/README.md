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
submit a final clinical decision. Patient cases are stored in a SQLite database
(`server/data/medagent.db`), making it easy to add new cases without code changes.

---

## Tasks (Easy → Medium → Hard)

| # | Task type | Difficulty | Description |
|---|-----------|------------|-------------|
| 1 | `vital_triage` | Easy | Assess vital signs → classify urgency: `stable` / `concerning` / `critical` |
| 2 | `news2_score` | Medium | Calculate the National Early Warning Score 2 (NEWS2, integer 0–20) |
| 3 | `medication_dosing` | Hard | Determine antibiotic dose adjustment based on renal function (eGFR) |

Each task has **10 clinical cases** in the database (30 total). Episodes cycle
deterministically: ep 1 → vital_triage, ep 2 → news2_score, ep 3 →
medication_dosing, ep 4 → vital_triage, …

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
  "available_fields":     ["heart_rate", "spo2_percent", "..."],
  "queried_fields":       {"heart_rate": 88, "...": "..."},
  "last_result":          "<feedback from last action>",
  "score":                0.0,
  "done":                 false,
  "reward":               0.1,
  "metadata": {
    "step":                 1,
    "max_steps":            10,
    "task_description":     "...",
    "valid_answers":        ["stable", "concerning", "critical"],
    "case_id":              0,
    "information_coverage": 0.6,
    "efficiency_score":     0.9,
    "ready_to_submit":      true,
    "suggestion":           "You have enough information to submit your answer.",
    "cumulative_reward":    0.35
  }
}
```

---

## Reward / Scoring

### Final score (on submit)

| Task | Scoring rule |
|------|-------------|
| `vital_triage` | 1.0 correct, 0.3 adjacent category, 0.0 wrong |
| `news2_score` | 1.0 exact, 0.7 off-by-1, 0.4 off-by-2, 0.0 otherwise |
| `medication_dosing` | 1.0 correct, 0.3 adjacent dose level, 0.0 wrong |

### Step-level reward shaping (MedAgentGym-style)

| Event | Reward |
|-------|--------|
| First query of a **critical** field | +0.10 |
| First query of a non-critical field | +0.03 |
| Duplicate query | 0.00 |
| Coverage bonus (≥60% of critical fields queried) | +0.10 (once) |
| Unknown field queried | −0.10 |
| `calculate` error | −0.05 |

Critical fields per task:
- `vital_triage`: spo2_percent, systolic_bp, heart_rate, respiratory_rate, consciousness
- `news2_score`: all 7 NEWS2 component fields
- `medication_dosing`: egfr_ml_min, drug, dialysis

---

## Quick Start

### Environment variables

```bash
export API_BASE_URL=https://api.openai.com/v1   # or any OpenAI-compatible URL
export MODEL_NAME=gpt-4o-mini
export HF_TOKEN=<your-huggingface-or-openai-key>
# OPENAI_API_KEY is also accepted as a fallback to HF_TOKEN
```

### Local development

```bash
# Install dependencies
pip install -r requirements.txt
pip install -e .

# Seed the database (run once; Dockerfile does this automatically)
python server/seed_db.py

# Start the server
uvicorn server.app:app --reload --port 8000

# Run baseline agent (3 episodes covering all tasks)
python inference.py --base_url http://localhost:8000 --episodes 3
```

### Docker

```bash
cd medagent_env
docker build -t medagent_env:latest .
docker run -p 8000:8000 \
  -e API_BASE_URL="$API_BASE_URL" \
  -e MODEL_NAME="$MODEL_NAME" \
  -e HF_TOKEN="$HF_TOKEN" \
  medagent_env:latest
```

### Validate with OpenEnv CLI

```bash
openenv validate                              # offline structural check
openenv validate --url http://localhost:8000  # runtime check
```

---

## Baseline Scores

Local smoke test (deterministic mock OpenAI-compatible endpoint):

- `inference.py` completes all 3 tasks successfully.
- Latest local smoke test: **average score 1.00** over 3 episodes.
- Re-run with your configured `API_BASE_URL`, `MODEL_NAME`, and `HF_TOKEN` to
  record your model baseline before submission.

---

## Code Example

```python
from medagent_env.client import MedAgentEnv
from medagent_env.models import MedAgentAction

with MedAgentEnv(base_url="http://localhost:8000").sync() as env:
    result = env.reset()
    print(result.observation.scenario_description)
    print("Available:", result.observation.available_fields)

    # Query a critical field
    result = env.step(MedAgentAction(action_type="query", field="spo2_percent"))
    print(result.observation.last_result)
    print("Coverage:", result.observation.metadata["information_coverage"])

    # Submit answer
    result = env.step(MedAgentAction(action_type="submit", answer="stable"))
    print("Score:", result.observation.score)
```
