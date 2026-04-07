# 🏆 ClinicalBench Leaderboard

**Last updated:** 2024-04-07

Submit your results via PR! Run inference and share your log files.

## Overall Rankings

| Rank | Model | Overall | Easy<br>(clinical_calc) | Medium<br>(biostat_power) | Hard<br>(biocoder) | Episodes | Avg Steps | Date |
|------|-------|---------|-------------------------|---------------------------|-------------------|----------|-----------|------|
| 🥇 1 | Qwen/Qwen2.5-72B-Instruct | **0.43** | 0.65 | 0.45 | 0.20 | 9 | 3.2 | 2024-04 |

## Task Breakdown

### Clinical Calculator (Easy)

| Model | Avg Score | Solve Rate | Problems |
|-------|-----------|------------|----------|
| Qwen/Qwen2.5-72B-Instruct | 0.65 | 55% | ~165/300 |

### Biostatistics (Medium)

| Model | Avg Score | Solve Rate | Problems |
|-------|-----------|------------|----------|
| Qwen/Qwen2.5-72B-Instruct | 0.45 | 33% | ~34/100 |

### BioCoder (Hard)

| Model | Avg Score | Solve Rate | Problems |
|-------|-----------|------------|----------|
| Qwen/Qwen2.5-72B-Instruct | 0.20 | 10% | ~5/50 |

---

## How to Submit

1. Run the baseline inference script:
   ```bash
   export HF_TOKEN=your_token
   export MODEL_NAME=your_model
   export DATA_PATH=./clinical_bench/data
   python inference.py > results/your_model_$(date +%Y%m%d).log 2>&1
   ```

2. Create a PR with your log file in the `results/` folder

3. The leaderboard will be automatically updated!

---

## Scoring

- **Overall Score:** Average across all tasks (0.0-1.0)
- **Solve Rate:** Percentage of problems with score ≥ 1.0
- **Avg Steps:** Average number of attempts per problem

Higher scores are better! Perfect score = 1.00

---

## 🎯 Challenge Categories

### 🥇 Gold Tier (Overall ≥ 0.70)
*No entries yet - be the first!*

### 🥈 Silver Tier (Overall ≥ 0.50)
*No entries yet*

### 🥉 Bronze Tier (Overall ≥ 0.30)
- Qwen/Qwen2.5-72B-Instruct (0.43)

---

Want to see your model here? Submit your results today! 🚀
