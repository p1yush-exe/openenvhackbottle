"""
Leaderboard generator for ClinicalBench.

Parses inference.py output logs and generates a markdown leaderboard.

Usage:
    # Run inference and save output
    python inference.py > results/gpt4_baseline.log 2>&1
    
    # Generate leaderboard
    python scripts/generate_leaderboard.py results/*.log

Output: LEADERBOARD.md
"""

import argparse
import json
import re
from pathlib import Path
from datetime import datetime
from typing import List, Dict


def parse_inference_log(filepath: Path) -> Dict:
    """
    Parse inference.py output log and extract scores.
    
    Expected format:
        [START] task=clinical_calc env=clinical_bench model=gpt-4
        [STEP] step=1 action=... reward=0.30 done=false error=null
        [END] success=true steps=2 score=1.00 rewards=0.30,1.00
    """
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Extract model name from first [START] line
    start_match = re.search(r'\[START\].*model=([^\s]+)', content)
    if not start_match:
        print(f"Warning: No model name found in {filepath}")
        return None
    
    model_name = start_match.group(1)
    
    # Extract all [END] lines
    end_pattern = r'\[END\]\s+success=(\w+)\s+steps=(\d+)\s+score=([\d.]+)\s+rewards=([\d.,]+)'
    episodes = []
    
    for match in re.finditer(end_pattern, content):
        success = match.group(1) == 'true'
        steps = int(match.group(2))
        score = float(match.group(3))
        
        episodes.append({
            'success': success,
            'steps': steps,
            'score': score
        })
    
    if not episodes:
        print(f"Warning: No episodes found in {filepath}")
        return None
    
    # Extract task-level summaries
    task_pattern = r'# Task (\w+): avg_score=([\d.]+) \((\d+)/(\d+) solved\)'
    tasks = {}
    
    for match in re.finditer(task_pattern, content):
        task_name = match.group(1)
        avg_score = float(match.group(2))
        solved = int(match.group(3))
        total = int(match.group(4))
        
        tasks[task_name] = {
            'avg_score': avg_score,
            'solved': solved,
            'total': total,
            'solve_rate': solved / total if total > 0 else 0.0
        }
    
    # Extract overall average
    overall_match = re.search(r'# Overall avg_score=([\d.]+)', content)
    overall_score = float(overall_match.group(1)) if overall_match else 0.0
    
    return {
        'model': model_name,
        'filepath': filepath.name,
        'date': datetime.fromtimestamp(filepath.stat().st_mtime).strftime('%Y-%m-%d'),
        'overall_score': overall_score,
        'tasks': tasks,
        'num_episodes': len(episodes),
        'total_steps': sum(ep['steps'] for ep in episodes),
        'avg_steps': sum(ep['steps'] for ep in episodes) / len(episodes)
    }


def generate_leaderboard(results: List[Dict]) -> str:
    """Generate markdown leaderboard table."""
    
    # Sort by overall score (descending)
    sorted_results = sorted(results, key=lambda x: x['overall_score'], reverse=True)
    
    md = """# 🏆 ClinicalBench Leaderboard

**Last updated:** {date}

Submit your results via PR! Run inference and share your log files.

## Overall Rankings

| Rank | Model | Overall | Easy<br>(clinical_calc) | Medium<br>(biostat_power) | Hard<br>(biocoder) | Episodes | Avg Steps | Date |
|------|-------|---------|-------------------------|---------------------------|-------------------|----------|-----------|------|
""".format(date=datetime.now().strftime('%Y-%m-%d %H:%M UTC'))
    
    for i, entry in enumerate(sorted_results, 1):
        emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else ""
        
        # Extract task scores
        easy = entry['tasks'].get('clinical_calc', {}).get('avg_score', 0.0)
        medium = entry['tasks'].get('biostat_power', {}).get('avg_score', 0.0)
        hard = entry['tasks'].get('biocoder', {}).get('avg_score', 0.0)
        
        md += f"| {emoji} {i} | {entry['model']} | **{entry['overall_score']:.2f}** | {easy:.2f} | {medium:.2f} | {hard:.2f} | {entry['num_episodes']} | {entry['avg_steps']:.1f} | {entry['date']} |\n"
    
    # Add detailed task breakdown
    md += """
## Task Breakdown

### Clinical Calculator (Easy)

| Model | Avg Score | Solve Rate | Problems |
|-------|-----------|------------|----------|
"""
    
    for entry in sorted_results:
        task = entry['tasks'].get('clinical_calc', {})
        if task:
            solve_pct = int(task.get('solve_rate', 0.0) * 100)
            md += f"| {entry['model']} | {task.get('avg_score', 0.0):.2f} | {solve_pct}% | {task.get('solved', 0)}/{task.get('total', 0)} |\n"
    
    md += """
### Biostatistics (Medium)

| Model | Avg Score | Solve Rate | Problems |
|-------|-----------|------------|----------|
"""
    
    for entry in sorted_results:
        task = entry['tasks'].get('biostat_power', {})
        if task:
            solve_pct = int(task.get('solve_rate', 0.0) * 100)
            md += f"| {entry['model']} | {task.get('avg_score', 0.0):.2f} | {solve_pct}% | {task.get('solved', 0)}/{task.get('total', 0)} |\n"
    
    md += """
### BioCoder (Hard)

| Model | Avg Score | Solve Rate | Problems |
|-------|-----------|------------|----------|
"""
    
    for entry in sorted_results:
        task = entry['tasks'].get('biocoder', {})
        if task:
            solve_pct = int(task.get('solve_rate', 0.0) * 100)
            md += f"| {entry['model']} | {task.get('avg_score', 0.0):.2f} | {solve_pct}% | {task.get('solved', 0)}/{task.get('total', 0)} |\n"
    
    md += """
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
"""
    
    return md


def main():
    parser = argparse.ArgumentParser(description='Generate ClinicalBench leaderboard')
    parser.add_argument('logs', nargs='+', type=Path, help='Inference log files')
    parser.add_argument('--output', '-o', type=Path, default='LEADERBOARD.md', help='Output markdown file')
    
    args = parser.parse_args()
    
    print(f"Parsing {len(args.logs)} log files...")
    
    results = []
    for log_file in args.logs:
        if not log_file.exists():
            print(f"Warning: {log_file} not found, skipping")
            continue
        
        result = parse_inference_log(log_file)
        if result:
            results.append(result)
            print(f"  ✓ {log_file.name}: {result['model']} - {result['overall_score']:.2f}")
        else:
            print(f"  ✗ {log_file.name}: Failed to parse")
    
    if not results:
        print("\nError: No valid results found!")
        return
    
    print(f"\nGenerating leaderboard with {len(results)} entries...")
    
    leaderboard = generate_leaderboard(results)
    
    with open(args.output, 'w') as f:
        f.write(leaderboard)
    
    print(f"✅ Leaderboard saved to {args.output}")
    print(f"\n🏆 Top model: {results[0]['model']} ({results[0]['overall_score']:.2f})")


if __name__ == "__main__":
    main()
