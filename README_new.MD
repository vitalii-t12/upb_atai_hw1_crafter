# Crafter – QR-DQN (from scratch)

This package implements a **from-scratch** QR-DQN agent for the Crafter environment, satisfying the assignment requirements:
- No external RL frameworks.
- Random-agent baseline preserved.
- Same evaluation logging format (`eval_stats.pkl`).
- Reproducible multi-seed runs and plots (mean ± std) with CSV export.
- LaTeX report + Beamer slides.

## 1) Install

Follow Crafter’s install instructions: <https://github.com/danijar/crafter>

Then create a fresh env (conda or venv) and install deps:
```bash
pip install -r requirements.txt
```

If you have a GPU, PyTorch with CUDA is recommended.

2) Random Baseline (from starter)

Example (10k steps):

python train.py --steps 10_000 --eval-interval 2500 --logdir logdir/random_agent/0


Multiple seeds:

for i in $(seq 1 3); do python train.py --steps 250_000 --eval-interval 25_000 --logdir logdir/random_agent/$i & done
wait


Note: The random-agent baseline is derived from the starter scaffold (uniform action sampling). Our plotting tools can overlay it with the QR-DQN results.

3) Train QR-DQN

Full 1M-steps, 3 seeds (recommended):

bash scripts/run_full_seeds.sh


Quick sanity (200k steps):

bash scripts/run_small.sh


Manual example:

python train.py --logdir logdir/qr_dqn/0 --seed 0

CLI knobs (best defaults already set)

--quantiles 51, --n-step 3, --replay-size 250000, --target-update-interval 10000

Epsilon schedule: cosine decay from 1.0 -> 0.01 over 800k steps.

Run python train.py -h to see all options.

4) Plotting + CSV export

Overlay curves (random vs QR-DQN), shaded std, CSV export to report/figures/:

python analysis/plot_eval_performance.py \
  --logdir logdir/random_agent logdir/qr_dqn \
  --outdir report/figures


This produces:

report/figures/eval_curves.png

report/figures/eval_curves.pdf

report/figures/random_agent_curve.csv, report/figures/qr_dqn_curve.csv

report/figures/random_agent_final.csv, report/figures/qr_dqn_final.csv

You can also aggregate one agent:

python analysis/aggregate.py --logdir logdir/qr_dqn --out report/figures/qr_dqn_agg.csv

5) LaTeX

Compile the report:

cd report
pdflatex main.tex && bibtex main && pdflatex main.tex && pdflatex main.tex


Compile slides:

cd ../slides
pdflatex talk.tex


Figures are parameterized: the files expected by the LaTeX docs are written by the plotting script after you train.

6) Reproducibility

Deterministic seeding for NumPy and PyTorch (--seed).

Replay in CPU RAM; observations compressed as uint8.

Evaluation is greedy (no epsilon), saved as eval_stats.pkl (compatible with starter).

7) Checklist (matches brief)

 Implemented own algorithm (QR-DQN + Double + Dueling + n-step + PER).

 Random baseline retained and comparable.

 Eval logging format unchanged.

 Plot avg episodic reward with shaded std; export CSV.

 Report final performance averaged over 2–3 runs (CSV ready).

 Defaults in train.py are best hyperparams; max 1M steps.

 Scripts for small/full runs and evaluation.

 No large checkpoints included.