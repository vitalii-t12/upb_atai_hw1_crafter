# -*- coding: utf-8 -*-
import os
import random

import numpy as np
import torch


def set_seed_everywhere(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed + 1)
    torch.manual_seed(seed + 2)
    torch.cuda.manual_seed_all(seed + 3)
    os.environ["PYTHONHASHSEED"] = str(seed)
    # Make CUDA deterministic where possible
    torch.backends.cudnn.deterministic = False  # allow perf