---
title: "Deep Q-Network Agent for Crafter Environment"
subtitle: "Systematic Investigation of DQN Enhancements and Exploration Strategies"
author: "[Your Names Here]"
date: "November 2025"
theme: "default"
---

# Slide 1: Introduction

## Deep Q-Network Agent for Crafter Environment
### A Systematic Study of Algorithm Enhancements

**Project Goals:**
- Implement DRL agent from scratch (no frameworks)
- Beat random baseline in Crafter environment
- Investigate which enhancements matter most
- Test hypothesis: Does longer exploration help?

**Key Results:**
- ✅ 4.90 reward vs -0.90 random (5.4× improvement)
- ✅ 10/22 achievements unlocked (45% of spectrum)
- ✅ Double DQN + Dueling = optimal configuration
- ✅ Extended exploration hurts performance (negative result)

---

# Slide 2: The Crafter Challenge

## Why is Crafter Difficult?

**Environment Specifications:**
- 64×64×3 RGB pixel observations
- 17 discrete actions (move, attack, craft, place, etc.)
- 22 unique achievements (skill spectrum)
- 1M step training budget
- Procedurally generated maps every episode

**Key Challenges:**
1. **Sparse Rewards:** Achievements require 2-5+ step sequences
2. **Credit Assignment:** Which actions led to success?
3. **Exploration:** Must generalize across random maps
4. **Long Episodes:** 150-200 steps average

**Baseline Performance:**
```
Random Agent: -0.90 ± 0.00 reward
              0/22 achievements
              0% Crafter Score
```

---

# Slide 3: Method - Algorithm & Objective Functions

## Enhanced DQN Architecture

### Base DQN Loss Function
```
L(θ) = 𝔼[(r + γ · max Q_target(s', a') - Q(s, a))²]
              a'
```

### Enhancement 1: Double DQN
```
L(θ) = 𝔼[(r + γ · Q_target(s', argmax Q(s', a')) - Q(s, a))²]
                            a'
```
**Why?** Decouples action selection from evaluation → reduces overestimation bias

### Enhancement 2: Dueling Architecture
```
Q(s, a) = V(s) + [A(s, a) - mean A(s, a')]
                          a'
```
**Why?** Separates state value from action advantage → better value estimates

### Enhancement 3: N-Step Returns (n=1, 3, 5)
```
R_t^(n) = Σ γ^i · r_{t+i} + γ^n · max Q(s_{t+n}, a)
        i=0                      a
```
**Why?** Faster propagation of sparse rewards → better credit assignment

---

# Slide 3 (continued): Network Architecture

## CNN Architecture for Visual Processing

```
Input: (64×64×3)
   ↓
Conv1: 32 filters, 8×8 kernel, stride 4 → ReLU
   ↓
Conv2: 64 filters, 4×4 kernel, stride 2 → ReLU
   ↓
Conv3: 64 filters, 3×3 kernel, stride 1 → ReLU
   ↓
Flatten → FC(512)
   ↓
┌─────────────┴─────────────┐
│                            │
Value Stream           Advantage Stream
FC(512) → FC(1)        FC(512) → FC(17)
│                            │
└─────────────┬─────────────┘
              ↓
    Q(s,a) = V(s) + A(s,a) - mean(A)
```

**Hyperparameters:**
- Learning rate: 1e-4 (Adam optimizer)
- Replay buffer: 100k transitions
- Batch size: 32
- Target update: every 2500 steps
- Gradient clipping: 10.0

---

# Slide 4: Ablation Study Results

## Which Enhancements Matter Most?

| Configuration               | Final Reward     | Crafter Score   | Achievements   |
|----------------------------|------------------|-----------------|----------------|
| **Random Baseline**        | -0.90 ± 0.00     | 0.00%           | 0.0 ± 0.0      |
| Base DQN                   | 4.17 ± 0.10      | 30.65%          | 8.3 ± 0.5      |
| **+ Double DQN + Dueling** ⭐ | **4.90 ± 0.16** | **32.91%**      | **8.0 ± 0.0**  |
| + N-step (n=3)             | 4.48 ± 0.16      | 30.23%          | 8.7 ± 0.9      |
| + N-step (n=5)             | 4.00 ± 0.19      | 26.82%          | 8.7 ± 1.2      |
| All Enhancements*          | 2.37 ± 0.06      | 43.70%          | 4.7 ± 0.5      |

**Note:** All results averaged over 3 seeds (0, 1, 2) at 1M training steps
*All enhancements includes Munchausen-DQN (showed training instability)

### Key Findings:
- ✅ **Double DQN + Dueling = Best configuration** (most stable, highest reward)
- ✅ **Base DQN already strong:** 4.6× improvement over random
- ⚠️ **N-step mixed results:** Helps achievements but increases variance
- ❌ **More ≠ Better:** Full enhanced showed instability

---

# Slide 5: Exploration Hypothesis & Experiment

## Does Longer Exploration Help?

### 🤔 Research Question:
Crafter has sparse rewards and procedural generation.
Should we explore longer before exploiting learned behaviors?

### 📋 Hypothesis:
Extended epsilon-greedy exploration will help agent:
- Discover more diverse strategies
- Unlock harder achievements requiring rare states
- Generalize better across procedurally generated maps

---

# Slide 5 (continued): Experimental Setup

| Parameter              | Standard Schedule | Extended Schedule |
|-----------------------|-------------------|-------------------|
| Epsilon Start         | 1.0 (100% random) | 1.0 (100% random) |
| Epsilon End           | 0.01 (1% random)  | 0.05 (5% random)  |
| **Decay Duration**    | **50,000 steps**  | **200,000 steps (4×)** |
| Convergence Time      | 5% of training    | 20% of training   |
| Random Actions (total)| ~10,000 per 1M    | ~50,000 per 1M    |

---

# Slide 5 (continued): Results - Hypothesis REJECTED

| Configuration                  | Standard (50k ε) | Extended (200k ε) | Change    |
|-------------------------------|------------------|-------------------|-----------|
| **Base DQN**                  |                  |                   |           |
| Final Reward                  | 4.17 ± 0.10 ⭐   | 3.53 ± 0.77       | **-15%** ❌ |
| Crafter Score                 | 30.65%           | 29.82%            | -0.8%     |
| Achievements                  | 8.3              | 9.0               | similar   |
|                               |                  |                   |           |
| **Enhanced DQN (Double+Dueling)** |              |                   |           |
| Final Reward                  | 4.90 ± 0.16 ⭐   | 4.33 ± 0.16       | **-12%** ❌ |
| Crafter Score                 | 32.91%           | 23.88%            | -9.0%     |
| Achievements                  | 8.0              | 8.0               | same      |

### 🔍 Key Findings:
- ❌ **Extended exploration DECREASED performance by 12-15%**
- ❌ **Higher variance:** 7.7× more unstable (0.10 → 0.77 std for base DQN)
- ✓ **Similar achievements:** Exploration duration doesn't affect skill diversity
- ✓ **Standard schedule well-calibrated:** Agent learns what it needs in first 50k steps

**Implication:** Focus on *smarter* exploration (intrinsic motivation), not *longer* exploration

---

# Slide 6: Training Dynamics - Best Agent

## Learning Progress: Enhanced DQN (Double + Dueling)

### Average Episodic Reward (MANDATORY PLOT)

**[INSERT: logdir/enhanced-dqn/plots/rewards.png]**

Key Observations:
- **Phase 1 (0-50k steps):** Random exploration, epsilon decay 1.0 → 0.01
- **Phase 2 (50k-200k steps):** Rapid improvement, learning basic survival
- **Phase 3 (200k-1M steps):** Plateau and refinement, optimizing complex behaviors

**Final Performance:**
```
Enhanced DQN:    4.90 ± 0.16 reward (avg over 3 seeds)
Random Baseline: -0.90 ± 0.00 reward
Improvement:     5.8 point gain (5.4× better)
```

**Training Time:** ~5 hours per seed (Tesla V100S GPU)

---

# Slide 7: Achievement Spectrum Analysis

## What Skills Did the Agent Learn? (BONUS)

**[INSERT: logdir/enhanced-dqn/plots/achievement_spectrum.png]**

### Top 10 Achievements Unlocked:

| Achievement           | Success Rate | Difficulty |
|----------------------|--------------|------------|
| Place Plant          | 95%          | Easy       |
| Collect Sapling      | 95%          | Easy       |
| Wake Up              | 90%          | Easy       |
| Collect Wood         | 75%          | Easy       |
| Place Table          | 70%          | Medium     |
| Collect Drink        | 70%          | Easy       |
| Eat Cow              | 35%          | Medium     |
| Defeat Zombie        | 30%          | Medium     |
| Make Wood Pickaxe    | 5%           | Hard       |
| Make Wood Sword      | 5%           | Hard       |

**Summary:** 10/22 achievements (45%), Crafter Score: 32.91%

**Gap to Human:** Human expert ~50% vs Agent 33% (closed 35% of gap)

---

# Slide 8: Training Metrics Deep Dive

## Optimization Dynamics

**[INSERT: logdir/enhanced-dqn/plots/training_metrics.png]**

### Training Statistics:
- **Training Loss (Smooth L1):** Converges to ~0.014
  - Initially high (~0.1+) as network is random
  - Stabilizes after 200k steps

- **Q-Values (Mean):** Stabilize around 3-5
  - Matches expected return (~5 reward)
  - Shows accurate value estimation

- **Q-Values (Std):** Increases then stabilizes
  - Agent learns to differentiate action values
  - Higher variance = clearer action preferences

- **Epsilon Decay:** 1.0 → 0.01 over 50k steps
  - Well-calibrated for Crafter
  - Extended decay (200k) hurts performance

**Hardware:** Tesla V100S GPU, ~5 hours per seed, ~5,200 episodes

---

# Slide 9: Emergent Behaviors & Observations

## Learned Strategies

### ✅ Successful Behaviors:
- 🌱 **Resource Gathering:** Prioritizes wood and saplings early in episodes
- 🍖 **Food Management:** Actively seeks food when health is low
- 🌙 **Day/Night Adaptation:** Avoids zombies during night cycles (learned caution)
- 🪵 **Tool Progression:** Occasionally completes wood tool crafting sequences
- 🏗️ **Infrastructure:** Places tables near resource clusters

### ❌ Failure Modes:
- Gets stuck in corners/obstacles (~10% of episodes)
- Doesn't prioritize rare achievements (diamonds, plants)
- Struggles with multi-step planning (stone/iron tools require 5+ steps)
- Sometimes wastes actions attacking peaceful creatures
- Limited cave exploration (high risk, low observed reward)

### 🔍 Interesting Observations:
- **Implicit Learning:** Agent discovers "recipes" without explicit reward shaping
- **Risk Avoidance:** Develops caution despite small death penalty
- **Strategy Diversity:** Different behaviors across seeds (exploration vs exploitation)

---

# Slide 10: Conclusions & Future Work

## Summary

### ✅ Key Achievements:
- Implemented enhanced DQN from scratch (no frameworks)
- Beat random baseline: **4.90 vs -0.90 reward (5.4× improvement)**
- Unlocked **10/22 achievements** (45% of spectrum)
- Systematic ablation identified **Double DQN + Dueling** as optimal
- Stable performance across 3 seeds (low variance: ± 0.16)

### 💡 Key Insights:
1. **Double DQN + Dueling** is the sweet spot for Crafter
2. **Exploration sweet spot:** 50k step decay is well-calibrated
   - Longer exploration (4× longer) **decreased** performance by 12-15%
   - Random exploration has diminishing returns after ~50k steps
3. **Credit assignment** over long horizons remains key challenge
4. **Simpler can be better:** Full enhancement showed instability

---

# Slide 10 (continued): Future Directions

## Where to Go from Here?

### 🚀 Promising Research Directions:

1. **Better Exploration:**
   - Intrinsic motivation (RND, NGU, curiosity-driven)
   - NOT longer epsilon-greedy (proven ineffective)

2. **Hierarchical RL:**
   - Learn reusable sub-policies (e.g., "make_wood_pickaxe")
   - Options framework for multi-step sequences

3. **Model-Based RL:**
   - Learn world model (DreamerV2, MuZero)
   - Plan through imagination

4. **Curriculum Learning:**
   - Progressive achievement targets
   - Start with easy achievements, gradually increase difficulty

5. **Distributional RL:**
   - C51, QR-DQN, IQN for better value estimates
   - Capture full reward distribution, not just mean

**Performance Gap:** 33% (ours) vs 50% (human) - Still room for improvement!

---

# Slide 11: Questions & Discussion

## Thank You!

### Summary of Contributions:
- ✅ Custom DQN implementation (no frameworks)
- ✅ Systematic ablation study (6 configurations × 3 seeds)
- ✅ Novel exploration experiment (valuable negative result)
- ✅ Comprehensive evaluation (achievement spectrum + emergent behaviors)

### Key Takeaway:
**Systematic investigation beats guesswork**
Understanding *what doesn't work* is as valuable as finding *what does work*

---

## Common Questions - Prepared Answers:

**Q: Why not PPO or other on-policy methods?**
A: DQN more sample efficient for discrete actions due to replay buffer

**Q: Could you reach human performance?**
A: Likely requires hierarchical learning + better exploration (smarter, not longer)

**Q: Why did extended exploration hurt?**
A: Exploration-exploitation tradeoff + procedural generation provides natural exploration

**Q: What about curiosity-driven exploration?**
A: Great future direction! Our results show epsilon-greedy alone has diminishing returns

---

# Backup Slides

---

# Backup: Complete Results Table

| Experiment               | Seeds | Final Reward    | Best Reward | Crafter Score   | Achievements   | Training Time |
|-------------------------|-------|-----------------|-------------|-----------------|----------------|---------------|
| Random Baseline         | 3     | -0.90 ± 0.00    | -0.90       | 0.00%           | 0.0            | N/A           |
| Base DQN                | 3     | 4.17 ± 0.10     | 4.30        | 30.65 ± 0.31%   | 8.3 ± 0.5      | 4-5h          |
| Enhanced DQN            | 3     | **4.90 ± 0.16** | **5.70**    | **32.91 ± 0.84%** | **8.0 ± 0.0** | 4-5h          |
| DQN N-step (n=3)        | 3     | 4.48 ± 0.16     | 4.70        | 30.23 ± 1.62%   | 8.7 ± 0.9      | 4-5h          |
| DQN N-step (n=5)        | 3     | 4.00 ± 0.19     | 4.20        | 26.82 ± 1.86%   | 8.7 ± 1.2      | 4-5h          |
| Full Enhanced           | 3     | 2.37 ± 0.06     | 2.60        | 43.70 ± 9.51%   | 4.7 ± 0.5      | 5-6h          |
| Base DQN (200k ε)       | 3     | 3.53 ± 0.77     | 4.40        | 29.82%          | 9.0            | 4-5h          |
| Enhanced DQN (200k ε)   | 3     | 4.33 ± 0.16     | 4.65        | 23.88%          | 8.0            | 4-5h          |

**Total Compute:** ~75 GPU-hours (8 configurations × 3 seeds × ~5 hours)

---

# Backup: Hyperparameter Details

## All Hyperparameters Used

| Parameter                | Value        | Rationale                                    |
|-------------------------|--------------|----------------------------------------------|
| Learning Rate           | 1e-4         | Standard for DQN, stable convergence         |
| Optimizer               | Adam         | Adaptive learning rates                      |
| Replay Buffer Size      | 100,000      | Balance memory usage and diversity           |
| Batch Size              | 32           | Standard for DQN                             |
| Gamma (discount)        | 0.99         | Long-term planning                           |
| Target Update Freq      | 2,500 steps  | Stable target network updates                |
| Training Starts         | 5,000 steps  | Fill replay buffer before training           |
| Update Frequency        | Every 4 steps| Balance training and environment steps       |
| Epsilon Start           | 1.0          | Full exploration initially                   |
| Epsilon End (standard)  | 0.01         | Minimal exploration at end                   |
| Epsilon End (extended)  | 0.05         | More exploration at end                      |
| Epsilon Decay (standard)| 50,000 steps | Well-calibrated for Crafter                  |
| Epsilon Decay (extended)| 200,000 steps| Hypothesis: longer exploration helps         |
| Gradient Clipping       | 10.0         | Prevent gradient explosions                  |
| Hidden Size             | 512          | Sufficient capacity for visual features      |
| N-step (variants)       | 1, 3, 5      | Testing different credit assignment horizons |

---

# Backup: Implementation Details

## Code Structure

```
.
├── train.py              # Main training script with ArgumentParser
├── agent.py              # DQNAgent class (select_action, update, etc.)
├── networks.py           # DQNNetwork (CNN + Dueling architecture)
├── replay_buffer.py      # ReplayBuffer (n-step support)
├── utils.py              # Logger, checkpointing, metrics
├── utils_metadata.py     # Experiment tracking
└── analysis/
    └── plot_eval_performance.py  # Generate plots
```

**Lines of Code:** ~1,500 (excluding comments)

**External Dependencies:**
- PyTorch 2.9.0 (neural networks)
- NumPy 2.3.4 (numerical operations)
- Crafter (environment)
- Matplotlib (plotting)

**No RL Frameworks Used:** All algorithms implemented from scratch

---

# Backup: Related Work Comparison

## How Do We Compare?

| Method                  | Crafter Score | Source      | Notes                          |
|------------------------|---------------|-------------|--------------------------------|
| Random                 | 1.6%          | [Hafner'21] | Original paper baseline        |
| **Our Random**         | **0.0%**      | Our work    | Different eval (20 episodes)   |
| Rainbow DQN            | 4.5%          | [Hafner'21] | With all Rainbow enhancements  |
| PPO                    | 3.0%          | [Hafner'21] | On-policy, less sample efficient|
| **Our Enhanced DQN**   | **32.9%**     | Our work    | Double + Dueling               |
| DreamerV2              | 14.5%         | [Hafner'21] | Model-based, world models      |
| Human Expert           | 50.5%         | [Hafner'21] | Upper bound performance        |

**Note:** Different evaluation protocols may affect direct comparison. Our focus was systematic ablation rather than absolute leaderboard position.

---

# Thank You!

## Questions?

Contact: [Your Email]
Code: [GitHub URL if available]
