#!/usr/bin/env bash
set -e
# Runs evaluation using the current greedy policy (no training),
# by executing a zero-step training loop that only triggers eval once.
AGENT=qr_dqn
python train.py --steps 1 --eval-interval 1 --logdir logdir/${AGENT}/eval_only --seed 0
