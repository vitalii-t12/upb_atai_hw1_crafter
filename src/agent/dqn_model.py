# -*- coding: utf-8 -*-
from typing import Tuple

import torch
import torch.nn as nn
import torch.nn.functional as F


class QRDuelingDQN(nn.Module):
    """
    Dueling CNN torso with Quantile heads.
    Outputs a distribution over returns for each action: [B, A, Ntau]
    Combine as V_tau + (A_tau - mean_a A_tau)
    """

    def __init__(self, in_channels: int, num_actions: int, num_quantiles: int = 51):
        super().__init__()
        self.num_actions = num_actions
        self.num_quantiles = num_quantiles

        # Torso for 84x84 inputs
        self.conv = nn.Sequential(
            nn.Conv2d(in_channels, 32, kernel_size=8, stride=4),  # 84->20
            nn.ReLU(inplace=True),
            nn.Conv2d(32, 64, kernel_size=4, stride=2),  # 20->9
            nn.ReLU(inplace=True),
            nn.Conv2d(64, 64, kernel_size=3, stride=1),  # 9->7
            nn.ReLU(inplace=True),
        )
        self.fc = nn.Sequential(nn.Flatten(), nn.Linear(64 * 7 * 7, 512), nn.ReLU(inplace=True))

        # Dueling quantile streams
        self.value_head = nn.Linear(512, num_quantiles)  # [B, N]
        self.adv_head = nn.Linear(512, num_actions * num_quantiles)  # [B, A*N]
        self._init()

    def _init(self):
        # Fan-in init for stability
        for m in self.modules():
            if isinstance(m, nn.Linear):
                nn.init.kaiming_uniform_(m.weight, nonlinearity="relu")
                nn.init.constant_(m.bias, 0.0)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        x: [B, C, 84, 84] float in [0,1]
        returns: [B, A, N]
        """
        x = x / 1.0  # already normalized
        feats = self.fc(self.conv(x))
        V = self.value_head(feats).unsqueeze(1)  # [B,1,N]
        A = self.adv_head(feats).view(-1, self.num_actions, self.num_quantiles)  # [B,A,N]
        A = A - A.mean(dim=1, keepdim=True)
        Z = V + A  # [B, A, N]
        return Z
