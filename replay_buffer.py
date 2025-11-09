"""
Experience Replay Buffer for DQN with N-step returns support.
"""

import numpy as np
from collections import deque


class ReplayBuffer:
  """
  Experience replay buffer for off-policy RL algorithms.
  Supports n-step returns.
  """

  def __init__(self, capacity, obs_shape, n_step=1, gamma=0.99):
    """
    Initialize replay buffer.

    Args:
        capacity: Maximum number of transitions to store
        obs_shape: Shape of observations
        n_step: N-step for returns (default=1 for standard TD)
        gamma: Discount factor for n-step returns
    """
    self.capacity = capacity
    self.obs_shape = obs_shape
    self.n_step = n_step
    self.gamma = gamma

    # Storage
    self.observations = np.zeros((capacity, *obs_shape), dtype=np.uint8)
    self.actions = np.zeros(capacity, dtype=np.int64)
    self.rewards = np.zeros(capacity, dtype=np.float32)
    self.next_observations = np.zeros((capacity, *obs_shape), dtype=np.uint8)
    self.dones = np.zeros(capacity, dtype=np.float32)

    # Pointer and size
    self.ptr = 0
    self.size = 0

  def add(self, obs, action, reward, next_obs, done):
    """
    Add a transition to the buffer.

    Args:
        obs: Current observation
        action: Action taken
        reward: Reward received (can be n-step reward)
        next_obs: Next observation
        done: Whether episode ended
    """
    # Convert observation to uint8 to save memory
    if obs.dtype != np.uint8:
      obs = (obs * 255).astype(np.uint8)
    if next_obs.dtype != np.uint8:
      next_obs = (next_obs * 255).astype(np.uint8)

    # Store transition
    self.observations[self.ptr] = obs
    self.actions[self.ptr] = action
    self.rewards[self.ptr] = reward
    self.next_observations[self.ptr] = next_obs
    self.dones[self.ptr] = done

    # Update pointer and size
    self.ptr = (self.ptr + 1) % self.capacity
    self.size = min(self.size + 1, self.capacity)

  def sample(self, batch_size):
    """
    Sample a batch of transitions.

    Args:
        batch_size: Number of transitions to sample

    Returns:
        Tuple of (observations, actions, rewards, next_observations, dones)
    """
    # Sample random indices
    indices = np.random.randint(0, self.size, size=batch_size)

    # Get batch
    obs = self.observations[indices].astype(np.float32) / 255.0
    actions = self.actions[indices]
    rewards = self.rewards[indices]
    next_obs = self.next_observations[indices].astype(np.float32) / 255.0
    dones = self.dones[indices]

    return obs, actions, rewards, next_obs, dones

  def __len__(self):
    """Return current size of buffer."""
    return self.size


class PrioritizedReplayBuffer:
  """
  Prioritized Experience Replay (PER) buffer.
  Optional enhancement for better sample efficiency.
  """

  def __init__(self, capacity, obs_shape, alpha=0.6, beta_start=0.4, beta_frames=100000):
    """
    Initialize prioritized replay buffer.

    Args:
        capacity: Maximum number of transitions
        obs_shape: Shape of observations
        alpha: Prioritization exponent (0 = uniform, 1 = full prioritization)
        beta_start: Initial importance sampling weight
        beta_frames: Number of frames to anneal beta to 1.0
    """
    self.capacity = capacity
    self.obs_shape = obs_shape
    self.alpha = alpha
    self.beta_start = beta_start
    self.beta_frames = beta_frames
    self.frame = 1

    # Storage
    self.observations = np.zeros((capacity, *obs_shape), dtype=np.uint8)
    self.actions = np.zeros(capacity, dtype=np.int64)
    self.rewards = np.zeros(capacity, dtype=np.float32)
    self.next_observations = np.zeros((capacity, *obs_shape), dtype=np.uint8)
    self.dones = np.zeros(capacity, dtype=np.float32)

    # Priority storage (using sum tree for efficient sampling)
    self.priorities = np.zeros(capacity, dtype=np.float32)
    self.max_priority = 1.0

    self.ptr = 0
    self.size = 0

  def add(self, obs, action, reward, next_obs, done):
    """Add transition with maximum priority."""
    # Convert to uint8
    if obs.dtype != np.uint8:
      obs = (obs * 255).astype(np.uint8)
    if next_obs.dtype != np.uint8:
      next_obs = (next_obs * 255).astype(np.uint8)

    # Store transition
    self.observations[self.ptr] = obs
    self.actions[self.ptr] = action
    self.rewards[self.ptr] = reward
    self.next_observations[self.ptr] = next_obs
    self.dones[self.ptr] = done

    # Set priority to maximum (new transitions are important)
    self.priorities[self.ptr] = self.max_priority

    self.ptr = (self.ptr + 1) % self.capacity
    self.size = min(self.size + 1, self.capacity)

  def sample(self, batch_size):
    """
    Sample batch according to priorities.

    Returns:
        Tuple of (obs, actions, rewards, next_obs, dones, weights, indices)
    """
    # Calculate beta (annealing)
    beta = min(1.0, self.beta_start + self.frame * (1.0 - self.beta_start) / self.beta_frames)
    self.frame += 1

    # Get priorities for current buffer size
    priorities = self.priorities[:self.size]

    # Calculate sampling probabilities
    probs = priorities ** self.alpha
    probs /= probs.sum()

    # Sample indices according to priorities
    indices = np.random.choice(self.size, batch_size, p=probs, replace=False)

    # Calculate importance sampling weights
    weights = (self.size * probs[indices]) ** (-beta)
    weights /= weights.max()  # Normalize

    # Get batch
    obs = self.observations[indices].astype(np.float32) / 255.0
    actions = self.actions[indices]
    rewards = self.rewards[indices]
    next_obs = self.next_observations[indices].astype(np.float32) / 255.0
    dones = self.dones[indices]

    return obs, actions, rewards, next_obs, dones, weights, indices

  def update_priorities(self, indices, priorities):
    """
    Update priorities for sampled transitions.

    Args:
        indices: Indices of transitions
        priorities: New priority values (typically TD errors)
    """
    for idx, priority in zip(indices, priorities):
      self.priorities[idx] = priority + 1e-6  # Small constant to avoid zero priority
      self.max_priority = max(self.max_priority, priority)

  def __len__(self):
    return self.size


class HindsightReplayBuffer(ReplayBuffer):
  """
  Hindsight Experience Replay (HER) buffer.
  Optional enhancement for sparse reward environments like Crafter.
  Relabels failed experiences with achieved goals.
  """

  def __init__(self, capacity, obs_shape, n_step=1, gamma=0.99, her_ratio=0.8):
    """
    Initialize HER buffer.

    Args:
        capacity: Maximum number of transitions
        obs_shape: Shape of observations
        n_step: N-step returns
        gamma: Discount factor
        her_ratio: Ratio of HER samples (0.8 = 80% HER, 20% normal)
    """
    super().__init__(capacity, obs_shape, n_step, gamma)
    self.her_ratio = her_ratio

    # Store episode trajectories for HER relabeling
    self.current_episode = []
    self.episodes = deque(maxlen=1000)  # Store last 1000 episodes

  def add(self, obs, action, reward, next_obs, done):
    """Add transition and handle episode storage for HER."""
    # Store in current episode
    self.current_episode.append((obs, action, reward, next_obs, done))

    # If episode ended, store it and relabel with HER
    if done:
      self.episodes.append(self.current_episode.copy())
      self._add_hindsight_experience(self.current_episode)
      self.current_episode = []

    # Add normal transition
    super().add(obs, action, reward, next_obs, done)

  def _add_hindsight_experience(self, episode):
    """
    Relabel episode with hindsight goals.
    For Crafter, we can relabel based on achievements unlocked.
    """
    # Simple HER: relabel last achievement as goal
    # This is a simplified version - full HER would be more sophisticated

    if len(episode) < 2:
      return

    # For each transition, create a HER version
    for i in range(len(episode)):
      obs, action, _, next_obs, done = episode[i]

      # Relabel reward based on "goal" being the final state
      # In Crafter, this could mean treating any achievement as success
      her_reward = 1.0 if done else 0.0

      # Add HER transition (simplified version)
      super().add(obs, action, her_reward, next_obs, done)
      