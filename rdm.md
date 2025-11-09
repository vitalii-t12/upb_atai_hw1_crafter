# Crafter Deep RL Agent

A comprehensive implementation of Deep Q-Network (DQN) agent with enhancements for the Crafter environment.

## Overview

This project implements a DQN agent with multiple enhancements to solve the Crafter benchmark:
- **Double DQN**: Reduces overestimation bias
- **Dueling Architecture**: Separate value and advantage streams
- **N-step Returns**: Better credit assignment (n=3 or n=5)
- **Munchausen-DQN**: Implicit KL regularization for stability

**Performance Target**: Beat random baseline (1.6% Crafter score) within 1M training steps

## Installation

### 1. Create Virtual Environment (Recommended)

```bash
# Using conda
conda create -n crafter python=3.8
conda activate crafter

# Or using venv
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Verify Installation

```bash
python -c "import crafter; import torch; print('✓ All dependencies installed')"
```

## Quick Start

### Train with Default Hyperparameters

```bash
python train.py
```

This will train an enhanced DQN agent with optimal default hyperparameters for 1M steps.

### Train a Specific Configuration

```bash
# Base DQN
python train.py --double-dqn --dueling --n-step 1 --logdir logdir/base-dqn/0

# With 3-step returns
python train.py --double-dqn --dueling --n-step 3 --logdir logdir/nstep3/0

# Full enhancements (recommended)
python train.py --double-dqn --dueling --n-step 3 --munchausen --logdir logdir/full/0
```

### Visualize Results

```bash
# After training, plot evaluation performance
python analysis/plot_eval_performance.py --logdir logdir/full/0

# Compare multiple seeds
python analysis/plot_eval_performance.py --logdir logdir/full
```

## Experimental Protocol

### Development Phase (100-200k steps)

Quick experiments to test different configurations:

```bash
# Experiment 1: Base DQN
python train.py --steps 200000 --double-dqn --dueling --logdir logdir/dev/base/0

# Experiment 2: With n-step
python train.py --steps 200000 --double-dqn --dueling --n-step 3 --logdir logdir/dev/nstep/0

# Experiment 3: Full enhancements
python train.py --steps 200000 --double-dqn --dueling --n-step 3 --munchausen --logdir logdir/dev/full/0
```

### Final Runs (1M steps, multiple seeds)

Run the best configuration with 3 seeds for reproducibility:

```bash
for seed in 0 1 2; do
    python train.py \
        --steps 1000000 \
        --double-dqn \
        --dueling \
        --n-step 3 \
        --munchausen \
        --logdir logdir/final/$seed \
        --seed $seed &
done
wait
```

### Automated Parallel Experiments

Run all experiments automatically:

```bash
./run_experiments.sh
```

This will launch:
1. Random baseline (for comparison)
2. Base DQN
3. Enhanced DQN (Double + Dueling)
4. N-step variants (n=3, n=5)
5. Full enhancement (all features)

Each experiment runs with 3 different seeds in parallel.

## Project Structure

```
crafter_agent/
├── train.py                  # Main training script
├── agent.py                  # DQN agent implementation
├── networks.py               # Neural network architectures
├── replay_buffer.py          # Experience replay buffer
├── utils.py                  # Utility functions
├── requirements.txt          # Python dependencies
├── README.md                 # This file
├── run_experiments.sh        # Automated experiment launcher
├── src/
│   └── crafter_wrapper.py    # Crafter environment wrapper
└── analysis/
    ├── plot_eval_performance.py   # Plotting script
    └── aggregate_runs.py          # Results aggregation
```

## Hyperparameters

### Default Configuration (Optimized for Crafter)

| Hyperparameter | Value | Description |
|----------------|-------|-------------|
| Learning rate | 1e-4 | Adam optimizer learning rate |
| Batch size | 32 | Training batch size |
| Replay buffer | 100k | Experience replay capacity |
| Gamma | 0.99 | Discount factor |
| Epsilon start | 1.0 | Initial exploration rate |
| Epsilon end | 0.01 | Final exploration rate |
| Epsilon decay | 50k steps | Exploration decay period |
| Target update | 2500 steps | Target network update frequency |
| Training starts | 5000 steps | Steps before training begins |
| N-step | 3 | N-step returns |
| Hidden size | 512 | Fully connected layer size |

### Tuning Hyperparameters

To modify hyperparameters:

```bash
python train.py \
    --lr 5e-5 \
    --batch-size 64 \
    --n-step 5 \
    --epsilon-decay-steps 100000 \
    --logdir logdir/custom/0
```

## Monitoring Training

### Real-time Monitoring

```bash
# Watch training progress
tail -f logdir/your-agent/0.log

# Monitor GPU usage
watch -n 1 nvidia-smi
```

### Checkpoints

Checkpoints are saved automatically:
- Every 100k steps during training
- At the end of training (final_model.pt)

Resume from checkpoint:

```bash
python train.py --resume logdir/your-agent/0/checkpoint_100000.pt
```

## Evaluation

### Generate Plots

```bash
# Single run
python analysis/plot_eval_performance.py --logdir logdir/your-agent/0

# Multiple seeds (aggregated)
python analysis/plot_eval_performance.py --logdir logdir/your-agent
```

This generates:
- `rewards.png`: Training and evaluation rewards
- `training_metrics.png`: Loss and Q-values
- `achievement_spectrum.png`: Success rates for all 22 achievements
- `summary.png`: Combined overview

### Compare Experiments

```bash
python analysis/aggregate_runs.py --logdir logdir
```

This creates a comparison table of all experiments with mean ± std statistics.

## Understanding Crafter Metrics

### Crafter Score

The official Crafter metric is computed as the geometric mean of achievement success rates:

```
score = exp(mean(log(rate + 1))) - 1
```

- Random baseline: ~1.6%
- Good performance: >4%
- Strong performance: >10%
- Human experts: ~50%

### Achievements

Crafter has 22 achievements organized in a technology tree:

**Easy** (0-2 steps):
- Collect Wood, Drink Water, Collect Sapling, Place Plant, Wake Up

**Medium** (2-4 steps):
- Place Table, Make Wood Pickaxe, Collect Stone, Make Stone Pickaxe, etc.

**Hard** (4+ steps):
- Make Iron Pickaxe, Make Iron Sword, Collect Diamond

## Tips for Better Performance

### 1. Exploration

- Use longer epsilon decay for harder achievements
- Consider intrinsic motivation (RND) for bonus exploration

### 2. Credit Assignment

- Increase n-step (try n=5 for long episodes)
- Use Munchausen-DQN for better value estimation

### 3. Stability

- Use gradient clipping (default: 10.0)
- Double DQN reduces overestimation
- Target network updates every 2500 steps

### 4. Efficiency

- Batch size 32 works well on most GPUs
- Store observations as uint8 to save memory
- Use parallel environment rollouts if needed

## Common Issues

### Out of Memory (OOM)

```bash
# Reduce batch size
python train.py --batch-size 16

# Reduce buffer size
python train.py --buffer-size 50000
```

### Training is Slow

```bash
# Check if using GPU
python -c "import torch; print(torch.cuda.is_available())"

# Reduce evaluation frequency
python train.py --eval-interval 100000
```

### Poor Performance

- Check epsilon decay (should explore 50k+ steps)
- Verify n-step returns (n=3 or n=5)
- Ensure Double DQN and Dueling are enabled
- Try longer training (1.5M steps)

## Advanced Features

### Prioritized Experience Replay (PER)

Modify `agent.py` to use `PrioritizedReplayBuffer` instead of `ReplayBuffer`.

### Noisy Networks

Use `NoisyDQNNetwork` from `networks.py` for parameter space exploration.

### Data Augmentation

Add random shifts to observations in the wrapper for better generalization.

## Citation

If you use this code, please cite the Crafter paper:

```bibtex
@inproceedings{hafner2021crafter,
  title={Benchmarking the Spectrum of Agent Capabilities},
  author={Hafner, Danijar},
  booktitle={International Conference on Learning Representations},
  year={2022}
}
```

## License

This project is for educational purposes. The Crafter environment is subject to its own license.

## Acknowledgments

- Crafter environment by Danijar Hafner
- DQN and enhancements from DeepMind research
- Assignment from UPB ATAI course

## Support

For issues or questions:
1. Check the Common Issues section
2. Review hyperparameters and ensure they match defaults
3. Verify all dependencies are installed correctly
4. Check GPU availability and memory

## Results

After running experiments, update this section with your results:

```
| Method | Crafter Score | Episode Reward | Achievements |
|--------|---------------|----------------|--------------|
| Random | 1.6%         | 2.1           | 6/22        |
| Your Agent | ?% | ? | ?/22 |
```

Good luck! 🚀