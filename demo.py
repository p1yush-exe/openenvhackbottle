"""
Gradio Interactive Demo for ClinicalBench

Launch with:
    python demo.py

Then open http://localhost:7860 in your browser.
"""

import asyncio
import gradio as gr
from clinical_bench.client import ClinicalBenchClient
from clinical_bench.models import ClinicalAction

# Example problems for each task
EXAMPLES = [
    # Clinical Calculator (Easy)
    [
        "clinical_calc",
        0,
        """# Calculate BMI from patient data
weight_kg = 85
height_m = 1.75

bmi = weight_kg / (height_m ** 2)
print(round(bmi, 1))"""
    ],
    # Biostat Power (Medium) 
    [
        "biostat_power",
        0,
        """# Calculate required sample size for a study
from scipy import stats
import math

alpha = 0.05
power = 0.80
effect_size = 0.5

z_alpha = stats.norm.ppf(1 - alpha/2)
z_beta = stats.norm.ppf(power)

n = ((z_alpha + z_beta) ** 2) / (effect_size ** 2)
n_per_group = math.ceil(n)

print(n_per_group)"""
    ],
    # BioCoder (Hard)
    [
        "biocoder",
        0,
        """def calculate_gc_content(sequence):
    \"\"\"Calculate GC content percentage of DNA sequence.\"\"\"
    if not sequence:
        return 0.0
    
    sequence = sequence.upper()
    gc_count = sequence.count('G') + sequence.count('C')
    total = len(sequence)
    
    return (gc_count / total) * 100

# Test the function
test_seq = "ATGCATGC"
result = calculate_gc_content(test_seq)
print(f"GC content: {result}%")"""
    ]
]

# Server base URL - update if running remotely
BASE_URL = "ws://localhost:8080"


async def run_episode(task_name: str, task_index: int, code: str) -> dict:
    """Run a single code submission against the environment."""
    try:
        async with ClinicalBenchClient(base_url=BASE_URL) as env:
            # Reset environment
            result = await env.reset(
                task_name=task_name, 
                task_index=task_index,
                seed=42
            )
            
            problem = result.observation.task_description
            
            # Submit code
            action = ClinicalAction(code=code)
            result = await env.step(action)
            
            return {
                "success": True,
                "problem": problem,
                "execution_result": result.observation.execution_result,
                "error": result.observation.error,
                "reward": result.observation.reward,
                "done": result.observation.done,
                "metadata": result.observation.metadata
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "problem": "",
            "execution_result": "",
            "reward": 0.0,
            "done": False,
            "metadata": {}
        }


def gradio_interface(task_name: str, task_index: int, code: str) -> str:
    """Gradio interface wrapper (synchronous)."""
    result = asyncio.run(run_episode(task_name, int(task_index), code))
    
    if not result["success"]:
        return f"""
## ❌ Error

**Connection Error:** {result['error']}

**Make sure the ClinicalBench server is running:**

```bash
cd clinical_bench
DATA_PATH=./data uvicorn server.app:app --host 0.0.0.0 --port 8080
```
"""
    
    # Format output
    reward_emoji = "✅" if result["reward"] >= 1.0 else "⚠️" if result["reward"] >= 0.5 else "❌"
    reward_pct = int(result["reward"] * 100)
    
    # Truncate long outputs
    problem_preview = result["problem"][:500] + "..." if len(result["problem"]) > 500 else result["problem"]
    
    output = f"""
## {reward_emoji} Score: {result['reward']:.2f} / 1.00 ({reward_pct}%)

### Problem
```
{problem_preview}
```

### Your Code Output
```
{result['execution_result'][:1000] if result['execution_result'] else '(no output)'}
```
"""
    
    if result["error"]:
        output += f"""
### Error
```
{result['error'][:500]}
```
"""
    
    # Status message
    if result["reward"] >= 1.0:
        output += "\n### 🎉 **SOLVED!** Perfect score!\n"
    elif result["reward"] >= 0.5:
        output += "\n### 🤔 **Close!** Try refining your answer.\n"
    elif result["reward"] >= 0.3:
        output += "\n### ⚠️ **Code runs** but answer is incorrect. Check your logic.\n"
    elif result["reward"] >= 0.1:
        output += "\n### ❌ **Syntax or runtime error.** Fix the error and try again.\n"
    else:
        output += "\n### ❌ **No output produced.** Make sure your code prints the answer.\n"
    
    # Metadata
    difficulty = result["metadata"].get("difficulty", "unknown")
    output += f"\n**Task:** {task_name} ({difficulty})\n"
    output += f"**Problem Index:** {task_index}\n"
    
    return output


# Create Gradio interface
demo = gr.Interface(
    fn=gradio_interface,
    inputs=[
        gr.Dropdown(
            choices=["clinical_calc", "biostat_power", "biocoder"],
            value="clinical_calc",
            label="Task Type",
            info="Select difficulty: clinical_calc (easy), biostat_power (medium), biocoder (hard)"
        ),
        gr.Number(
            value=0,
            label="Problem Index",
            info="Index of the problem to solve (0-based)",
            precision=0
        ),
        gr.Code(
            language="python",
            label="Your Python Code",
            lines=15,
            value=EXAMPLES[0][2]
        )
    ],
    outputs=gr.Markdown(label="Result"),
    title="🏥 ClinicalBench Interactive Demo",
    description="""
**Try solving medical code generation problems!**

ClinicalBench is an OpenEnv environment for biomedical code generation. Submit Python code to solve clinical, biostatistics, and bioinformatics problems.

**How to use:**
1. Select a task type (Easy → Medium → Hard)
2. Choose a problem index (or leave at 0)
3. Write Python code that prints the answer
4. Click Submit to see your score!

**Reward system:**
- 1.0 = Correct answer ✅
- 0.5 = Close answer (within 2× tolerance)
- 0.3 = Code runs but wrong answer
- 0.1 = Syntax/runtime error
- 0.0 = No output

---

⚠️ **Note:** Server must be running at `localhost:8080`. See instructions below if you get connection errors.
""",
    examples=EXAMPLES,
    cache_examples=False,
    theme=gr.themes.Soft(),
    allow_flagging="never"
)


if __name__ == "__main__":
    print("=" * 60)
    print("🏥 ClinicalBench Interactive Demo")
    print("=" * 60)
    print("\n📋 Prerequisites:")
    print("   1. ClinicalBench server must be running:")
    print("      $ cd clinical_bench")
    print("      $ DATA_PATH=./data uvicorn server.app:app --port 8080\n")
    print("   2. Open http://localhost:7860 in your browser\n")
    print("=" * 60)
    print("\n🚀 Starting Gradio interface...\n")
    
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False
    )
