"""
Utility functions for Crafter agent training.
Includes logging, checkpointing, metric tracking, and visualization helpers.
"""

import os
import json
import pickle
from pathlib import Path
from collections import defaultdict

import numpy as np
import torch


class Logger:
  """Simple logger for training metrics."""

  def __init__(self, log_dir):
    """
    Initialize logger.

    Args:
        log_dir: Directory to save logs
    """
    self.log_dir = Path(log_dir)
    self.log_dir.mkdir(parents=True, exist_ok=True)

    # Storage for metrics
    self.metrics = defaultdict(list)
    self.steps = defaultdict(list)

    # File handles
    self.log_file = open(self.log_dir / 'log.txt', 'w')

  def log_scalar(self, tag, value, step):
    """
    Log a scalar value.

    Args:
        tag: Name of the metric (e.g., 'train/loss')
        value: Value to log
        step: Training step
    """
    self.metrics[tag].append(value)
    self.steps[tag].append(step)

  def log_scalars(self, metrics_dict, step, prefix=''):
    """
    Log multiple scalar values.

    Args:
        metrics_dict: Dictionary of metrics
        step: Training step
        prefix: Prefix to add to metric names
    """
    for key, value in metrics_dict.items():
      tag = f"{prefix}/{key}" if prefix else key
      self.log_scalar(tag, value, step)

  def print_and_log(self, message):
    """Print message and write to log file."""
    print(message)
    self.log_file.write(message + '\n')
    self.log_file.flush()

  def save_metrics(self):
    """Save all metrics to JSON file."""
    metrics_dict = {
      'metrics': dict(self.metrics),
      'steps': dict(self.steps)
    }

    with open(self.log_dir / 'metrics.json', 'w') as f:
      # Convert numpy arrays to lists for JSON serialization
      for key in metrics_dict['metrics']:
        metrics_dict['metrics'][key] = [float(v) for v in metrics_dict['metrics'][key]]
        metrics_dict['steps'][key] = [int(s) for s in metrics_dict['steps'][key]]

      json.dump(metrics_dict, f, indent=2)

  def load_metrics(self):
    """Load metrics from JSON file."""
    metrics_file = self.log_dir / 'metrics.json'
    if metrics_file.exists():
      with open(metrics_file, 'r') as f:
        data = json.load(f)
        self.metrics = defaultdict(list, data['metrics'])
        self.steps = defaultdict(list, data['steps'])

  def close(self):
    """Close log file and save metrics."""
    self.save_metrics()
    self.log_file.close()

  def __del__(self):
    """Cleanup when logger is destroyed."""
    if hasattr(self, 'log_file') and not self.log_file.closed:
      self.close()


def save_checkpoint(path, agent, step, logger=None):
  """
  Save training checkpoint.

  Args:
      path: Path to save checkpoint
      agent: DQN agent
      step: Current training step
      logger: Logger instance (optional)
  """
  checkpoint = {
    'step': step,
    'agent_state': {
      'q_network': agent.q_network.state_dict(),
      'target_network': agent.target_network.state_dict(),
      'optimizer': agent.optimizer.state_dict(),
      'train_steps': agent.train_steps
    },
    'config': {
      'obs_shape': agent.obs_shape,
      'n_actions': agent.n_actions,
      'gamma': agent.gamma,
      'batch_size': agent.batch_size,
      'double_dqn': agent.double_dqn,
      'n_step': agent.n_step,
      'munchausen': agent.munchausen
    }
  }

  # Save logger metrics if provided
  if logger is not None:
    logger.save_metrics()
    checkpoint['metrics_path'] = str(logger.log_dir / 'metrics.json')

  torch.save(checkpoint, path)
  print(f"Checkpoint saved to {path}")


def load_checkpoint(path, agent, logger=None):
  """
  Load training checkpoint.

  Args:
      path: Path to checkpoint
      agent: DQN agent
      logger: Logger instance (optional)

  Returns:
      step: Training step at checkpoint
  """
  checkpoint = torch.load(path, map_location=agent.device)

  # Load agent state
  agent.q_network.load_state_dict(checkpoint['agent_state']['q_network'])
  agent.target_network.load_state_dict(checkpoint['agent_state']['target_network'])
  agent.optimizer.load_state_dict(checkpoint['agent_state']['optimizer'])
  agent.train_steps = checkpoint['agent_state']['train_steps']

  # Load logger metrics if available
  if logger is not None and 'metrics_path' in checkpoint:
    logger.load_metrics()

  step = checkpoint['step']
  print(f"Checkpoint loaded from {path} at step {step}")

  return step


def compute_geometric_mean_score(achievement_rates):
  """
  Compute Crafter score as geometric mean of achievement success rates.

  Args:
      achievement_rates: Dictionary of achievement -> success rate (0-100)

  Returns:
      score: Crafter score as percentage
  """
  # Add 1 to handle zero rates (as per Crafter paper)
  rates_plus_one = [rate + 1 for rate in achievement_rates.values()]

  # Geometric mean
  n = len(rates_plus_one)
  if n == 0:
    return 0.0

  product = np.prod(rates_plus_one)
  geo_mean = product ** (1.0 / n)

  # Subtract 1 (as per Crafter formula)
  score = geo_mean - 1

  return score


def aggregate_results(log_dirs):
  """
  Aggregate results across multiple runs (different seeds).

  Args:
      log_dirs: List of log directories from different runs

  Returns:
      aggregated: Dictionary with mean and std for each metric
  """
  all_metrics = []

  for log_dir in log_dirs:
    metrics_file = Path(log_dir) / 'metrics.json'
    if metrics_file.exists():
      with open(metrics_file, 'r') as f:
        metrics = json.load(f)
        all_metrics.append(metrics)

  if not all_metrics:
    return {}

  # Aggregate
  aggregated = {}

  # Get all metric names
  metric_names = set()
  for metrics in all_metrics:
    metric_names.update(metrics['metrics'].keys())

  # Compute mean and std for each metric
  for name in metric_names:
    values_by_step = defaultdict(list)

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

    aggregated[name] = {
      'steps': steps,
      'mean': means,
      'std': stds
    }

  return aggregated


def smooth_curve(values, weight=0.9):
  """
  Exponential moving average smoothing.

  Args:
      values: List of values to smooth
      weight: Smoothing weight (higher = smoother)

  Returns:
      smoothed: Smoothed values
  """
  if len(values) == 0:
    return []

  smoothed = []
  last = values[0]

  for value in values:
    smoothed_val = last * weight + value * (1 - weight)
    smoothed.append(smoothed_val)
    last = smoothed_val

  return smoothed


def format_achievement_table(achievements, achievement_rates):
  """
  Format achievement success rates as a nice table.

  Args:
      achievements: List of achievement names
      achievement_rates: Dictionary of achievement -> rate

  Returns:
      table_str: Formatted table string
  """
  lines = []
  lines.append("Achievement Success Rates:")
  lines.append("-" * 50)
  lines.append(f"{'Achievement':<30} {'Success Rate':>15}")
  lines.append("-" * 50)

  for achievement in sorted(achievements):
    rate = achievement_rates.get(achievement, 0.0)
    lines.append(f"{achievement:<30} {rate:>14.1f}%")

  lines.append("-" * 50)

  # Compute Crafter score
  score = compute_geometric_mean_score(achievement_rates)
  lines.append(f"{'Crafter Score':<30} {score:>14.1f}%")
  lines.append("-" * 50)

  return '\n'.join(lines)


class MovingAverage:
  """Helper class for computing moving averages."""

  def __init__(self, window_size=100):
    """
    Initialize moving average.

    Args:
        window_size: Size of the moving window
    """
    self.window_size = window_size
    self.values = []

  def add(self, value):
    """Add a value to the moving average."""
    self.values.append(value)
    if len(self.values) > self.window_size:
      self.values.pop(0)

  def get(self):
    """Get current moving average."""
    if len(self.values) == 0:
      return 0.0
    return np.mean(self.values)

  def reset(self):
    """Reset the moving average."""
    self.values = []


def setup_experiment_dir(base_dir, experiment_name):
  """
  Setup directory structure for experiment.

  Args:
      base_dir: Base directory for logs
      experiment_name: Name of the experiment

  Returns:
      exp_dir: Path to experiment directory
  """
  exp_dir = Path(base_dir) / experiment_name
  exp_dir.mkdir(parents=True, exist_ok=True)

  # Create subdirectories
  (exp_dir / 'checkpoints').mkdir(exist_ok=True)
  (exp_dir / 'videos').mkdir(exist_ok=True)
  (exp_dir / 'plots').mkdir(exist_ok=True)

  return exp_dir


def count_parameters(model):
  """
  Count trainable parameters in a model.

  Args:
      model: PyTorch model

  Returns:
      count: Number of trainable parameters
  """
  return sum(p.numel() for p in model.parameters() if p.requires_grad)


def get_device_info():
  """Get information about available compute devices."""
  if torch.cuda.is_available():
    device_name = torch.cuda.get_device_name(0)
    device_memory = torch.cuda.get_device_properties(0).total_memory / 1e9
    return f"CUDA: {device_name} ({device_memory:.1f} GB)"
  else:
    return "CPU"