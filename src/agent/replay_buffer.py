# -*- coding: utf-8 -*-
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional, Tuple

import numpy as np
import torch


@dataclass
class Transition:
    obs: np.ndarray
    action: int
    reward: float
    next_obs: np.ndarray
    done: bool


class NStepAdder:
    """
    Small n-step return adder that maintains an internal deque.
    Produces (s0, a0, Rn, s_n, done_n).
    """
    def __init__(self, n: int, gamma: float):
        from collections import deque
        self.n = n
        self.gamma = gamma
        self.buf = deque(maxlen=n)
        self.obs0 = None

    def reset(self, first_obs: torch.Tensor):
        self.buf.clear()
        self.obs0 = first_obs.detach().cpu().numpy()

    def add(self, action: int, reward: float, next_obs: torch.Tensor, done: bool):
        self.buf.append((action, reward, next_obs.detach().cpu().numpy(), done))
        if len(self.buf) == self.n:
            Rn = 0.0
            done_n = False
            for i, (_, r, _, d) in enumerate(self.buf):
                Rn += (self.gamma ** i) * r
                if d:
                    # stop accumulating at first terminal
                    done_n = True
                    break
            a0, _, _, _ = self.buf[0]
            s0 = self.obs0
            sn = self.buf[-1][2]
            out = (s0, a0, Rn, sn, float(done_n))
            # move window: next trajectory starts from the second element's obs as obs0
            self.obs0 = self.buf[0][2]
            self.buf.popleft()
            return out
        return None


class PrioritizedReplayBuffer:
    """
    Simple PER buffer with proportional priorities (sum-tree via arrays).
    Observations stored as uint8 to save RAM; converted to float in [0,1] on sample.
    """

    def __init__(
        self,
        capacity: int,
        obs_shape: Tuple[int, ...],
        alpha: float,
        beta_start: float,
        beta_frames: int,
        device: torch.device,
        store_uint8: bool = True,
    ):
        self.capacity = int(capacity)
        self.alpha = alpha
        self.beta_start = beta_start
        self.beta_frames = beta_frames
        self.device = device
        self.store_uint8 = store_uint8

        self.pos = 0
        self.full = False

        obs_dtype = np.uint8 if store_uint8 else np.float32
        self.obs = np.zeros((self.capacity,) + obs_shape, dtype=obs_dtype)
        self.next_obs = np.zeros((self.capacity,) + obs_shape, dtype=obs_dtype)
        self.actions = np.zeros((self.capacity,), dtype=np.int64)
        self.rewards = np.zeros((self.capacity,), dtype=np.float32)
        self.dones = np.zeros((self.capacity,), dtype=np.float32)

        # priorities
        self.priorities = np.zeros((self.capacity,), dtype=np.float32)
        self.eps = 1e-6  # small constant

        self.frame = 1  # for beta anneal

    @property
    def size(self) -> int:
        return self.capacity if self.full else self.pos

    def beta_by_frame(self) -> float:
        return min(1.0, self.beta_start + (1.0 - self.beta_start) * (self.frame / self.beta_frames))

    def _encode_obs(self, x: np.ndarray) -> np.ndarray:
        if not self.store_uint8:
            return x.astype(np.float32, copy=False)
        # expect float [0,1] -> uint8
        return (np.clip(x, 0.0, 1.0) * 255.0).astype(np.uint8)

    def _decode_obs(self, x: np.ndarray) -> torch.Tensor:
        if not self.store_uint8:
            return torch.from_numpy(x).float().to(self.device)
        return torch.from_numpy(x.astype(np.float32) / 255.0).to(self.device)

    def add(self, obs: np.ndarray, action: int, reward: float, next_obs: np.ndarray, done: float):
        idx = self.pos
        self.obs[idx] = self._encode_obs(obs)
        self.next_obs[idx] = self._encode_obs(next_obs)
        self.actions[idx] = action
        self.rewards[idx] = reward
        self.dones[idx] = done

        # max priority for newly added
        max_prio = self.priorities.max() if self.pos > 0 or self.full else 1.0
        self.priorities[idx] = max_prio

        self.pos = (self.pos + 1) % self.capacity
        if self.pos == 0:
            self.full = True

    def sample(self, batch_size: int) -> Dict[str, torch.Tensor]:
        assert self.size > 0, "Replay is empty"
        prios = self.priorities[: self.size]
        probs = prios ** self.alpha
        probs /= probs.sum()

        indices = np.random.choice(self.size, batch_size, p=probs)
        beta = self.beta_by_frame()
        self.frame += 1

        weights = (self.size * probs[indices]) ** (-beta)
        weights /= weights.max() + 1e-6

        batch = {
            "obs": self._decode_obs(self.obs[indices]),
            "actions": torch.from_numpy(self.actions[indices]).long().to(self.device),
            "rewards": torch.from_numpy(self.rewards[indices]).float().to(self.device),
            "next_obs": self._decode_obs(self.next_obs[indices]),
            "dones": torch.from_numpy(self.dones[indices]).float().to(self.device),
            "weights": torch.from_numpy(weights).float().to(self.device),
            "indices": indices,
        }
        return batch

    def update_priorities(self, indices: np.ndarray, td_errors: np.ndarray):
        # Use mean per-sample quantile error as TD error magnitude
        td = np.mean(np.abs(td_errors), axis=1) + self.eps
        self.priorities[indices] = td
