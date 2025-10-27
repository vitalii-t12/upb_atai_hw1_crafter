# -*- coding: utf-8 -*-
from abc import ABC, abstractmethod
import math


class Schedule(ABC):
    @abstractmethod
    def value(self, t: int) -> float:
        ...


class LinearSchedule(Schedule):
    def __init__(self, start: float, end: float, decay_steps: int):
        self.start = start
        self.end = end
        self.decay_steps = max(1, decay_steps)

    def value(self, t: int) -> float:
        frac = min(1.0, t / self.decay_steps)
        return self.start + frac * (self.end - self.start)


class CosineSchedule(Schedule):
    """
    Cosine from start -> end over decay_steps, then hold end.
    """
    def __init__(self, start: float, end: float, decay_steps: int):
        self.start = start
        self.end = end
        self.decay_steps = max(1, decay_steps)

    def value(self, t: int) -> float:
        if t >= self.decay_steps:
            return self.end
        cos = (1 + math.cos(math.pi * t / self.decay_steps)) / 2.0  # 1->0
        return self.end + (self.start - self.end) * cos
