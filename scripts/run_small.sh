#!/usr/bin/env bash
set -e
# Small sanity run (200k steps, 2 seeds) for quick iteration.
AGENT=qr_dqn
STEPS=200000
EVAL=25000

for SEED in 0 1; do
  python train.py \
    --steps ${STEPS} \
    --eval-interval ${EVAL} \
    --logdir logdir/${AGENT}/${SEED} \
    --seed ${SEED} \
    &
done
wait

# Plot overlay with random baseline if present.
python analysis/plot_eval_performance.py --logdir logdir/random_agent logdir/${AGENT} --outdir report/figures
