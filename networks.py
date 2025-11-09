"""
Neural Network Architectures for Crafter DQN Agent.

Includes:
- Convolutional feature extraction for 64x64x3 images
- Dueling architecture (separate value and advantage streams)
"""

import torch
import torch.nn as nn
import torch.nn.functional as F


class DQNNetwork(nn.Module):
  """
  Deep Q-Network with CNN for image processing.
  Supports Dueling architecture.
  """

  def __init__(self, obs_shape, n_actions, hidden_size=512, dueling=True):
    """
    Initialize DQN network.

    Args:
        obs_shape: Shape of observations (C, H, W)
        n_actions: Number of actions
        hidden_size: Size of fully connected layers
        dueling: Whether to use dueling architecture
    """
    super(DQNNetwork, self).__init__()

    self.obs_shape = obs_shape
    self.n_actions = n_actions
    self.dueling = dueling

    # Convolutional layers for image processing
    # Input: (batch, 3, 64, 64)
    self.conv1 = nn.Conv2d(obs_shape[0], 32, kernel_size=8, stride=4)
    # After conv1: (batch, 32, 15, 15)

    self.conv2 = nn.Conv2d(32, 64, kernel_size=4, stride=2)
    # After conv2: (batch, 64, 6, 6)

    self.conv3 = nn.Conv2d(64, 64, kernel_size=3, stride=1)
    # After conv3: (batch, 64, 4, 4)

    # Calculate size after conv layers
    conv_out_size = self._get_conv_out_size(obs_shape)

    # Fully connected layers
    if dueling:
      # Dueling architecture: separate value and advantage streams

      # Shared feature layer
      self.fc_shared = nn.Linear(conv_out_size, hidden_size)

      # Value stream
      self.fc_value = nn.Linear(hidden_size, hidden_size)
      self.value_head = nn.Linear(hidden_size, 1)

      # Advantage stream
      self.fc_advantage = nn.Linear(hidden_size, hidden_size)
      self.advantage_head = nn.Linear(hidden_size, n_actions)
    else:
      # Standard architecture
      self.fc1 = nn.Linear(conv_out_size, hidden_size)
      self.fc2 = nn.Linear(hidden_size, hidden_size)
      self.fc_out = nn.Linear(hidden_size, n_actions)

  def _get_conv_out_size(self, shape):
    """Calculate output size of convolutional layers."""
    dummy_input = torch.zeros(1, *shape)
    dummy_output = self.conv3(self.conv2(self.conv1(dummy_input)))
    return int(torch.prod(torch.tensor(dummy_output.shape[1:])))

  def forward(self, x):
    """
    Forward pass.

    Args:
        x: Input observation (batch, C, H, W)

    Returns:
        Q-values for each action (batch, n_actions)
    """
    # Ensure input is in correct range [0, 1]
    if x.max() > 1.0:
      x = x / 255.0

    # Convolutional layers with ReLU activation
    x = F.relu(self.conv1(x))
    x = F.relu(self.conv2(x))
    x = F.relu(self.conv3(x))

    # Flatten
    x = x.view(x.size(0), -1)

    if self.dueling:
      # Dueling architecture
      # Shared features
      x = F.relu(self.fc_shared(x))

      # Value stream
      value = F.relu(self.fc_value(x))
      value = self.value_head(value)

      # Advantage stream
      advantage = F.relu(self.fc_advantage(x))
      advantage = self.advantage_head(advantage)

      # Combine value and advantage
      # Q(s,a) = V(s) + (A(s,a) - mean(A(s,a)))
      q_values = value + (advantage - advantage.mean(dim=1, keepdim=True))
    else:
      # Standard architecture
      x = F.relu(self.fc1(x))
      x = F.relu(self.fc2(x))
      q_values = self.fc_out(x)

    return q_values


class NoisyLinear(nn.Module):
  """
  Noisy Linear layer for NoisyNet-DQN (optional enhancement).
  Adds parametric noise to the weights for better exploration.
  """

  def __init__(self, in_features, out_features, sigma_init=0.5):
    """
    Initialize noisy linear layer.

    Args:
        in_features: Input dimension
        out_features: Output dimension
        sigma_init: Initial value for noise standard deviation
    """
    super(NoisyLinear, self).__init__()

    self.in_features = in_features
    self.out_features = out_features
    self.sigma_init = sigma_init

    # Learnable parameters
    self.weight_mu = nn.Parameter(torch.empty(out_features, in_features))
    self.weight_sigma = nn.Parameter(torch.empty(out_features, in_features))
    self.bias_mu = nn.Parameter(torch.empty(out_features))
    self.bias_sigma = nn.Parameter(torch.empty(out_features))

    # Register noise buffers
    self.register_buffer('weight_epsilon', torch.empty(out_features, in_features))
    self.register_buffer('bias_epsilon', torch.empty(out_features))

    self.reset_parameters()
    self.reset_noise()

  def reset_parameters(self):
    """Initialize learnable parameters."""
    mu_range = 1 / self.in_features ** 0.5
    self.weight_mu.data.uniform_(-mu_range, mu_range)
    self.weight_sigma.data.fill_(self.sigma_init / self.in_features ** 0.5)
    self.bias_mu.data.uniform_(-mu_range, mu_range)
    self.bias_sigma.data.fill_(self.sigma_init / self.out_features ** 0.5)

  def reset_noise(self):
    """Generate new noise."""
    epsilon_in = self._scale_noise(self.in_features)
    epsilon_out = self._scale_noise(self.out_features)

    self.weight_epsilon.copy_(epsilon_out.outer(epsilon_in))
    self.bias_epsilon.copy_(epsilon_out)

  def _scale_noise(self, size):
    """Factorized Gaussian noise."""
    x = torch.randn(size)
    return x.sign().mul_(x.abs().sqrt_())

  def forward(self, x):
    """Forward pass with noisy weights."""
    if self.training:
      weight = self.weight_mu + self.weight_sigma * self.weight_epsilon
      bias = self.bias_mu + self.bias_sigma * self.bias_epsilon
    else:
      weight = self.weight_mu
      bias = self.bias_mu

    return F.linear(x, weight, bias)


# Example of how to use NoisyLinear in DQN (optional)
class NoisyDQNNetwork(nn.Module):
  """DQN with NoisyNet layers for exploration."""

  def __init__(self, obs_shape, n_actions, hidden_size=512):
    super(NoisyDQNNetwork, self).__init__()

    # Convolutional layers (same as standard DQN)
    self.conv1 = nn.Conv2d(obs_shape[0], 32, kernel_size=8, stride=4)
    self.conv2 = nn.Conv2d(32, 64, kernel_size=4, stride=2)
    self.conv3 = nn.Conv2d(64, 64, kernel_size=3, stride=1)

    conv_out_size = self._get_conv_out_size(obs_shape)

    # Noisy fully connected layers
    self.noisy_fc1 = NoisyLinear(conv_out_size, hidden_size)
    self.noisy_fc2 = NoisyLinear(hidden_size, n_actions)

  def _get_conv_out_size(self, shape):
    dummy_input = torch.zeros(1, *shape)
    dummy_output = self.conv3(self.conv2(self.conv1(dummy_input)))
    return int(torch.prod(torch.tensor(dummy_output.shape[1:])))

  def forward(self, x):
    if x.max() > 1.0:
      x = x / 255.0

    x = F.relu(self.conv1(x))
    x = F.relu(self.conv2(x))
    x = F.relu(self.conv3(x))
    x = x.view(x.size(0), -1)

    x = F.relu(self.noisy_fc1(x))
    q_values = self.noisy_fc2(x)

    return q_values

  def reset_noise(self):
    """Reset noise for all noisy layers."""
    self.noisy_fc1.reset_noise()
    self.noisy_fc2.reset_noise()