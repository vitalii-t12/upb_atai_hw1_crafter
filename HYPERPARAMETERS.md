# Hyperparameter Guide for Crafter DQN Agent

This document provides a comprehensive explanation of each hyperparameter, what it influences, and how to tune it.

---

## 📊 **ENVIRONMENT & TRAINING SETTINGS**

### `--steps` (default: 1,000,000)
**What it does:** Total number of environment steps to train for.
**Influences:**
- Training duration (more steps = longer training, better performance)
- Crafter is designed for 1M steps as a benchmark limit
- Too few steps: Agent won't learn complex behaviors
- Too many steps: Diminishing returns, wasted compute

**Recommendation:** Keep at 1M for fair comparison with Crafter benchmarks

---

### `--eval-interval` (default: 50,000)
**What it does:** How often to pause training and evaluate the agent.
**Influences:**
- Frequency of evaluation data points (for plotting)
- Training time (evaluation pauses training)
- Granularity of performance curve

**Impact on logging:**
- More frequent = smoother eval curves, but slower training
- 50K steps → 20 evaluation points over 1M steps (good resolution)
- Less frequent (e.g., 100K) → fewer data points, faster training

**Recommendation:** 50K for good temporal resolution

---

### `--eval-episodes` (default: 20)
**What it does:** Number of episodes to run during each evaluation.
**Influences:**
- Statistical reliability of evaluation metrics
- Evaluation time
- Variance in reported performance

**Why it matters:**
- Crafter has stochastic map generation → high variance
- More episodes = more reliable mean reward estimate
- 20 episodes gives good balance of accuracy vs. speed

**Recommendation:** 20-30 episodes for reliable statistics

---

### `--seed` (default: 0)
**What it does:** Random seed for reproducibility.
**Influences:**
- All random number generation (exploration, env resets, weight init)
- Makes experiments reproducible
- Different seeds → different training trajectories

**Why run multiple seeds:**
- RL is high variance
- Assignment requires 2-3 seeds to average results
- Shows robustness of algorithm

**Recommendation:** Run seeds 0, 1, 2 for each experiment

---

## 🧠 **NETWORK ARCHITECTURE**

### `--hidden-size` (default: 512)
**What it does:** Number of neurons in hidden layers of the Q-network.
**Influences:**
- Model capacity (ability to learn complex patterns)
- Training speed and memory usage
- Overfitting vs. underfitting

**Trade-offs:**
- **Smaller (256):** Faster, less memory, may underfit
- **Larger (1024):** More capacity, slower, may overfit
- Crafter has complex visual patterns → needs decent capacity

**Recommendation:** 512 is a good balance for Crafter

---

## 🎓 **LEARNING HYPERPARAMETERS**

### `--lr` (default: 1e-4)
**What it does:** Learning rate for Adam optimizer.
**Influences:**
- How fast the network updates weights
- Training stability and convergence speed

**Impact:**
- **Too high (1e-3):** Unstable, Q-values may diverge, training crashes
- **Too low (1e-5):** Very slow learning, may not converge in 1M steps
- **Just right (1e-4):** Stable, reasonable convergence

**What to watch in logs:**
- If loss oscillates wildly → reduce lr
- If loss barely decreases → increase lr
- If Q-values explode → reduce lr immediately

**Recommendation:** 1e-4 is well-tested for DQN on Atari-like tasks

---

### `--batch-size` (default: 32)
**What it does:** Number of transitions sampled from replay buffer per update.
**Influences:**
- Gradient estimate quality (larger = less noisy)
- Training stability
- GPU utilization and speed
- Sample efficiency

**Trade-offs:**
- **Smaller (16):** Noisier gradients, less stable, faster iteration
- **Larger (64, 128):** Smoother gradients, more stable, slower, better GPU use
- Crafter is complex → benefits from stable gradients

**What to watch:**
- If loss is very noisy → increase batch size
- If training is slow → decrease batch size (if GPU underutilized)

**Recommendation:** 32-64 for good stability/speed balance

---

### `--gamma` (default: 0.99)
**What it does:** Discount factor for future rewards.
**Influences:**
- How much agent values future vs. immediate rewards
- Credit assignment over time
- Planning horizon

**Impact:**
- **γ = 0.9:** Short-sighted, values next 10 steps heavily
- **γ = 0.99:** Looks ~100 steps ahead, good for long-term planning
- **γ = 0.999:** Very far-sighted, slower learning

**For Crafter:**
- Many achievements require long action sequences (e.g., crafting tools)
- Need high gamma to propagate reward back through long chains
- 0.99 is standard for complex tasks

**Recommendation:** 0.99 (don't change unless you have good reason)

---

### `--grad-clip` (default: 10.0)
**What it does:** Maximum gradient norm before clipping.
**Influences:**
- Training stability (prevents gradient explosion)
- Protection against outlier transitions
- Convergence smoothness

**Why it matters:**
- DQN can have large Q-values → large gradients
- Rare high-reward events can cause gradient spikes
- Clipping prevents catastrophic updates

**What to watch:**
- If training becomes unstable after initially working → gradients exploding
- Check `torch.nn.utils.clip_grad_norm_` output (if logged)

**Recommendation:** 10.0 is standard for DQN

---

## 💾 **REPLAY BUFFER**

### `--buffer-size` (default: 100,000)
**What it does:** Maximum number of transitions stored in replay buffer.
**Influences:**
- Memory usage (~4GB for 100K with image observations)
- Diversity of training data
- Sample efficiency
- Correlation between consecutive samples

**Trade-offs:**
- **Smaller (50K):** Less memory, more correlated samples, less diverse
- **Larger (1M):** Very diverse, breaks correlation, but huge memory cost
- Crafter episodes are ~1000 steps → 100K = ~100 episodes

**Impact on learning:**
- Larger buffer = more diverse experiences = better generalization
- But very old experiences may be from bad policy (off-policy staleness)

**Recommendation:** 100K-500K depending on available RAM

---

### `--training-starts` (default: 5,000)
**What it does:** Environment steps before training begins (random exploration).
**Influences:**
- Initial replay buffer diversity
- Training stability (don't train on empty buffer)
- Exploration coverage early on

**Why it matters:**
- Need enough diverse experiences before training
- Too low → training on mostly random noise
- Too high → wasted time (not learning)

**Recommendation:** 5K-10K (5-10 episodes of random exploration)

---

### `--update-freq` (default: 4)
**What it does:** Environment steps between gradient updates.
**Influences:**
- Training speed vs. sample efficiency
- How many times each experience is used
- Computational efficiency

**Impact:**
- **update-freq=1:** Update after every step (slow, max sample efficiency)
- **update-freq=4:** Update every 4 steps (4x faster, still good)
- **update-freq=16:** Much faster but less sample efficient

**Trade-off:**
- Lower = more updates = slower but better learning
- Higher = fewer updates = faster but may learn slower

**Recommendation:** 4 is DQN standard (from original paper)

---

### `--target-update-freq` (default: 2,500)
**What it does:** Steps between copying Q-network to target network.
**Influences:**
- Training stability (target network provides stable TD targets)
- Convergence speed
- Risk of moving target problem

**Why target networks:**
- TD learning uses Q(s',a') as target for Q(s,a)
- If both update every step → chasing moving target → instability
- Fixed target network for N steps → stable targets

**Impact:**
- **Too frequent (500):** Targets change too fast, instability
- **Too slow (10K):** Targets become stale, slow learning
- 2500 ≈ 2-3 episodes in Crafter

**Recommendation:** 2000-5000 steps

---

## 🔍 **EXPLORATION**

### `--epsilon-start` (default: 1.0)
**What it does:** Initial probability of random action.
**Influences:**
- Early exploration coverage
- Initial data diversity in replay buffer

**Why 1.0:**
- Start with pure random exploration
- Ensure diverse experiences before exploitation
- Critical for discovering rare achievements

**Recommendation:** Keep at 1.0

---

### `--epsilon-end` (default: 0.01)
**What it does:** Final epsilon after decay.
**Influences:**
- Long-term exploration rate
- Exploitation vs. exploration balance
- Achievement discovery later in training

**Impact:**
- **0.0:** Pure exploitation (risky, may get stuck in local optima)
- **0.01:** 1% random actions (standard, maintains minimal exploration)
- **0.1:** 10% random (too much, hurts performance)

**For Crafter:**
- Need some exploration throughout (procedural maps = never see exact same state)
- 1% is good balance

**Recommendation:** 0.01

---

### `--epsilon-decay-steps` (default: 50,000)
**What it does:** Steps over which epsilon decays from start to end.
**Influences:**
- Exploration→exploitation transition speed
- When agent starts exploiting learned policy

**Impact:**
- **Too fast (10K):** Exploits too early, may miss achievements
- **Too slow (500K):** Random too long, slow learning
- 50K = first 5% of training for exploration-heavy

**What to watch in logs:**
- Check `train/epsilon` curve
- Agent should start learning before epsilon decays completely

**Recommendation:** 50K-100K (5-10% of total steps)

---

## ⚡ **DQN ENHANCEMENTS**

### `--double-dqn` (default: True)
**What it does:** Use Double DQN algorithm to select target actions.
**Influences:**
- Reduces overestimation bias in Q-values
- More accurate value estimates
- Better performance (usually)

**How it works:**
- Standard DQN: `max_a Q_target(s', a)` → picks highest Q (biased upward)
- Double DQN: `Q_target(s', argmax_a Q_online(s', a))` → decouple selection from evaluation

**Impact on logs:**
- `train/q_values_mean` should be more stable
- Less likely to see Q-value explosion
- Better final performance

**Recommendation:** Always use (proven improvement)

---

### `--dueling` (default: True)
**What it does:** Use Dueling network architecture.
**Influences:**
- Better value estimation (separates state value from action advantage)
- Faster learning (especially when actions don't matter)
- Network capacity allocation

**How it works:**
- Standard: Q(s,a) directly
- Dueling: Q(s,a) = V(s) + A(s,a) where V = state value, A = advantage

**Why it helps:**
- Many states have similar value regardless of action
- Dueling learns "this state is good" separately from "this action is better"
- More efficient learning

**Recommendation:** Always use (proven improvement)

---

### `--n-step` (default: 3)
**What it does:** Use n-step returns instead of 1-step TD.
**Influences:**
- Credit assignment speed (how fast rewards propagate)
- Bias-variance tradeoff in value estimates
- Learning efficiency

**How it works:**
- **1-step:** r + γ Q(s', a') — low variance, high bias
- **3-step:** r₀ + γr₁ + γ²r₂ + γ³ Q(s₃, a₃) — medium variance, lower bias
- **∞-step:** Monte Carlo (full return) — no bias, high variance

**Impact on Crafter:**
- Achievements have sparse rewards separated by many steps
- N-step helps bridge the gap faster
- Too large → noisy estimates

**What to watch:**
- Compare n=1, n=3, n=5 in your experiments
- Check if eval reward improves faster with n-step

**Recommendation:** 3-5 for Crafter (good for credit assignment)

---

### `--munchausen` (default: False)
**What it does:** Add Munchausen-DQN modification (scaled log-policy to reward).
**Influences:**
- Implicit entropy regularization
- Policy smoothness
- Exploration quality
- Convergence stability

**How it works:**
- Adds `α * log π(a|s)` to reward
- Encourages visiting diverse states
- Regularizes policy (smoother Q-values)

**Impact:**
- Better exploration (implicit entropy bonus)
- More stable training
- Slightly more complex (two extra hyperparameters)

**When to use:**
- If standard DQN plateaus
- If you want better exploration
- For complex environments like Crafter

**Recommendation:** Try with and without (experimental)

---

### `--munchausen-alpha` (default: 0.9)
**What it does:** Scaling factor for Munchausen log-policy term.
**Influences:**
- Strength of entropy regularization
- How much exploration is encouraged

**Impact:**
- **α = 0:** No Munchausen (standard DQN)
- **α = 0.9:** Strong regularization (original paper value)
- **α > 1:** Very strong (may be unstable)

**Recommendation:** 0.9 if using Munchausen

---

### `--munchausen-tau` (default: 0.03)
**What it does:** Temperature for softmax in Munchausen-DQN.
**Influences:**
- Entropy of the implicit policy
- Exploration diversity

**Impact:**
- **Low τ (0.01):** Sharper policy (more exploitative)
- **High τ (0.1):** Softer policy (more exploratory)

**Recommendation:** 0.03 (original paper value)

---

## 💾 **CHECKPOINTING**

### `--save-freq` (default: 100,000)
**What it does:** Steps between saving model checkpoints.
**Influences:**
- Disk space usage
- Recovery options if training crashes
- Ability to resume training

**Why it matters:**
- 1M steps = ~several hours
- Crashes happen → need checkpoints
- Can analyze agent at different training stages

**Recommendation:** 100K (10 checkpoints over 1M steps)

---

### `--resume` (default: None)
**What it does:** Path to checkpoint to resume training from.
**Influences:**
- Allows continuing interrupted training
- Useful for extending training beyond 1M steps
- Recovers from crashes

**Usage:**
```bash
python train.py --resume logdir/my-agent/0/checkpoint_500000.pt
```

---

## 📈 **HOW HYPERPARAMETERS AFFECT LOGGING**

### **Loss (train/loss):**
- `lr` too high → loss oscillates wildly
- `batch-size` too small → noisy loss curve
- `grad-clip` preventing explosions → smooth loss
- `gamma` affects loss magnitude

### **Q-values (train/q_values_mean):**
- `gamma` affects final Q-value magnitude (higher γ → higher Q)
- `double-dqn` prevents overestimation → more stable Q
- `n-step` can increase Q-values (multi-step returns)
- Watch for divergence (Q increasing without bound → problem!)

### **Episode Reward (train/episode_reward):**
- `epsilon` high early → low reward (random actions)
- As epsilon decays → reward should increase (if learning)
- `n-step`, `double-dqn`, `dueling` → faster reward growth
- Plateau → need better exploration or longer training

### **Eval Reward (eval/mean_reward):**
- Most important metric (pure exploitation performance)
- Should be higher than training reward (epsilon=0 during eval)
- Use for comparing algorithms
- Should increase over time (if not → hyperparameter issue)

---

## 🎯 **RECOMMENDED CONFIGURATIONS FOR EXPERIMENTS**

### **Baseline DQN:**
```bash
--double-dqn --dueling --n-step 1 --lr 1e-4 --batch-size 32
```
Good for understanding if enhancements help.

### **Enhanced DQN (Default - Best Performance):**
```bash
--double-dqn --dueling --n-step 3 --lr 1e-4 --batch-size 32
```
This is your default in train.py - well-balanced.

### **Experimental (Maximum Enhancements):**
```bash
--double-dqn --dueling --n-step 3 --munchausen --lr 1e-4 --batch-size 64
```
Best performance but slower.

### **Fast Development:**
```bash
--steps 200000 --eval-interval 25000 --buffer-size 50000
```
For quick testing (not for final results).

---

## 🔬 **USING LOGS TO TUNE HYPERPARAMETERS**

### **Problem: Training unstable (loss spikes)**
**Check:** `train/loss`, `train/q_values_mean`
**Solutions:**
- Reduce `lr` (1e-4 → 5e-5)
- Increase `batch-size` (32 → 64)
- Reduce `grad-clip` (10 → 5)

### **Problem: Learning too slow**
**Check:** `eval/mean_reward` barely improving
**Solutions:**
- Increase `lr` (1e-4 → 2e-4)
- Decrease `epsilon-decay-steps` (exploit sooner)
- Increase `n-step` (faster credit assignment)
- Decrease `update-freq` (more updates)

### **Problem: Q-values exploding**
**Check:** `train/q_values_mean` increasing without bound
**Solutions:**
- Reduce `lr` immediately
- Reduce `gamma` (0.99 → 0.95)
- Check `grad-clip` is working
- May need to restart training

### **Problem: Poor exploration (low achievements)**
**Check:** `eval/achievement_*` metrics
**Solutions:**
- Increase `epsilon-end` (0.01 → 0.05)
- Increase `epsilon-decay-steps` (explore longer)
- Try `--munchausen` for implicit exploration
- Increase `eval-episodes` (might just be high variance)

---

## 📊 **HYPERPARAMETER SENSITIVITY (Rough Guide)**

**High Impact (tune carefully):**
- `lr` — Wrong value = failure
- `gamma` — Critical for long-term tasks
- `n-step` — Big impact on Crafter performance
- `epsilon-decay-steps` — Affects exploration quality

**Medium Impact (reasonable defaults work):**
- `batch-size` — Affects stability/speed tradeoff
- `buffer-size` — Larger usually better (if you have RAM)
- `target-update-freq` — Broad range works (1K-5K)
- `grad-clip` — Protects against disasters

**Low Impact (don't worry much):**
- `hidden-size` — 256-512 all work reasonably
- `eval-interval` — Just affects plot resolution
- `save-freq` — Just for checkpointing
- `update-freq` — 1-4 all reasonable

---

## 🎓 **FURTHER READING**

- **DQN:** Mnih et al., "Playing Atari with Deep Reinforcement Learning" (2013)
- **Double DQN:** van Hasselt et al., "Deep Reinforcement Learning with Double Q-learning" (2016)
- **Dueling DQN:** Wang et al., "Dueling Network Architectures" (2016)
- **N-step Returns:** Sutton & Barto, "Reinforcement Learning: An Introduction" Chapter 7
- **Munchausen-DQN:** Vieillard et al., "Munchausen Reinforcement Learning" (2020)
- **Crafter:** Hafner, "Benchmarking the Spectrum of Agent Capabilities" (2021)

---

This guide should help you understand what each parameter does and how to analyze your logs to diagnose issues!
