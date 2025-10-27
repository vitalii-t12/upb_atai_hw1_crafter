# -*- coding: utf-8 -*-
from typing import Tuple

import torch
import torch.nn.functional as F


def quantile_huber_loss(
    dist_pred: torch.Tensor, dist_target: torch.Tensor, kappa: float = 1.0
) -> Tuple[torch.Tensor, torch.Tensor]:
    """
    Quantile Huber regression loss as in Dabney et al. 2018 (QR-DQN).
    dist_pred:   [B, N]
    dist_target: [B, N]
    Returns:
       per-sample loss (B,1) and elementwise absolute TD errors (B,N) for PER.
    """
    B, N = dist_pred.shape
    # Sort quantile midpoints tau_i
    tau = (torch.arange(N, device=dist_pred.device, dtype=dist_pred.dtype) + 0.5) / N  # [N]
    tau = tau.view(1, N)  # [1, N]

    # Pairwise TD errors: target - pred (broadcast over quantiles)
    # In QR-DQN we align quantiles one-to-one (not full pairwise like IQN)
    u = dist_target.detach() - dist_pred  # [B,N]

    # Huber
    abs_u = torch.abs(u)
    huber = torch.where(abs_u <= kappa, 0.5 * u.pow(2), kappa * (abs_u - 0.5 * kappa))

    # Quantile weights
    # Indicator(u < 0) -> 1 if negative
    indicator = (u.detach() < 0.0).float()
    quantile_weight = torch.abs(tau - indicator)  # [B,N] via broadcast

    loss_per_item = (quantile_weight * huber).sum(dim=1, keepdim=True) / N  # [B,1]
    return loss_per_item, u.abs()
