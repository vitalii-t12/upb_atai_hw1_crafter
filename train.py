#!/usr/bin/env python3
"""
Main training script for Crafter Deep RL Agent
Supports DQN with various enhancements: Double DQN, Dueling, N-step, Distributional RL
"""

import argparse
import os
import random
import time
from pathlib import Path

import numpy as np
import torch

from agent import DQNAgent
from src.crafter_wrapper import CrafterWrapper
from utils import Logger, save_checkpoint, load_checkpoint
from utils_metadata import collect_metadata, save_metadata, update_metadata_end, format_metadata_summary


def parse_args():
  """Parse command line arguments with default hyperparameters."""
  parser = argparse.ArgumentParser(description='Train DQN agent on Crafter')

  # Environment settings
  parser.add_argument('--env-name', type=str, default='crafter',
                      help='Environment name')
  parser.add_argument('--steps', type=int, default=1_000_000,
                      help='Total training steps')
  parser.add_argument('--eval-interval', type=int, default=50_000,
                      help='Evaluation interval')
  parser.add_argument('--eval-episodes', type=int, default=20,
                      help='Number of evaluation episodes')

  # Training settings
  parser.add_argument('--seed', type=int, default=0,
                      help='Random seed')
  parser.add_argument('--logdir', type=str, default='logdir/dqn-agent/0',
                      help='Log directory')
  parser.add_argument('--device', type=str, default='cuda' if torch.cuda.is_available() else 'cpu',
                      help='Device (cuda/cpu)')

  # Agent hyperparameters (optimized defaults)
  parser.add_argument('--lr', type=float, default=1e-4,
                      help='Learning rate')
  parser.add_argument('--batch-size', type=int, default=32,
                      help='Batch size')
  parser.add_argument('--buffer-size', type=int, default=100_000,
                      help='Replay buffer size')
  parser.add_argument('--gamma', type=float, default=0.99,
                      help='Discount factor')
  parser.add_argument('--target-update-freq', type=int, default=2500,
                      help='Target network update frequency')
  parser.add_argument('--training-starts', type=int, default=5000,
                      help='Steps before training starts')
  parser.add_argument('--update-freq', type=int, default=4,
                      help='Environment steps per gradient update')

  # Exploration
  parser.add_argument('--epsilon-start', type=float, default=1.0,
                      help='Initial epsilon for epsilon-greedy')
  parser.add_argument('--epsilon-end', type=float, default=0.01,
                      help='Final epsilon')
  parser.add_argument('--epsilon-decay-steps', type=int, default=50_000,
                      help='Steps to decay epsilon')

  # Enhancements
  parser.add_argument('--double-dqn', action='store_true', default=False,
                      help='Use Double DQN')
  parser.add_argument('--no-double-dqn', dest='double_dqn', action='store_false',
                      help='Disable Double DQN')
  parser.add_argument('--dueling', action='store_true', default=False,
                      help='Use Dueling architecture')
  parser.add_argument('--no-dueling', dest='dueling', action='store_false',
                      help='Disable Dueling architecture')
  parser.add_argument('--n-step', type=int, default=1,
                      help='N-step returns (1 for standard TD)')
  parser.add_argument('--munchausen', action='store_true', default=False,
                      help='Use Munchausen-DQN')
  parser.add_argument('--munchausen-alpha', type=float, default=0.9,
                      help='Munchausen alpha parameter')
  parser.add_argument('--munchausen-tau', type=float, default=0.03,
                      help='Munchausen tau parameter')

  # Network architecture
  parser.add_argument('--hidden-size', type=int, default=512,
                      help='Hidden layer size')
  parser.add_argument('--grad-clip', type=float, default=10.0,
                      help='Gradient clipping value')

  # Checkpointing
  parser.add_argument('--save-freq', type=int, default=100_000,
                      help='Checkpoint save frequency')
  parser.add_argument('--resume', type=str, default=None,
                      help='Path to checkpoint to resume from')

  return parser.parse_args()


def set_seed(seed):
  """Set random seeds for reproducibility."""
  random.seed(seed)
  np.random.seed(seed)
  torch.manual_seed(seed)
  if torch.cuda.is_available():
    torch.cuda.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False


def evaluate(agent, env, num_episodes=20, device='cpu'):
  """Evaluate agent performance."""
  episode_rewards = []
  episode_lengths = []
  achievements = {}

  for ep in range(num_episodes):
    obs = env.reset()
    done = False
    episode_reward = 0
    episode_length = 0
    episode_achievements = set()  # Track unique achievements this episode

    while not done:
      action = agent.select_action(obs, epsilon=0.0)  # Greedy evaluation
      obs, reward, done, info = env.step(action)
      episode_reward += reward
      episode_length += 1

      # Track achievements (only once per episode)
      if 'achievements' in info:
        for achievement, unlocked in info['achievements'].items():
          if unlocked:
            episode_achievements.add(achievement)

    # Count episodes where each achievement was unlocked
    for achievement in episode_achievements:
      achievements[achievement] = achievements.get(achievement, 0) + 1

    episode_rewards.append(episode_reward)
    episode_lengths.append(episode_length)

  # Calculate success rates (percentage of episodes with achievement)
  achievement_rates = {k: v / num_episodes * 100 for k, v in achievements.items()}

  return {
    'mean_reward': np.mean(episode_rewards),
    'std_reward': np.std(episode_rewards),
    'mean_length': np.mean(episode_lengths),
    'achievements': achievement_rates
  }


def train(args):
  """Main training loop."""
  set_seed(args.seed)
  os.makedirs(args.logdir, exist_ok=True)

  # Initialize logger early
  logger = Logger(args.logdir)

  # Collect and save metadata
  metadata = collect_metadata('training_run', vars(args))
  metadata_path = os.path.join(args.logdir, 'metadata.json')
  save_metadata(metadata, metadata_path)

  # Log metadata summary
  summary = format_metadata_summary(metadata)
  logger.print_and_log(summary)
  logger.print_and_log("")

  # Create environments
  train_env = CrafterWrapper(env_reward=True, log_dir=os.path.join(args.logdir, 'train'))
  eval_env = CrafterWrapper(env_reward=True, log_dir=os.path.join(args.logdir, 'eval'))

  # Create agent
  obs_shape = train_env.observation_space.shape
  n_actions = train_env.action_space.n

  agent = DQNAgent(
    obs_shape=obs_shape,
    n_actions=n_actions,
    device=args.device,
    lr=args.lr,
    gamma=args.gamma,
    buffer_size=args.buffer_size,
    batch_size=args.batch_size,
    double_dqn=args.double_dqn,
    dueling=args.dueling,
    n_step=args.n_step,
    hidden_size=args.hidden_size,
    grad_clip=args.grad_clip,
    munchausen=args.munchausen,
    munchausen_alpha=args.munchausen_alpha,
    munchausen_tau=args.munchausen_tau
  )

  # Resume from checkpoint if specified
  start_step = 0
  if args.resume:
    start_step = load_checkpoint(args.resume, agent, logger)
    logger.print_and_log(f"Resumed from step {start_step}")

  # Training loop
  obs = train_env.reset()
  episode_reward = 0
  episode_length = 0
  episode_num = 0

  start_time = time.time()

  for step in range(start_step, args.steps):
    # Epsilon decay
    epsilon = max(
      args.epsilon_end,
      args.epsilon_start - (args.epsilon_start - args.epsilon_end) *
      min(step / args.epsilon_decay_steps, 1.0)
    )

    # Select action
    action = agent.select_action(obs, epsilon=epsilon)

    # Environment step
    next_obs, reward, done, info = train_env.step(action)

    # Store transition
    agent.store_transition(obs, action, reward, next_obs, done)

    # Update observation
    obs = next_obs
    episode_reward += reward
    episode_length += 1

    # Train agent
    if step >= args.training_starts and step % args.update_freq == 0:
      loss_info = agent.update()
      if loss_info is not None:
        logger.log_scalars(loss_info, step, prefix='train')

    # Update target network
    if step % args.target_update_freq == 0:
      agent.update_target_network()

    # Episode end
    if done:
      logger.log_scalar('train/episode_reward', episode_reward, step)
      logger.log_scalar('train/episode_length', episode_length, step)
      logger.log_scalar('train/epsilon', epsilon, step)

      # Log achievements if available
      if 'episode_achievements' in info:
        for achievement, count in info['episode_achievements'].items():
          logger.log_scalar(f'train/achievement_{achievement}', count, step)

      # Reset episode
      obs = train_env.reset()
      episode_reward = 0
      episode_length = 0
      episode_num += 1

      # Print progress
      if episode_num % 10 == 0:
        elapsed = time.time() - start_time
        fps = step / elapsed if elapsed > 0 else 0
        logger.print_and_log(f"Step: {step}/{args.steps} | Episode: {episode_num} | "
                             f"Epsilon: {epsilon:.3f} | FPS: {fps:.0f}")

    # Evaluation
    if (step + 1) % args.eval_interval == 0:
      logger.print_and_log(f"\n{'='*60}")
      logger.print_and_log(f"Evaluating at step {step + 1}...")
      eval_results = evaluate(agent, eval_env, args.eval_episodes, args.device)

      logger.log_scalar('eval/mean_reward', eval_results['mean_reward'], step)
      logger.log_scalar('eval/std_reward', eval_results['std_reward'], step)
      logger.log_scalar('eval/mean_length', eval_results['mean_length'], step)

      # Log achievement success rates
      for achievement, rate in eval_results['achievements'].items():
        logger.log_scalar(f'eval/achievement_{achievement}', rate, step)

      logger.print_and_log(f"Eval - Mean Reward: {eval_results['mean_reward']:.2f} ± "
                           f"{eval_results['std_reward']:.2f}, "
                           f"Mean Length: {eval_results['mean_length']:.0f}")
      logger.print_and_log(f"Achievements unlocked: {len(eval_results['achievements'])}/22")
      logger.print_and_log(f"{'='*60}\n")

      # Save metrics after each evaluation (for safety in case of crashes)
      logger.save_metrics()

    # Save checkpoint
    if (step + 1) % args.save_freq == 0:
      save_path = os.path.join(args.logdir, f'checkpoint_{step + 1}.pt')
      save_checkpoint(save_path, agent, step + 1, logger)
      logger.print_and_log(f"Saved checkpoint to {save_path}")

  # Final evaluation
  logger.print_and_log("\n" + "="*60)
  logger.print_and_log("FINAL EVALUATION")
  logger.print_and_log("="*60)
  final_results = evaluate(agent, eval_env, args.eval_episodes, args.device)
  logger.print_and_log(f"Final Mean Reward: {final_results['mean_reward']:.2f} ± "
                       f"{final_results['std_reward']:.2f}")
  logger.print_and_log(f"Final Achievements: {len(final_results['achievements'])}/22")

  # Log final achievement details
  if final_results['achievements']:
    logger.print_and_log("\nFinal Achievement Success Rates:")
    for achievement, rate in sorted(final_results['achievements'].items(),
                                     key=lambda x: x[1], reverse=True):
      achievement_name = achievement.replace('eval/achievement_', '')
      logger.print_and_log(f"  {achievement_name}: {rate:.1f}%")

  # Save final model
  save_path = os.path.join(args.logdir, 'final_model.pt')
  save_checkpoint(save_path, agent, args.steps, logger)
  logger.print_and_log(f"\nSaved final model to {save_path}")

  # Close environments
  train_env.close()
  eval_env.close()

  # Update metadata with end time and duration
  update_metadata_end(metadata_path)

  # Save final metrics to disk
  logger.print_and_log(f"Metrics saved to {args.logdir}/metrics.json")
  logger.print_and_log(f"Metadata saved to {metadata_path}")
  logger.print_and_log("="*60)
  logger.print_and_log("TRAINING COMPLETE!")
  logger.print_and_log("="*60)
  logger.close()


if __name__ == '__main__':
  args = parse_args()
  train(args)