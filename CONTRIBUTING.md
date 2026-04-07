# Contributing to ClinicalBench

Thank you for your interest in contributing to ClinicalBench! This document provides guidelines and instructions for contributing.

## 🎯 How to Contribute

### Adding New Tasks

1. **Create a task class** in `clinical_bench/server/tasks/your_task.py`:

```python
from .base import BaseTask
from ..sandbox import ExecutionResult

class YourTask(BaseTask):
    _data_subdir = "your_task_data"
    _test_file = "test_tasks.jsonl"
    difficulty = "medium"  # easy, medium, or hard
    
    def build_prompt(self, item: dict) -> str:
        """Build the prompt shown to the agent."""
        return f"Solve this problem: {item['problem']}"
    
    def grade(self, item: dict, result: ExecutionResult) -> float:
        """Grade the execution result (return 0.0-1.0)."""
        if result.syntax_error:
            return 0.1
        # Add your grading logic
        return 1.0 if result.stdout.strip() == item['answer'] else 0.0
```

2. **Add test data** in JSONL format at `clinical_bench/data/your_task_data/test_tasks.jsonl`:

```jsonl
{"problem": "Calculate 2+2", "answer": "4"}
{"problem": "Calculate 3*3", "answer": "9"}
```

3. **Register your task** in `clinical_bench/server/tasks/__init__.py`:

```python
from .your_task import YourTask

TASK_REGISTRY = {
    "clinical_calc": ClinicalCalcTask,
    "biostat_power": BiostatPowerTask,
    "biocoder": BiocoderTask,
    "your_task": YourTask,  # Add here
}
```

4. **Update `openenv.yaml`** to include your task metadata.

### Adding Test Cases

To add more problems to existing tasks:

1. Open the appropriate JSONL file in `clinical_bench/data/<task_name>/`
2. Add new lines following the existing schema
3. Ensure proper JSON formatting

**Example for clinical_calc:**
```jsonl
{
  "Patient Note": "45-year-old female, height 165cm, weight 70kg",
  "Question": "Calculate BMI",
  "Ground Truth Answer": 25.7,
  "Lower Limit": 25.5,
  "Upper Limit": 25.9
}
```

### Improving Graders

If you have ideas for better grading:

1. Open the relevant task file (e.g., `clinical_bench/server/tasks/clinical_calc.py`)
2. Modify the `grade()` method
3. **Add unit tests** in `tests/test_graders.py` to validate your changes
4. Run tests: `pytest tests/ -v`

### Documentation

Help improve the docs:

- Fix typos or unclear explanations in `README.md`
- Add more examples to the walkthrough section
- Translate docs to other languages

## 🧪 Running Tests

### Install dev dependencies

```bash
pip install -r requirements.txt
pip install pytest mypy ruff
```

### Run tests

```bash
# All tests
pytest tests/ -v

# Specific test file
pytest tests/test_graders.py -v

# Type checking
mypy clinical_bench/ --ignore-missing-imports

# Linting
ruff check clinical_bench/
```

### Test Docker

```bash
docker build -t clinical-bench:test .
docker run -p 8080:8080 clinical-bench:test

# In another terminal
curl http://localhost:8080/health
```

## 📝 Code Style

- **Python version:** 3.11+
- **Style guide:** Follow PEP 8
- **Type hints:** Add type hints to all public functions
- **Docstrings:** Use Google-style docstrings

### Example

```python
def calculate_score(result: ExecutionResult, answer: str) -> float:
    """
    Calculate the score for an execution result.
    
    Args:
        result: The execution result from the sandbox
        answer: The expected answer
        
    Returns:
        Score between 0.0 and 1.0
        
    Raises:
        ValueError: If answer is empty
    """
    if not answer:
        raise ValueError("Answer cannot be empty")
    
    return 1.0 if result.stdout.strip() == answer else 0.0
```

## 🚀 Submitting Changes

1. **Fork the repository**
2. **Create a branch:** `git checkout -b feature/your-feature`
3. **Make your changes**
4. **Run tests:** `pytest tests/ -v`
5. **Commit:** `git commit -m "Add feature: your feature description"`
6. **Push:** `git push origin feature/your-feature`
7. **Create a Pull Request** with a clear description

### PR Checklist

- [ ] Tests pass locally
- [ ] Added tests for new features
- [ ] Updated documentation
- [ ] Followed code style guidelines
- [ ] No merge conflicts with main branch

## 🏆 Submitting to Leaderboard

Want to benchmark your model? Submit your results!

1. **Run inference:**
   ```bash
   export HF_TOKEN=your_token
   export MODEL_NAME=your_model
   python inference.py > results/your_model_$(date +%Y%m%d).log 2>&1
   ```

2. **Create PR with your log file** in `results/` folder

3. **Include in PR description:**
   - Model name and size
   - API provider used
   - Any special settings (temperature, max_tokens, etc.)
   - Date of run

## 💡 Ideas for Contributions

Looking for something to work on? Try these:

### High Priority
- [ ] Add more clinical calculator problems
- [ ] Improve BioCoder grading (currently token overlap)
- [ ] Add visualization tools for error analysis
- [ ] Create Jupyter notebook tutorials

### Medium Priority
- [ ] Add multi-turn conversation support
- [ ] Implement curriculum learning mode
- [ ] Create model comparison dashboard
- [ ] Add more comprehensive unit tests

### Nice to Have
- [ ] Support for R or Julia code (not just Python)
- [ ] Web-based demo with live leaderboard
- [ ] Integration with popular RL frameworks (Stable-Baselines3, etc.)

## ❓ Questions?

- **Issues:** Open an issue on GitHub
- **Discussions:** Use GitHub Discussions for questions
- **Documentation:** Check the main README first

## 📜 Code of Conduct

Be respectful and constructive. We're all here to build something useful!

## 🙏 Attribution

Major contributions will be acknowledged in:
- `README.md` Contributors section
- Release notes
- Academic citations (if applicable)

---

Thank you for contributing to ClinicalBench! 🏥
