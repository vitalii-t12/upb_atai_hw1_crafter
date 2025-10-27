# -*- coding: utf-8 -*-
from typing import Optional

import torch

from src.utils.schedule import Schedule


class GreedyPolicy:
    def __init__(self, net: torch.nn.Module, num_actions: int, num_quantiles: int, device: torch.device):
        self.net = net
        self.num_actions = num_actions
        self.num_quantiles = num_quantiles
        self.device = device

    @torch.no_grad()
    def act(self, obs: torch.Tensor) -> int:
        if obs.dim() == 3:
            obs = obs.unsqueeze(0)
        z = self.net(obs.to(self.device))  # [1, A, N]
        q = z.mean(dim=2)  # expectation over quantiles -> [1,A]
        action = int(q.argmax(dim=1).item())
        return action


class EpsGreedyPolicy(GreedyPolicy):
    def __init__(
        self,
        net: torch.nn.Module,
        num_actions: int,
        num_quantiles: int,
        schedule: Schedule,
        device: torch.device,
    ):
        super().__init__(net, num_actions, num_quantiles, device)
        self.schedule = schedule
        self.t = 0

    def act(self, obs: torch.Tensor, force_random: bool = False) -> int:
        eps = self.schedule.value(self.t)
        self.t += 1
        if force_random or torch.rand(()) < eps:
            return int(torch.randint(0, self.num_actions, ()).item())
        return super().act(obs)
