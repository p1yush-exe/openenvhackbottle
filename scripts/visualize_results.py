"""
Visualize baseline inference results.

Usage:
    python scripts/visualize_results.py results/baseline.log

Generates: docs/baseline_results.png
"""

import argparse
import re
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from pathlib import Path


def parse_inference_log(filepath: Path):
    """Parse inference log and extract task scores."""
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Extract task summaries
    task_pattern = r'# Task (\w+): avg_score=([\d.]+) \((\d+)/(\d+) solved\)'
    tasks = {}
    
    for match in re.finditer(task_pattern, content):
        task_name = match.group(1)
        avg_score = float(match.group(2))
        solved = int(match.group(3))
        total = int(match.group(4))
        
        tasks[task_name] = {
            'avg_score': avg_score,
            'solve_rate': solved / total if total > 0 else 0.0,
            'solved': solved,
            'total': total
        }
    
    # Extract overall
    overall_match = re.search(r'# Overall avg_score=([\d.]+)', content)
    overall_score = float(overall_match.group(1)) if overall_match else 0.0
    
    return tasks, overall_score


def create_visualization(tasks, overall_score, output_path='docs/baseline_results.png'):
    """Create a visualization of baseline results."""
    
    # Prepare data
    task_order = ['clinical_calc', 'biostat_power', 'biocoder']
    task_labels = {
        'clinical_calc': 'Clinical Calc\n(Easy)',
        'biostat_power': 'Biostat Power\n(Medium)',
        'biocoder': 'BioCoder\n(Hard)'
    }
    
    avg_scores = [tasks.get(t, {}).get('avg_score', 0.0) for t in task_order]
    solve_rates = [tasks.get(t, {}).get('solve_rate', 0.0) for t in task_order]
    labels = [task_labels.get(t, t) for t in task_order]
    
    # Color mapping (green for easy, orange for medium, red for hard)
    colors = ['#2ecc71', '#f39c12', '#e74c3c']
    
    # Create figure with 2 subplots
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    
    # Plot 1: Average Scores
    bars1 = ax1.bar(labels, avg_scores, color=colors, alpha=0.8, edgecolor='black', linewidth=1.5)
    ax1.set_ylabel('Average Score', fontsize=12, fontweight='bold')
    ax1.set_title('Baseline Performance by Task', fontsize=14, fontweight='bold')
    ax1.set_ylim(0, 1.0)
    ax1.axhline(y=overall_score, color='blue', linestyle='--', linewidth=2, label=f'Overall: {overall_score:.2f}')
    ax1.legend(fontsize=10)
    ax1.grid(axis='y', alpha=0.3)
    
    # Add value labels on bars
    for bar, score in zip(bars1, avg_scores):
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height + 0.02,
                f'{score:.2f}',
                ha='center', va='bottom', fontweight='bold', fontsize=11)
    
    # Plot 2: Solve Rates
    bars2 = ax2.bar(labels, solve_rates, color=colors, alpha=0.8, edgecolor='black', linewidth=1.5)
    ax2.set_ylabel('Solve Rate', fontsize=12, fontweight='bold')
    ax2.set_title('Success Rate by Task (Score ≥ 1.0)', fontsize=14, fontweight='bold')
    ax2.set_ylim(0, 1.0)
    ax2.grid(axis='y', alpha=0.3)
    
    # Add percentage labels on bars
    for bar, rate in zip(bars2, solve_rates):
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height + 0.02,
                f'{int(rate * 100)}%',
                ha='center', va='bottom', fontweight='bold', fontsize=11)
    
    # Overall styling
    plt.suptitle('🏥 ClinicalBench Baseline Results', fontsize=16, fontweight='bold', y=0.98)
    plt.tight_layout()
    
    # Save
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"✅ Visualization saved to {output_path}")
    
    # Also save a summary plot
    summary_path = output_path.parent / 'baseline_summary.png'
    
    fig2, ax = plt.subplots(figsize=(10, 6))
    
    # Combined plot
    x = range(len(labels))
    width = 0.35
    
    bars_score = ax.bar([i - width/2 for i in x], avg_scores, width, 
                        label='Avg Score', color='#3498db', alpha=0.8, edgecolor='black')
    bars_solve = ax.bar([i + width/2 for i in x], solve_rates, width,
                        label='Solve Rate', color='#e74c3c', alpha=0.8, edgecolor='black')
    
    ax.set_ylabel('Score / Rate', fontsize=12, fontweight='bold')
    ax.set_title('ClinicalBench Performance Overview', fontsize=14, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_ylim(0, 1.0)
    ax.legend(fontsize=11)
    ax.grid(axis='y', alpha=0.3)
    
    # Add value labels
    for bars in [bars_score, bars_solve]:
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + 0.02,
                    f'{height:.2f}',
                    ha='center', va='bottom', fontsize=9, fontweight='bold')
    
    plt.tight_layout()
    plt.savefig(summary_path, dpi=150, bbox_inches='tight')
    print(f"✅ Summary saved to {summary_path}")


def main():
    parser = argparse.ArgumentParser(description='Visualize ClinicalBench results')
    parser.add_argument('logfile', type=Path, help='Inference log file to visualize')
    parser.add_argument('--output', '-o', type=Path, default='docs/baseline_results.png',
                       help='Output PNG file path')
    
    args = parser.parse_args()
    
    if not args.logfile.exists():
        print(f"Error: {args.logfile} not found!")
        return
    
    print(f"Parsing {args.logfile}...")
    tasks, overall = parse_inference_log(args.logfile)
    
    if not tasks:
        print("Error: No task data found in log file!")
        return
    
    print(f"\nResults:")
    for task_name, data in tasks.items():
        print(f"  {task_name}: {data['avg_score']:.2f} ({data['solved']}/{data['total']} solved)")
    print(f"  Overall: {overall:.2f}")
    
    print(f"\nGenerating visualization...")
    create_visualization(tasks, overall, args.output)
    print("\n✅ Done!")


if __name__ == "__main__":
    main()
