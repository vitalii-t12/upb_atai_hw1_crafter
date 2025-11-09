"""
Plot evaluation performance for Crafter agent.
Aggregates results across multiple seeds and plots mean with confidence intervals.
"""

import argparse
import json
from pathlib import Path
import numpy as np
import matplotlib

matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
from collections import defaultdict


def load_metrics(log_dir):
  """Load metrics from a log directory."""
  metrics_file = Path(log_dir) / 'metrics.json'

  if not metrics_file.exists():
    print(f"Warning: {metrics_file} does not exist")
    return None

  with open(metrics_file, 'r') as f:
    return json.load(f)


def aggregate_runs(log_dirs):
  """
    Aggregate metrics across multiple runs.

    Args:
        log_dirs: List of log directories

    Returns:
        aggregated: Dict of metric_name -> {steps, mean, std, min, max}
    """
  all_metrics = []

  for log_dir in log_dirs:
    metrics = load_metrics(log_dir)
    if metrics is not None:
      all_metrics.append(metrics)

  if not all_metrics:
    return {}

  aggregated = {}

  # Get all metric names
  metric_names = set()
  for metrics in all_metrics:
    metric_names.update(metrics['metrics'].keys())

  # Aggregate each metric
  for name in metric_names:
    values_by_step = defaultdict(list)

    # Collect values from all runs
    for metrics in all_metrics:
      if name in metrics['metrics']:
        steps = metrics['steps'][name]
        values = metrics['metrics'][name]

        for step, value in zip(steps, values):
          values_by_step[step].append(value)

    # Compute statistics
    steps = sorted(values_by_step.keys())
    means = [np.mean(values_by_step[s]) for s in steps]
    stds = [np.std(values_by_step[s]) for s in steps]
    mins = [np.min(values_by_step[s]) for s in steps]
    maxs = [np.max(values_by_step[s]) for s in steps]

    aggregated[name] = {
      'steps': steps,
      'mean': means,
      'std': stds,
      'min': mins,
      'max': maxs,
      'num_runs': len(log_dirs)
    }

  return aggregated


def plot_metric(ax, data, title, ylabel, smoothing=0.0):
  """
    Plot a single metric with mean and confidence interval.

    Args:
        ax: Matplotlib axis
        data: Dictionary with steps, mean, std
        title: Plot title
        ylabel: Y-axis label
        smoothing: Smoothing factor (0 = no smoothing)
    """
  steps = np.array(data['steps'])
  mean = np.array(data['mean'])
  std = np.array(data['std'])

  # Apply smoothing if requested
  if smoothing > 0:
    mean = exponential_smoothing(mean, smoothing)
    std = exponential_smoothing(std, smoothing)

  # Plot mean
  ax.plot(steps, mean, linewidth=2, label=f"Mean ({data['num_runs']} runs)")

  # Plot confidence interval (mean ± std)
  ax.fill_between(steps, mean - std, mean + std, alpha=0.3)

  # Plot min/max range (lighter)
  if 'min' in data and 'max' in data:
    ax.fill_between(steps, data['min'], data['max'], alpha=0.1, label='Min/Max range')

  ax.set_xlabel('Training Steps')
  ax.set_ylabel(ylabel)
  ax.set_title(title)
  ax.legend()
  ax.grid(True, alpha=0.3)


def exponential_smoothing(values, weight=0.9):
  """Apply exponential moving average smoothing."""
  smoothed = []
  last = values[0] if len(values) > 0 else 0

  for value in values:
    smoothed_val = last * weight + value * (1 - weight)
    smoothed.append(smoothed_val)
    last = smoothed_val

  return np.array(smoothed)


def plot_achievements_spectrum(ax, achievements_data, title="Achievement Success Rates"):
  """
    Plot achievement success rates as a bar chart.

    Args:
        ax: Matplotlib axis
        achievements_data: Dict of achievement -> success rate
        title: Plot title
    """
  if not achievements_data:
    return

  # Sort achievements by success rate
  sorted_achievements = sorted(achievements_data.items(), key=lambda x: x[1], reverse=True)

  names = [name.replace('eval/achievement_', '').replace('_', ' ').title()
           for name, _ in sorted_achievements]
  rates = [rate for _, rate in sorted_achievements]

  # Create bar plot
  y_pos = np.arange(len(names))
  ax.barh(y_pos, rates, align='center', alpha=0.7)
  ax.set_yticks(y_pos)
  ax.set_yticklabels(names, fontsize=8)
  ax.invert_yaxis()  # Highest at top
  ax.set_xlabel('Success Rate (%)')
  ax.set_title(title)
  ax.grid(True, axis='x', alpha=0.3)


def plot_all_results(aggregated, save_dir, smoothing=0.9):
  """
    Create comprehensive plots of all results.

    Args:
        aggregated: Aggregated metrics dictionary
        save_dir: Directory to save plots
        smoothing: Smoothing factor for curves
    """
  save_dir = Path(save_dir)
  save_dir.mkdir(parents=True, exist_ok=True)

  # 1. Plot training and evaluation rewards
  fig, axes = plt.subplots(1, 2, figsize=(15, 5))

  if 'train/episode_reward' in aggregated:
    plot_metric(axes[0], aggregated['train/episode_reward'],
                'Training Episode Reward', 'Reward', smoothing)

  if 'eval/mean_reward' in aggregated:
    plot_metric(axes[1], aggregated['eval/mean_reward'],
                'Evaluation Mean Reward', 'Reward', 0)  # No smoothing for eval

  plt.tight_layout()
  plt.savefig(save_dir / 'rewards.png', dpi=300, bbox_inches='tight')
  print(f"Saved rewards plot to {save_dir / 'rewards.png'}")
  plt.close()

  # 2. Plot training metrics (loss, Q-values)
  # Only plot key metrics, not achievements
  training_metrics = [k for k in aggregated.keys()
                      if k.startswith('train/')
                      and 'episode' not in k
                      and 'achievement' not in k]  # Exclude achievement tracking from this plot

  if training_metrics:
    n_metrics = len(training_metrics)
    # Limit to max 4 metrics side-by-side, use rows if more
    if n_metrics <= 4:
      ncols = n_metrics
      nrows = 1
    else:
      ncols = 4
      nrows = (n_metrics + 3) // 4

    fig, axes = plt.subplots(nrows, ncols, figsize=(5 * ncols, 5 * nrows))

    if n_metrics == 1:
      axes = [axes]
    else:
      axes = axes.flatten() if n_metrics > 1 else [axes]

    for i, metric_name in enumerate(training_metrics):
      ylabel = metric_name.split('/')[-1].replace('_', ' ').title()
      plot_metric(axes[i], aggregated[metric_name],
                  ylabel, ylabel, smoothing)

    # Hide unused subplots
    for i in range(n_metrics, len(axes)):
      axes[i].set_visible(False)

    plt.tight_layout()
    plt.savefig(save_dir / 'training_metrics.png', dpi=300, bbox_inches='tight')
    print(f"Saved training metrics plot to {save_dir / 'training_metrics.png'}")
    plt.close()

  # 3. Plot achievement spectrum
  achievement_metrics = {k: v for k, v in aggregated.items()
                         if k.startswith('eval/achievement_')}

  if achievement_metrics:
    # Get final values (last step)
    final_achievements = {}
    for name, data in achievement_metrics.items():
      if len(data['mean']) > 0:
        final_achievements[name] = data['mean'][-1]

    fig, ax = plt.subplots(figsize=(10, 8))
    plot_achievements_spectrum(ax, final_achievements,
                               'Final Achievement Success Rates')
    plt.tight_layout()
    plt.savefig(save_dir / 'achievement_spectrum.png', dpi=300, bbox_inches='tight')
    print(f"Saved achievement spectrum to {save_dir / 'achievement_spectrum.png'}")
    plt.close()

  # 4. Summary plot: Reward + Episode Length
  fig, axes = plt.subplots(2, 1, figsize=(12, 10))

  if 'eval/mean_reward' in aggregated:
    plot_metric(axes[0], aggregated['eval/mean_reward'],
                'Evaluation Performance', 'Mean Reward', 0)

  if 'eval/mean_length' in aggregated:
    plot_metric(axes[1], aggregated['eval/mean_length'],
                'Episode Length', 'Steps', 0)

  plt.tight_layout()
  plt.savefig(save_dir / 'summary.png', dpi=300, bbox_inches='tight')
  print(f"Saved summary plot to {save_dir / 'summary.png'}")
  plt.close()


def print_final_statistics(aggregated):
  """Print final performance statistics."""
  print("\n" + "=" * 60)
  print("FINAL PERFORMANCE STATISTICS")
  print("=" * 60)

  # Evaluation reward
  if 'eval/mean_reward' in aggregated:
    data = aggregated['eval/mean_reward']
    if len(data['mean']) > 0:
      final_reward = data['mean'][-1]
      final_std = data['std'][-1]
      print(f"Final Eval Reward: {final_reward:.2f} ± {final_std:.2f}")

  # Achievement count
  achievement_metrics = [k for k in aggregated.keys() if k.startswith('eval/achievement_')]
  if achievement_metrics:
    unlocked = sum(1 for k in achievement_metrics if aggregated[k]['mean'][-1] > 5.0)
    print(f"Achievements Unlocked (>5%): {unlocked}/22")

  # Crafter score (geometric mean of achievement rates)
  if achievement_metrics:
    final_rates = [aggregated[k]['mean'][-1] for k in achievement_metrics]
    # Crafter score formula: exp(mean(log(rate + 1))) - 1
    rates_plus_one = [r + 1 for r in final_rates]
    geo_mean = np.exp(np.mean(np.log(rates_plus_one)))
    crafter_score = geo_mean - 1
    print(f"Crafter Score: {crafter_score:.2f}%")

  print("=" * 60 + "\n")


def main():
  parser = argparse.ArgumentParser(description='Plot Crafter agent performance')
  parser.add_argument('--logdir', type=str, required=True,
                      help='Log directory (can contain multiple runs as subdirectories)')
  parser.add_argument('--smoothing', type=float, default=0.9,
                      help='Smoothing factor for training curves')
  parser.add_argument('--save-dir', type=str, default=None,
                      help='Directory to save plots (default: logdir/plots)')

  args = parser.parse_args()

  logdir = Path(args.logdir)

  # Find all run directories (look for subdirectories with metrics.json)
  run_dirs = []

  if (logdir / 'metrics.json').exists():
    # Single run
    run_dirs = [logdir]
  else:
    # Multiple runs (look for numbered subdirectories)
    for subdir in sorted(logdir.iterdir()):
      if subdir.is_dir() and (subdir / 'metrics.json').exists():
        run_dirs.append(subdir)

  if not run_dirs:
    print(f"Error: No runs found in {logdir}")
    return

  print(f"Found {len(run_dirs)} run(s) in {logdir}")
  for run_dir in run_dirs:
    print(f"  - {run_dir}")

  # Aggregate results
  print("\nAggregating results...")
  aggregated = aggregate_runs(run_dirs)

  if not aggregated:
    print("Error: No metrics found to plot")
    return

  # Determine save directory
  if args.save_dir:
    save_dir = Path(args.save_dir)
  else:
    save_dir = logdir / 'plots'

  # Create plots
  print(f"\nCreating plots...")
  plot_all_results(aggregated, save_dir, args.smoothing)

  # Print final statistics
  print_final_statistics(aggregated)

  print(f"\nAll plots saved to {save_dir}")


if __name__ == '__main__':
  main()