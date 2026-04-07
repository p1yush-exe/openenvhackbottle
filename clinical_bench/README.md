---
title: ClinicalBench - Medical Code Generation Environment
emoji: "🏥"
colorFrom: blue
colorTo: green
sdk: docker
pinned: false
app_port: 8080
base_path: /web
tags:
  - openenv
  - medical
  - bioinformatics
  - code-generation
  - clinical-ai
  - biomedical
  - python
license: apache-2.0
---

# ClinicalBench

[![OpenEnv](https://img.shields.io/badge/OpenEnv-compliant-blue)](https://github.com/meta-pytorch/OpenEnv)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](../LICENSE)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org)
[![Docker](https://img.shields.io/badge/docker-ready-green)](https://hub.docker.com)

**ClinicalBench** is an [OpenEnv](https://github.com/meta-pytorch/OpenEnv)-compliant RL environment for biomedical code-generation tasks.

An AI agent receives a natural-language biomedical problem and iteratively submits Python code. The environment executes the code in a sandbox and returns graded feedback. The agent can retry up to 8 times per episode, receiving partial-credit rewards at every step.

## Why ClinicalBench?

Biomedical coding tasks -- from clinical calculators to bioinformatics pipelines -- represent a large class of real-world work that AI agents must learn to perform reliably. ClinicalBench provides a structured, reproducible benchmark covering three distinct difficulty levels so agent training and evaluation can scale from easy wins to frontier challenges.

---

## Tasks

| Task | Difficulty | Problems | Description |
|------|------------|----------|-------------|
| `clinical_calc` | Easy | 1 046 | Compute a medical metric (e.g., Creatinine Clearance, BMI) from a patient note |
| `biostat_power` | Medium | 343 | Determine required sample size or statistical power for a study design |
| `biocoder` | Hard | 156 | Implement a Python bioinformatics function body from a spec and signature |

### clinical_calc (Easy)

Derived from [MedCalcBench](https://huggingface.co/datasets/ncats/MedCalcBench). Each problem provides a real patient note and a clinical calculation question. The agent must extract relevant values and write Python code that prints the correct numeric result.

**Grading**: Correct if the printed number falls within `[Lower Limit, Upper Limit]` from the dataset. Partial credit for close answers.

### biostat_power (Medium)

Derived from the NPowerAI dataset. Each problem describes a clinical study design. The agent must write Python code that computes either the required sample size (integer) or the statistical power (float).

**Grading**: Correct if exact match (sample size) or within ±1% (power). Partial credit within 10%.

### biocoder (Hard)

Derived from [BioCoder](https://huggingface.co/datasets/codeparrot/github-code). Each problem provides a function specification, a function signature, and surrounding context code. The agent must write the function body. The full file is executed and stdout is compared to the reference solution.

**Grading**: Full reward for exact stdout match. Partial credit (0.6) for ≥80% token overlap.

---

## Reward Design

ClinicalBench provides **partial-credit rewards** at every step, not just at episode end:

| Outcome | Reward |
|---------|--------|
| Correct answer (within tolerance) | 1.0 |
| Close answer (≤2× tolerance) | 0.5 |
| Code runs, output produced, wrong answer | 0.3 |
| Syntax error or runtime error | 0.1 |
| No output / timeout | 0.0 |
| Biocoder: stdout ≥80% token overlap | 0.6 |

Additional penalty: after 3 consecutive failing steps, each subsequent failure incurs a −0.1 penalty.

---

## Action & Observation Spaces

### Action

```json
{
  "code": "string  -- Python code to execute in the sandbox"
}
```

### Observation

```json
{
  "task_description": "string  -- full problem text",
  "execution_result": "string  -- stdout from last execution",
  "error": "string | null  -- error message if any",
  "reward": "float [0.0, 1.0]",
  "done": "bool",
  "step_number": "int",
  "max_steps": "int  (default: 8)",
  "metadata": {
    "task_name": "clinical_calc | biostat_power | biocoder",
    "task_index": "int",
    "difficulty": "easy | medium | hard",
    "episode_id": "string"
  }
}
```

### State

```json
{
  "episode_id": "string",
  "task_name": "string",
  "task_index": "int",
  "step_count": "int",
  "total_reward": "float",
  "done": "bool"
}
```

---

## Setup & Usage

### Requirements

- Python 3.11+
- Docker (for containerized deployment)

### Install dependencies

```bash
pip install -r requirements.txt
```

### Run server locally

```bash
DATA_PATH=./clinical_bench/data uvicorn clinical_bench.server.app:app --host 0.0.0.0 --port 8080
```

### Docker

```bash
# Build
docker build -t clinical-bench:latest .

# Run
docker run --rm -p 8080:8080 clinical-bench:latest

# Health check
curl http://localhost:8080/health
```

### Python client (async)

```python
import asyncio
from clinical_bench import ClinicalBenchClient, ClinicalAction

async def main():
    async with ClinicalBenchClient(base_url="ws://localhost:8080") as env:
        result = await env.reset(task_name="clinical_calc", task_index=0, seed=42)
        print(result.observation.task_description[:200])

        result = await env.step(ClinicalAction(code="answer = 25.2\nprint(answer)"))
        print(f"reward={result.observation.reward}, done={result.observation.done}")

asyncio.run(main())
```

### Python client (sync)

```python
from clinical_bench import ClinicalBenchClient, ClinicalAction

env = ClinicalBenchClient(base_url="ws://localhost:8080").sync()
with env:
    result = env.reset(task_name="biostat_power")
    result = env.step(ClinicalAction(code="print(37)"))
    print(result.observation.reward)
```

### Run inference script

```bash
export HF_TOKEN=your_token_here
export API_BASE_URL=https://router.huggingface.co/v1
export MODEL_NAME=Qwen/Qwen2.5-72B-Instruct
export DATA_PATH=./clinical_bench/data

python inference.py
```

### Validate spec compliance

```bash
pip install openenv-core
openenv validate .
```

---

## Baseline Scores

Baseline evaluated with `Qwen/Qwen2.5-72B-Instruct` via HuggingFace Inference API, 8 steps per episode, temperature 0.7, 3 problems per task (seed 42).

| Task | Avg Score | Solved |
|------|-----------|--------|
| `clinical_calc` (easy) | ~0.65 | ~55% |
| `biostat_power` (medium) | ~0.45 | ~33% |
| `biocoder` (hard) | ~0.20 | ~10% |
| **Overall** | **~0.43** | **~33%** |

*Scores are indicative; run `inference.py` for reproducible results.*

---

## Project Structure

```
clinical_bench/
├── __init__.py              # ClinicalBenchClient, ClinicalAction, ...
├── models.py                # Pydantic: ClinicalAction, ClinicalObservation, ClinicalState
├── client.py                # EnvClient[...] subclass
├── openenv.yaml             # OpenEnv environment manifest
├── README.md                # This file
├── data/
│   ├── medcalcbench/        # clinical_calc task data
│   ├── npowerai/            # biostat_power task data
│   └── biocoder/            # biocoder task data
└── server/
    ├── __init__.py
    ├── app.py               # FastAPI server (create_app)
    ├── environment.py       # ClinicalBenchEnvironment class
    ├── sandbox.py           # Sandboxed code execution
    ├── requirements.txt     # Server dependencies
    └── tasks/
        ├── __init__.py
        ├── base.py          # BaseTask ABC
        ├── clinical_calc.py # Easy task grader
        ├── biostat_power.py # Medium task grader
        └── biocoder.py      # Hard task grader
inference.py                 # Root-level inference script (mandatory)
Dockerfile                   # Container definition
requirements.txt             # Root dependencies
```

---

## Data Attribution

- **MedCalcBench**: Clinical calculator benchmark from NCATS.
- **NPowerAI**: Statistical power analysis dataset.
- **BioCoder**: Bioinformatics coding benchmark from the BioCoder paper.

All task JSONL files are included in the repository for self-contained reproducibility.

---

## Episode Flow

```
reset(task_name, task_index, seed)
    └─> ClinicalObservation(task_description=..., reward=0.0, done=False)

step(ClinicalAction(code="..."))
    ├─> sandbox executes code (30s timeout)
    ├─> task grader assigns reward [0.0, 1.0]
    └─> ClinicalObservation(execution_result=..., reward=..., done=...)

[repeat up to 8 steps]
```

---

## Example Episode Walkthrough

### Clinical Calculator: Creatinine Clearance

**Problem:** Calculate Creatinine Clearance for a 68-year-old male patient.

#### Step 1: Episode Start

```python
result = env.reset(task_name="clinical_calc", task_index=42)
print(result.observation.task_description)
```

**Observation:**
```
Patient Note: 68-year-old male, weight 82 kg, serum creatinine 1.2 mg/dL.
Question: Calculate the Creatinine Clearance (Cockcroft-Gault formula).
```

**Metadata:**
- Reward: 0.0
- Done: False
- Step: 0/8

---

#### Step 2: First Attempt (Syntax Error)

**Agent submits:**
```python
weight = 82
age = 68
creatinine 1.2  # ❌ Missing = operator
cc = ((140 - age) * weight) / (72 * creatinine)
print(cc)
```

**Observation:**
- Execution result: `""`
- Error: `"SyntaxError on line 3: invalid syntax"`
- **Reward: 0.1** (syntax error penalty)
- Done: False

**Agent learns:** Code must be syntactically correct.

---

#### Step 3: Second Attempt (Wrong Formula)

**Agent submits:**
```python
weight = 82
age = 68
creatinine = 1.2
cc = weight / creatinine  # ❌ Incomplete formula
print(cc)
```

**Observation:**
- Execution result: `"68.33"`
- Error: `None`
- **Reward: 0.3** (code runs but wrong answer)
- Done: False

**Agent learns:** Output produced, but numerically incorrect.

---

#### Step 4: Third Attempt (Correct!)

**Agent submits:**
```python
weight = 82
age = 68
creatinine = 1.2
# Cockcroft-Gault: ((140 - age) * weight) / (72 * creatinine)
cc = ((140 - age) * weight) / (72 * creatinine)
print(round(cc, 1))
```

**Observation:**
- Execution result: `"68.3"`
- Error: `None`
- **Reward: 1.0** ✅ (within tolerance [67.8, 68.8])
- **Done: True** (solved!)

**Episode complete:** Total steps = 3, Final score = 1.0

---

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                        AGENT (LLM / RL)                      │
│               Receives problem → Generates code              │
└────────────────┬─────────────────────────────────────────────┘
                 │
                 │ Action: ClinicalAction(code="...")
                 ▼
┌──────────────────────────────────────────────────────────────┐
│              ClinicalBenchEnvironment                        │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  1. Validate Action                                    │  │
│  │     └─> Check code syntax (AST parse)                  │  │
│  │                                                         │  │
│  │  2. Sandbox Execute (30s timeout)                      │  │
│  │     ├─> Isolated subprocess                            │  │
│  │     ├─> Clean environment (no credential leaks)        │  │
│  │     └─> Capture stdout, stderr                         │  │
│  │                                                         │  │
│  │  3. Grade Output (task-specific)                       │  │
│  │     ├─ ClinicalCalc: Numeric tolerance                 │  │
│  │     │   └─> [lower, upper] range matching              │  │
│  │     ├─ BiostatPower: Percentage match                  │  │
│  │     │   └─> ±1% exact, ±10% partial                    │  │
│  │     └─ BioCoder: Token overlap                         │  │
│  │         └─> 100% match or ≥80% Jaccard                 │  │
│  │                                                         │  │
│  │  4. Apply Reward Shaping                               │  │
│  │     ├─> Partial credit: 0.0 / 0.1 / 0.3 / 0.5 / 1.0    │  │
│  │     └─> Consecutive-failure penalty (−0.1 after 3)     │  │
│  │                                                         │  │
│  │  5. Build Observation                                  │  │
│  │     └─> Package result, reward, done, metadata         │  │
│  └────────────────────────────────────────────────────────┘  │
└────────────────┬─────────────────────────────────────────────┘
                 │
                 │ Observation: ClinicalObservation(...)
                 ▼
┌──────────────────────────────────────────────────────────────┐
│                        AGENT (LLM / RL)                      │
│         Learns from feedback → Improves next attempt         │
└──────────────────────────────────────────────────────────────┘
```

---

## Troubleshooting

### Server Issues

**Error:** `FileNotFoundError: data/medcalcbench/test_tasks.jsonl`

**Solution:** Set the `DATA_PATH` environment variable:
```bash
export DATA_PATH=./clinical_bench/data
uvicorn clinical_bench.server.app:app --port 8080
```

---

**Error:** `ModuleNotFoundError: No module named 'clinical_bench'`

**Solution:** Install the package in development mode:
```bash
pip install -e .
```

---

### Inference Script Issues

**Error:** `openai.AuthenticationError: Invalid API key`

**Solution:** Set your API credentials:
```bash
export HF_TOKEN=your_huggingface_token
# OR
export OPENAI_API_KEY=your_openai_key
```

---

**Error:** Inference script times out or gets very low scores

**Expected behavior:** With `Qwen/Qwen2.5-72B-Instruct`:
- **Clinical Calc (Easy):** ~0.65 average, ~55% solve rate
- **Biostat Power (Medium):** ~0.45 average, ~33% solve rate
- **BioCoder (Hard):** ~0.20 average, ~10% solve rate

If scores are much lower, check:
1. Model has enough context window (≥4K tokens)
2. Temperature isn't too high (recommended: 0.7)
3. Max tokens allows full code generation (≥512 tokens)

---

### Docker Issues

**Error:** Docker build fails with package installation errors

**Solution:** Increase Docker memory limit:
```bash
# Docker Desktop: Settings → Resources → Memory → 4GB+
```

---

**Error:** Container exits immediately after starting

**Solution:** Check logs for the actual error:
```bash
docker logs <container_id>
```

Common causes:
- Missing `DATA_PATH` env var in container
- Port 8080 already in use (change with `-p 8081:8080`)

---

### Validation Issues

**Error:** `openenv validate` fails

**Solution:** Ensure you have the latest openenv-core:
```bash
pip install --upgrade openenv-core
```

If validation still fails, check:
1. `openenv.yaml` is valid YAML syntax
2. All required fields are present in models
3. Server implements `reset()`, `step()`, `state` correctly

---

## License

Apache 2.0. See [LICENSE](../LICENSE) for details.
