"""
Aggregate results from multiple experimental runs and generate summary tables.
"""

import argparse
import json
from pathlib import Path
import numpy as np
from tabulate import tabulate


def load_final_metrics(log_dir):
  """Load final evaluation metrics from a run."""
  metrics_file = Path(log_dir) / 'metrics.json'

  if not metrics_file.exists():
    return None

  with open(metrics_file, 'r') as f:
    data = json.load(f)

  # Extract final evaluation metrics
  results = {}

  # Get final eval reward
  if 'eval/mean_reward' in data['metrics']:
    rewards = data['metrics']['eval/mean_reward']
    if len(rewards) > 0:
      results['final_reward'] = rewards[-1]

  # Get final achievements
  achievement_keys = [k for k in data['metrics'].keys() if k.startswith('eval/achievement_')]
  achievement_rates = []
  unlocked_count = 0

  for key in achievement_keys:
    values = data['metrics'][key]
    if len(values) > 0:
      rate = values[-1]
      achievement_rates.append(rate)
      if rate > 5.0:  # Consider unlocked if >5% success rate
        unlocked_count += 1

  if achievement_rates:
    results['achievements_unlocked'] = unlocked_count
    results['achievement_rates'] = achievement_rates

    # Compute Crafter score (geometric mean)
    rates_plus_one = [r + 1 for r in achievement_rates]
    geo_mean = np.exp(np.mean(np.log(rates_plus_one)))
    results['crafter_score'] = geo_mean - 1

  return results


def aggregate_experiment(experiment_dir):
  """
  Aggregate results from an experiment with multiple seeds.

  Args:
      experiment_dir: Directory containing runs from different seeds

  Returns:
      summary: Dictionary with mean and std of metrics
  """
  experiment_dir = Path(experiment_dir)

  # Find all seed directories
  seed_dirs = []
  for subdir in sorted(experiment_dir.iterdir()):
    if subdir.is_dir() and (subdir / 'metrics.json').exists():
      seed_dirs.append(subdir)

  if not seed_dirs:
    return None

  # Collect metrics from all seeds
  all_rewards = []
  all_scores = []
  all_achievements = []

  for seed_dir in seed_dirs:
    results = load_final_metrics(seed_dir)
    if results:
      if 'final_reward' in results:
        all_rewards.append(results['final_reward'])
      if 'crafter_score' in results:
        all_scores.append(results['crafter_score'])
      if 'achievements_unlocked' in results:
        all_achievements.append(results['achievements_unlocked'])

  # Compute summary statistics
  summary = {
    'num_seeds': len(seed_dirs),
    'reward_mean': np.mean(all_rewards) if all_rewards else 0.0,
    'reward_std': np.std(all_rewards) if all_rewards else 0.0,
    'score_mean': np.mean(all_scores) if all_scores else 0.0,
    'score_std': np.std(all_scores) if all_scores else 0.0,
    'achievements_mean': np.mean(all_achievements) if all_achievements else 0.0,
    'achievements_std': np.std(all_achievements) if all_achievements else 0.0
  }

  return summary


def generate_comparison_table(experiment_dirs, experiment_names):
  """
  Generate a comparison table of multiple experiments.

  Args:
      experiment_dirs: List of experiment directories
      experiment_names: List of experiment names

  Returns:
      table_str: Formatted table string
  """
  results = []

  for exp_name, exp_dir in zip(experiment_names, experiment_dirs):
    summary = aggregate_experiment(exp_dir)
    if summary:
      results.append([
        exp_name,
        f"{summary['reward_mean']:.2f} ± {summary['reward_std']:.2f}",
        f"{summary['score_mean']:.2f} ± {summary['score_std']:.2f}",
        f"{summary['achievements_mean']:.1f} ± {summary['achievements_std']:.1f}",
        summary['num_seeds']
      ])

  headers = ['Experiment', 'Final Reward', 'Crafter Score (%)', 'Achievements', 'Seeds']

  return tabulate(results, headers=headers, tablefmt='grid')


def main():
  parser = argparse.ArgumentParser(description='Aggregate Crafter experiment results')
  parser.add_argument('--logdir', type=str, required=True,
                      help='Base log directory containing experiments')
  parser.add_argument('--experiments', type=str, nargs='+',
                      help='List of experiment names to compare')
  parser.add_argument('--save', type=str, default=None,
                      help='Save comparison table to file')

  args = parser.parse_args()

  logdir = Path(args.logdir)

  if args.experiments:
    # Compare specific experiments
    experiment_names = args.experiments
    experiment_dirs = [logdir / name for name in experiment_names]
  else:
    # Find all experiment directories
    experiment_dirs = [d for d in logdir.iterdir() if d.is_dir()]
    experiment_names = [d.name for d in experiment_dirs]

  # Generate comparison table
  print("\n" + "=" * 80)
  print("EXPERIMENT COMPARISON")
  print("=" * 80 + "\n")

  table = generate_comparison_table(experiment_dirs, experiment_names)
  print(table)

  # Save if requested
  if args.save:
    with open(args.save, 'w') as f:
      f.write(table)
    print(f"\nTable saved to {args.save}")

  # Print detailed results for each experiment
  print("\n" + "=" * 80)
  print("DETAILED RESULTS")
  print("=" * 80 + "\n")

  for exp_name, exp_dir in zip(experiment_names, experiment_dirs):
    print(f"\nExperiment: {exp_name}")
    print("-" * 40)

    summary = aggregate_experiment(exp_dir)
    if summary:
      print(f"Seeds: {summary['num_seeds']}")
      print(f"Final Reward: {summary['reward_mean']:.2f} ± {summary['reward_std']:.2f}")
      print(f"Crafter Score: {summary['score_mean']:.2f}% ± {summary['score_std']:.2f}%")
      print(f"Achievements: {summary['achievements_mean']:.1f} ± {summary['achievements_std']:.1f}")
    else:
      print("No results found")


if __name__ == '__main__':
  # Try to import tabulate, provide helpful message if not available
  try:
    from tabulate import tabulate
  except ImportError:
    print("Error: tabulate package not found")
    print("Install with: pip install tabulate")
    exit(1)

  main()