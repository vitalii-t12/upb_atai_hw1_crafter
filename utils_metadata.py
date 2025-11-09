"""
Metadata collection utilities for experiment tracking.
Collects system info, git info, package versions, etc.
"""

import os
import sys
import platform
import subprocess
import json
from datetime import datetime
import socket


def get_git_info():
    """Get git repository information."""
    try:
        # Get current commit hash
        commit_hash = subprocess.check_output(
            ['git', 'rev-parse', 'HEAD'],
            stderr=subprocess.DEVNULL
        ).decode('utf-8').strip()

        # Get branch name
        branch = subprocess.check_output(
            ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
            stderr=subprocess.DEVNULL
        ).decode('utf-8').strip()

        # Check if there are uncommitted changes
        status = subprocess.check_output(
            ['git', 'status', '--porcelain'],
            stderr=subprocess.DEVNULL
        ).decode('utf-8').strip()

        has_uncommitted = len(status) > 0

        return {
            'commit_hash': commit_hash,
            'commit_short': commit_hash[:7],
            'branch': branch,
            'has_uncommitted_changes': has_uncommitted,
            'uncommitted_files': status if has_uncommitted else None
        }
    except (subprocess.CalledProcessError, FileNotFoundError):
        return {
            'commit_hash': 'N/A',
            'commit_short': 'N/A',
            'branch': 'N/A',
            'has_uncommitted_changes': False,
            'uncommitted_files': None
        }


def get_gpu_info():
    """Get GPU information using nvidia-smi."""
    try:
        result = subprocess.check_output(
            ['nvidia-smi', '--query-gpu=name,driver_version,memory.total',
             '--format=csv,noheader'],
            stderr=subprocess.DEVNULL
        ).decode('utf-8').strip()

        gpus = []
        for line in result.split('\n'):
            parts = line.split(', ')
            if len(parts) >= 3:
                gpus.append({
                    'name': parts[0],
                    'driver_version': parts[1],
                    'memory_total': parts[2]
                })

        return gpus
    except (subprocess.CalledProcessError, FileNotFoundError):
        return []


def get_package_versions():
    """Get versions of key packages."""
    packages = {}

    try:
        import torch
        packages['torch'] = torch.__version__
        packages['cuda_available'] = torch.cuda.is_available()
        if torch.cuda.is_available():
            packages['cuda_version'] = torch.version.cuda
            packages['cudnn_version'] = torch.backends.cudnn.version()
    except ImportError:
        packages['torch'] = 'N/A'

    try:
        import numpy
        packages['numpy'] = numpy.__version__
    except ImportError:
        packages['numpy'] = 'N/A'

    try:
        import crafter
        packages['crafter'] = crafter.__version__ if hasattr(crafter, '__version__') else 'unknown'
    except ImportError:
        packages['crafter'] = 'N/A'

    packages['python'] = sys.version

    return packages


def get_system_info():
    """Get system information."""
    return {
        'hostname': socket.gethostname(),
        'platform': platform.platform(),
        'system': platform.system(),
        'release': platform.release(),
        'machine': platform.machine(),
        'processor': platform.processor(),
        'python_version': platform.python_version(),
        'cpu_count': os.cpu_count(),
    }


def collect_metadata(experiment_name, args_dict):
    """
    Collect comprehensive metadata for an experiment.

    Args:
        experiment_name: Name of the experiment
        args_dict: Dictionary of experiment arguments

    Returns:
        metadata: Dictionary with all metadata
    """
    metadata = {
        'experiment_name': experiment_name,
        'timestamp_start': datetime.now().isoformat(),
        'timestamp_start_unix': datetime.now().timestamp(),
        'git': get_git_info(),
        'system': get_system_info(),
        'gpu': get_gpu_info(),
        'packages': get_package_versions(),
        'arguments': args_dict,
        'environment': {
            'user': os.environ.get('USER', 'unknown'),
            'cwd': os.getcwd(),
            'python_executable': sys.executable,
        }
    }

    return metadata


def save_metadata(metadata, filepath):
    """Save metadata to JSON file."""
    with open(filepath, 'w') as f:
        json.dump(metadata, f, indent=2)


def update_metadata_end(filepath, training_stats=None):
    """
    Update metadata with end timestamp and training statistics.

    Args:
        filepath: Path to metadata JSON file
        training_stats: Optional dict with final training statistics
    """
    with open(filepath, 'r') as f:
        metadata = json.load(f)

    metadata['timestamp_end'] = datetime.now().isoformat()
    metadata['timestamp_end_unix'] = datetime.now().timestamp()

    # Calculate duration
    start = metadata['timestamp_start_unix']
    end = metadata['timestamp_end_unix']
    duration_seconds = end - start

    metadata['duration'] = {
        'seconds': duration_seconds,
        'minutes': duration_seconds / 60,
        'hours': duration_seconds / 3600,
        'human_readable': format_duration(duration_seconds)
    }

    # Add training statistics if provided
    if training_stats:
        metadata['training_stats'] = training_stats

    with open(filepath, 'w') as f:
        json.dump(metadata, f, indent=2)


def format_duration(seconds):
    """Format duration in human-readable format."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)

    if hours > 0:
        return f"{hours}h {minutes}m {secs}s"
    elif minutes > 0:
        return f"{minutes}m {secs}s"
    else:
        return f"{secs}s"


def format_metadata_summary(metadata):
    """Format metadata as human-readable summary."""
    lines = []
    lines.append("=" * 70)
    lines.append(f"Experiment: {metadata['experiment_name']}")
    lines.append("=" * 70)

    # Timing
    lines.append(f"\nStart Time: {metadata['timestamp_start']}")
    if 'timestamp_end' in metadata:
        lines.append(f"End Time: {metadata['timestamp_end']}")
        lines.append(f"Duration: {metadata['duration']['human_readable']}")

    # Git info
    git = metadata['git']
    lines.append(f"\nGit Info:")
    lines.append(f"  Commit: {git['commit_short']} ({git['branch']})")
    if git['has_uncommitted_changes']:
        lines.append(f"  WARNING: Uncommitted changes present!")

    # System info
    sys_info = metadata['system']
    lines.append(f"\nSystem Info:")
    lines.append(f"  Hostname: {sys_info['hostname']}")
    lines.append(f"  Platform: {sys_info['platform']}")
    lines.append(f"  CPU Count: {sys_info['cpu_count']}")

    # GPU info
    if metadata['gpu']:
        lines.append(f"\nGPU Info:")
        for i, gpu in enumerate(metadata['gpu']):
            lines.append(f"  GPU {i}: {gpu['name']}")
            lines.append(f"    Memory: {gpu['memory_total']}")
            lines.append(f"    Driver: {gpu['driver_version']}")

    # Package versions
    pkg = metadata['packages']
    lines.append(f"\nPackage Versions:")
    lines.append(f"  PyTorch: {pkg.get('torch', 'N/A')}")
    if pkg.get('cuda_available'):
        lines.append(f"  CUDA: {pkg.get('cuda_version', 'N/A')}")
    lines.append(f"  NumPy: {pkg.get('numpy', 'N/A')}")
    lines.append(f"  Crafter: {pkg.get('crafter', 'N/A')}")

    # Arguments
    lines.append(f"\nExperiment Arguments:")
    for key, value in sorted(metadata['arguments'].items()):
        lines.append(f"  {key}: {value}")

    # Training statistics (if available)
    if 'training_stats' in metadata:
        stats = metadata['training_stats']
        lines.append(f"\nFinal Training Statistics:")
        if 'final_eval_reward_mean' in stats:
            lines.append(f"  Final Eval Reward: {stats['final_eval_reward_mean']:.2f} ± {stats.get('final_eval_reward_std', 0):.2f}")
        if 'best_eval_reward' in stats:
            lines.append(f"  Best Eval Reward: {stats['best_eval_reward']:.2f}")
        if 'total_episodes' in stats:
            lines.append(f"  Total Episodes: {stats['total_episodes']}")
        if 'final_loss' in stats:
            lines.append(f"  Final Loss: {stats['final_loss']:.4f}")
        if 'final_epsilon' in stats:
            lines.append(f"  Final Epsilon: {stats['final_epsilon']:.4f}")

    lines.append("=" * 70)

    return '\n'.join(lines)


if __name__ == '__main__':
    """Test metadata collection."""
    test_metadata = collect_metadata('test-experiment', {
        'lr': 1e-4,
        'batch_size': 32,
        'steps': 1000000
    })

    print(format_metadata_summary(test_metadata))

    # Save to test file
    save_metadata(test_metadata, 'test_metadata.json')
    print("\nSaved to test_metadata.json")
