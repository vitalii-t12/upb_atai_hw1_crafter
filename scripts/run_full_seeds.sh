#!/usr/bin/env bash
set -e
# Full 1M steps, 3 seeds in parallel (adjust to your GPU/CPU capacity).
AGENT=qr_dqn
STEPS=1000000
EVAL=25000

for SEED in 0 1 2; do
  python train.py \
    --steps ${STEPS} \
    --eval-interval ${EVAL} \
    --logdir logdir/${AGENT}/${SEED} \
    --seed ${SEED} \
    &
done
wait

python analysis/plot_eval_performance.py --logdir logdir/random_agent logdir/${AGENT} --outdir report/figures
