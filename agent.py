"""
DQN Agent with enhancements:
- Double DQN: Reduces overestimation bias
- Dueling architecture: Separate value and advantage streams
- N-step returns: Better credit assignment
- Munchausen-DQN: Implicit KL regularization
"""

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from collections import deque

from networks import DQNNetwork
from replay_buffer import ReplayBuffer


class DQNAgent:
  """Deep Q-Network agent with enhancements."""

  def __init__(self,
               obs_shape,
               n_actions,
               device='cuda',
               lr=1e-4,
               gamma=0.99,
               buffer_size=100_000,
               batch_size=32,
               double_dqn=True,
               dueling=True,
               n_step=1,
               hidden_size=512,
               grad_clip=10.0,
               munchausen=False,
               munchausen_alpha=0.9,
               munchausen_tau=0.03):
    """
    Initialize DQN agent.

    Args:
        obs_shape: Shape of observations (C, H, W)
        n_actions: Number of actions
        device: Device to use (cuda/cpu)
        lr: Learning rate
        gamma: Discount factor
        buffer_size: Size of replay buffer
        batch_size: Batch size for training
        double_dqn: Use Double DQN
        dueling: Use Dueling architecture
        n_step: N-step returns (1 for standard TD)
        hidden_size: Size of hidden layers
        grad_clip: Gradient clipping value
        munchausen: Use Munchausen-DQN
        munchausen_alpha: Munchausen alpha parameter
        munchausen_tau: Munchausen tau (temperature) parameter
    """
    self.obs_shape = obs_shape
    self.n_actions = n_actions
    self.device = device
    self.gamma = gamma
    self.batch_size = batch_size
    self.double_dqn = double_dqn
    self.n_step = n_step
    self.grad_clip = grad_clip
    self.munchausen = munchausen
    self.munchausen_alpha = munchausen_alpha
    self.munchausen_tau = munchausen_tau

    # Create Q-network and target network
    self.q_network = DQNNetwork(obs_shape, n_actions, hidden_size, dueling).to(device)
    self.target_network = DQNNetwork(obs_shape, n_actions, hidden_size, dueling).to(device)
    self.target_network.load_state_dict(self.q_network.state_dict())
    self.target_network.eval()

    # Optimizer
    self.optimizer = torch.optim.Adam(self.q_network.parameters(), lr=lr)

    # Replay buffer
    self.replay_buffer = ReplayBuffer(buffer_size, obs_shape, n_step, gamma)

    # N-step buffer for storing recent transitions
    self.n_step_buffer = deque(maxlen=n_step)

    # Training stats
    self.train_steps = 0

  def select_action(self, obs, epsilon=0.0):
    """
    Select action using epsilon-greedy policy.

    Args:
        obs: Observation (numpy array)
        epsilon: Exploration rate

    Returns:
        action: Selected action (int)
    """
    if np.random.random() < epsilon:
      return np.random.randint(self.n_actions)

    # Greedy action
    with torch.no_grad():
      obs_tensor = torch.FloatTensor(obs).unsqueeze(0).to(self.device)
      q_values = self.q_network(obs_tensor)
      action = q_values.argmax(dim=1).item()

    return action

  def store_transition(self, obs, action, reward, next_obs, done):
    """
    Store transition in replay buffer (handles n-step).

    Args:
        obs: Current observation
        action: Action taken
        reward: Reward received
        next_obs: Next observation
        done: Whether episode ended
    """
    # Add to n-step buffer
    self.n_step_buffer.append((obs, action, reward, next_obs, done))

    # If we have enough steps or episode ended, compute n-step return
    if len(self.n_step_buffer) == self.n_step or done:
      # Compute n-step return
      n_step_reward = 0
      for i, (_, _, r, _, _) in enumerate(self.n_step_buffer):
        n_step_reward += (self.gamma ** i) * r

      # Get first observation and action
      first_obs, first_action, _, _, _ = self.n_step_buffer[0]

      # Get last next_obs and done
      _, _, _, last_next_obs, last_done = self.n_step_buffer[-1]

      # Store in replay buffer
      self.replay_buffer.add(first_obs, first_action, n_step_reward,
                             last_next_obs, last_done)

      # Clear buffer if episode ended
      if done:
        self.n_step_buffer.clear()

  def update(self):
    """
    Update Q-network using a batch from replay buffer.

    Returns:
        dict: Training metrics (loss, q_values, etc.)
    """
    if len(self.replay_buffer) < self.batch_size:
      return None

    # Sample batch
    batch = self.replay_buffer.sample(self.batch_size)
    obs, actions, rewards, next_obs, dones = batch

    # Convert to tensors
    obs = torch.FloatTensor(obs).to(self.device)
    actions = torch.LongTensor(actions).to(self.device)
    rewards = torch.FloatTensor(rewards).to(self.device)
    next_obs = torch.FloatTensor(next_obs).to(self.device)
    dones = torch.FloatTensor(dones).to(self.device)

    # Compute current Q-values
    current_q_values = self.q_network(obs)
    current_q = current_q_values.gather(1, actions.unsqueeze(1)).squeeze(1)

    # Compute target Q-values
    with torch.no_grad():
      if self.double_dqn:
        # Double DQN: use online network to select action, target network to evaluate
        next_q_values_online = self.q_network(next_obs)
        next_actions = next_q_values_online.argmax(dim=1)
        next_q_values_target = self.target_network(next_obs)
        next_q = next_q_values_target.gather(1, next_actions.unsqueeze(1)).squeeze(1)
      else:
        # Standard DQN
        next_q_values = self.target_network(next_obs)
        next_q = next_q_values.max(dim=1)[0]

      # Compute target
      target_q = rewards + (1 - dones) * (self.gamma ** self.n_step) * next_q

      # Munchausen-DQN modification
      if self.munchausen:
        # Compute log policy for current state
        current_q_log_policy = F.log_softmax(current_q_values / self.munchausen_tau, dim=1)
        munchausen_addon = self.munchausen_alpha * current_q_log_policy.gather(1, actions.unsqueeze(1)).squeeze(1)

        # Clip to prevent numerical issues
        munchausen_addon = torch.clamp(munchausen_addon, min=-1, max=0)

        # Add to reward
        target_q = (rewards + munchausen_addon) + (1 - dones) * (self.gamma ** self.n_step) * next_q

    # Compute loss (Huber loss is more stable than MSE)
    loss = F.smooth_l1_loss(current_q, target_q)

    # Optimize
    self.optimizer.zero_grad()
    loss.backward()

    # Gradient clipping
    if self.grad_clip is not None:
      torch.nn.utils.clip_grad_norm_(self.q_network.parameters(), self.grad_clip)

    self.optimizer.step()

    self.train_steps += 1

    # Return metrics
    return {
      'loss': loss.item(),
      'q_values_mean': current_q.mean().item(),
      'q_values_std': current_q.std().item(),
      'target_q_mean': target_q.mean().item()
    }

  def update_target_network(self):
    """Update target network with current Q-network weights."""
    self.target_network.load_state_dict(self.q_network.state_dict())

  def save(self, path):
    """Save agent state."""
    torch.save({
      'q_network': self.q_network.state_dict(),
      'target_network': self.target_network.state_dict(),
      'optimizer': self.optimizer.state_dict(),
      'train_steps': self.train_steps
    }, path)

  def load(self, path):
    """Load agent state."""
    checkpoint = torch.load(path, map_location=self.device)
    self.q_network.load_state_dict(checkpoint['q_network'])
    self.target_network.load_state_dict(checkpoint['target_network'])
    self.optimizer.load_state_dict(checkpoint['optimizer'])
    self.train_steps = checkpoint['train_steps']