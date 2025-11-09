"""
Wrapper for Crafter environment with preprocessing and logging.
Based on starter code structure.
"""

import numpy as np
import crafter


class CrafterWrapper:
  """
    Wrapper for Crafter environment that provides:
    - Observation preprocessing (convert to CHW format)
    - Achievement tracking
    - Episode statistics logging
    """

  def __init__(self, env_reward=True, log_dir=None, seed=None):
    """
        Initialize Crafter wrapper.

        Args:
            env_reward: Whether to use environment rewards (True) or unsupervised (False)
            log_dir: Directory for logging (optional)
            seed: Random seed (optional)
        """
    # Create Crafter environment
    self.env = crafter.Env(reward=env_reward, size=(64, 64))

    self.log_dir = log_dir
    self.env_reward = env_reward

    if seed is not None:
      self.env.seed(seed)

    # Episode tracking
    self.episode_achievements = {}
    self.episode_return = 0
    self.episode_length = 0

    # Achievement tracking across all episodes
    self.all_achievements = set()

  @property
  def observation_space(self):
    """Return observation space (modified to CHW format)."""
    # Crafter gives HWC (64, 64, 3), we want CHW (3, 64, 64)
    return type('Space', (), {
      'shape': (3, 64, 64),
      'dtype': np.float32
    })()

  @property
  def action_space(self):
    """Return action space."""
    return type('Space', (), {
      'n': self.env.action_space.n
    })()

  def reset(self):
    """
        Reset environment and return initial observation.

        Returns:
            obs: Initial observation in CHW format (3, 64, 64)
        """
    # Reset episode tracking
    self.episode_achievements = {}
    self.episode_return = 0
    self.episode_length = 0

    # Reset environment
    obs = self.env.reset()

    # Convert from HWC to CHW and normalize
    obs = self._preprocess_observation(obs)

    return obs

  def step(self, action):
    """
        Take a step in the environment.

        Args:
            action: Action to take (int)

        Returns:
            obs: Next observation (3, 64, 64)
            reward: Reward received
            done: Whether episode ended
            info: Additional information dictionary
        """
    # Take step
    obs, reward, done, info = self.env.step(action)

    # Preprocess observation
    obs = self._preprocess_observation(obs)

    # Track episode stats
    self.episode_return += reward
    self.episode_length += 1

    # Track achievements
    if 'achievements' in info:
      for achievement, unlocked in info['achievements'].items():
        if unlocked:
          self.episode_achievements[achievement] = \
            self.episode_achievements.get(achievement, 0) + 1
          self.all_achievements.add(achievement)

    # Add episode info if done
    if done:
      info['episode_return'] = self.episode_return
      info['episode_length'] = self.episode_length
      info['episode_achievements'] = self.episode_achievements.copy()
      info['num_achievements_unlocked'] = len(self.episode_achievements)

    return obs, reward, done, info

  def _preprocess_observation(self, obs):
    """
        Preprocess observation: HWC -> CHW and normalize to [0, 1].

        Args:
            obs: Observation in HWC format (64, 64, 3) with values in [0, 255]

        Returns:
            processed: Observation in CHW format (3, 64, 64) with values in [0, 1]
        """
    # Convert from HWC to CHW
    obs = np.transpose(obs, (2, 0, 1))

    # Normalize to [0, 1]
    obs = obs.astype(np.float32) / 255.0

    return obs

  def close(self):
    """Close the environment."""
    self.env.close()

  def seed(self, seed):
    """Set random seed."""
    self.env.seed(seed)

  def render(self, mode='rgb_array'):
    """Render the environment."""
    return self.env.render(mode=mode)

  def get_achievement_summary(self):
    """
        Get summary of achievements unlocked throughout training.

        Returns:
            summary: Dictionary with achievement statistics
        """
    return {
      'total_achievements_discovered': len(self.all_achievements),
      'achievements': list(self.all_achievements)
    }