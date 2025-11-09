# Quick Start Guide - Crafter Assignment

This guide explains how to run experiments and collect all data needed for the assignment.

---

## 🚀 **ONE-COMMAND SOLUTION**

To run all experiments and automatically collect all data:

```bash
chmod +x run_experiment.sh
./run_experiment.sh
```

**What this does:**
1. Runs 6 experiments with 3 seeds each (18 training runs total)
2. Waits for all training to complete (~several hours)
3. Automatically generates all plots
4. Creates comparison tables
5. Generates a comprehensive summary
6. Organizes everything for your assignment submission

**Output:**
- Individual plots in `logdir/<experiment>/plots/`
- Comparison table in `logdir/results_<timestamp>/comparison_table.txt`
- Summary report in `logdir/results_<timestamp>/SUMMARY.md`
- All raw data in `logdir/<experiment>/<seed>/metrics.json`
- Training logs in `logdir/<experiment>/<seed>/log.txt`

---

## 📊 **WHAT DATA GETS COLLECTED**

### **Metrics Tracked (in metrics.json)**

**Training Metrics:**
- `train/episode_reward` - Reward per episode during training
- `train/loss` - TD loss over time
- `train/q_values_mean` - Average Q-values
- `train/q_values_std` - Q-value variance
- `train/target_q_mean` - Target network Q-values
- `train/epsilon` - Exploration rate decay
- `train/achievement_*` - Achievement unlocking during training

**Evaluation Metrics (most important):**
- `eval/mean_reward` - **MANDATORY** Average reward across episodes
- `eval/std_reward` - Standard deviation of rewards
- `eval/mean_length` - Episode length
- `eval/achievement_*` - Success rate for each achievement (22 total)

### **Logs Generated**

**log.txt** - Human-readable training log with:
- Hyperparameter configuration
- Training progress every 10 episodes
- Evaluation results every 50K steps
- Final performance summary
- Achievement success rates

**<seed>.log** - stdout/stderr from training run

**config.txt** - Experiment configuration

---

## 🧪 **EXPERIMENTS RUN**

| Experiment | Description | Purpose |
|------------|-------------|---------|
| `random-baseline` | Random agent (no learning) | Baseline comparison |
| `base-dqn` | Standard DQN | Baseline algorithm |
| `enhanced-dqn` | Double DQN + Dueling | Enhanced baseline |
| `dqn-nstep3` | + 3-step returns | Test credit assignment |
| `dqn-nstep5` | + 5-step returns | Compare n-step values |
| `full-enhanced` | + Munchausen-DQN | All enhancements |

---

## 📈 **PLOTS GENERATED**

Each experiment gets 4 plots in `logdir/<experiment>/plots/`:

1. **rewards.png**
   - Training episode rewards (smoothed)
   - Evaluation mean rewards
   - Shows learning progress over time
   - **Use for assignment requirement: "average episodic reward"**

2. **training_metrics.png**
   - Loss curve (TD error)
   - Q-value evolution
   - **Use for assignment requirement: "loss, q-values, etc."**

3. **achievement_spectrum.png**
   - Bar chart of all 22 achievements
   - Success rates from 0-100%
   - **BONUS: Achievement spectrum per assignment**

4. **summary.png**
   - Evaluation reward over time
   - Episode length over time
   - Comprehensive overview

---

## 🔍 **HOW TO USE THE DATA**

### **For Your Presentation PDF:**

1. **Algorithm Description**
   - Check `HYPERPARAMETERS.md` for detailed explanations
   - Use `logdir/<experiment>/config.txt` for your specific setup

2. **Required Plots**
   - **Episodic reward:** Use `rewards.png` from your best experiment
   - **Loss/Q-values:** Use `training_metrics.png`
   - **Baseline comparison:** Use `comparison_table.txt` or overlay plots

3. **Multiple Seed Averaging**
   - All plots already show mean ± std across 3 seeds
   - Stats in `comparison_table.txt` show mean ± std

4. **Bonus Achievement Spectrum**
   - Use `achievement_spectrum.png`

### **Analyzing Results:**

```bash
# View comparison table
cat logdir/results_*/comparison_table.txt

# View detailed logs
cat logdir/full-enhanced/0/log.txt

# Check metrics programmatically
python -c "import json; print(json.load(open('logdir/full-enhanced/0/metrics.json'))['metrics'].keys())"
```

---

## 🛠️ **MANUAL OPERATIONS**

### **Run Single Experiment:**

```bash
# Run one seed
python train.py --logdir logdir/my-test/0 --seed 0

# Run with custom hyperparameters
python train.py \
    --logdir logdir/custom/0 \
    --seed 0 \
    --lr 2e-4 \
    --n-step 5 \
    --munchausen
```

### **Generate Plots Manually:**

```bash
# For one experiment
python analysis/plot_eval_performance.py --logdir logdir/full-enhanced

# For comparison
python analysis/aggregate_runs.py --logdir logdir
```

### **Quick Test Run:**

```bash
# Short run for testing (200K steps)
python train.py \
    --logdir logdir/quick-test \
    --steps 200000 \
    --eval-interval 25000
```

---

## 📦 **ASSIGNMENT SUBMISSION**

### **Files to Submit:**

1. **Source Code Archive** (no checkpoints!)
```bash
tar -czf surname_name_middlename.zip \
    train.py agent.py networks.py replay_buffer.py utils.py \
    src/ analysis/ \
    HYPERPARAMETERS.md \
    --exclude='*.pyc' --exclude='__pycache__'
```

2. **PDF Slide Deck**
   - Use plots from `logdir/*/plots/`
   - Include comparison with random baseline
   - Show algorithm description

### **What NOT to Include:**

- ❌ Checkpoint files (*.pt)
- ❌ logdir/ directory
- ❌ metrics.json files
- ❌ Video files

The assignment says: **"Make sure not to include any large files such as checkpoints."**

---

## 📊 **DATA FOR BACKTRACING**

You asked how to backtrace model performance. Here's what each log tells you:

### **metrics.json** - Complete training history

```python
import json
import matplotlib.pyplot as plt

# Load metrics
with open('logdir/full-enhanced/0/metrics.json') as f:
    data = json.load(f)

# Analyze when reward milestone was reached
rewards = data['metrics']['eval/mean_reward']
steps = data['steps']['eval/mean_reward']
milestone_idx = next(i for i, r in enumerate(rewards) if r > 5.0)
print(f"Reached reward > 5.0 at step {steps[milestone_idx]}")

# Check if loss was stable
loss = data['metrics']['train/loss']
if max(loss[-100:]) > 10 * min(loss[-100:]):
    print("Warning: Loss unstable in final 100 updates!")

# Find which achievements were learned when
for achievement in data['metrics'].keys():
    if 'achievement' in achievement:
        rates = data['metrics'][achievement]
        if max(rates) > 10:
            first_unlock = next(i for i, r in enumerate(rates) if r > 10)
            print(f"{achievement}: first >10% at step {steps[first_unlock]}")
```

### **log.txt** - Human-readable history

```bash
# See training progress
grep "Step:" logdir/full-enhanced/0/log.txt

# See all evaluations
grep "Eval -" logdir/full-enhanced/0/log.txt

# Check final results
tail -50 logdir/full-enhanced/0/log.txt
```

### **Backtracing Specific Issues:**

**Problem: Agent stopped improving**
- Check `eval/mean_reward` - plateaued?
- Check `train/epsilon` - exploration ended?
- Check `train/loss` - diverged?
- Check `train/q_values_mean` - exploded?

**Problem: Some achievements never unlocked**
- Check `eval/achievement_*` for those skills
- Look at epsilon decay timing
- Check if those skills require prerequisites

**Problem: Training unstable**
- Check `train/loss` for spikes
- Check `train/q_values_std` for variance
- Check hyperparameters (lr too high?)

---

## ⚙️ **HYPERPARAMETER INFLUENCE**

See `HYPERPARAMETERS.md` for complete guide. Quick reference:

| Parameter | Affects | Logged In |
|-----------|---------|-----------|
| `--lr` | Training speed/stability | `train/loss` stability |
| `--gamma` | Long-term planning | `train/q_values_mean` magnitude |
| `--n-step` | Credit assignment | `eval/achievement_*` unlock speed |
| `--epsilon-*` | Exploration | `train/epsilon`, achievement diversity |
| `--batch-size` | Gradient stability | `train/loss` noise |
| `--double-dqn` | Q-value accuracy | `train/q_values_mean` overestimation |
| `--dueling` | Value estimation | Learning speed |
| `--munchausen` | Exploration quality | Achievement diversity |

---

## 🎯 **MONITORING DURING TRAINING**

```bash
# Watch progress
tail -f logdir/full-enhanced/0.log

# Check if still running
ps aux | grep train.py

# Monitor GPU
watch -n 1 nvidia-smi

# Check current step
grep -a "Step:" logdir/full-enhanced/0/log.txt | tail -1

# See latest eval
grep -a "Eval -" logdir/full-enhanced/0/log.txt | tail -1
```

---

## 🆘 **TROUBLESHOOTING**

**Q: Folders created but empty?**
- Training might not have completed yet
- Check if processes are running: `ps aux | grep train.py`
- Check log files: `tail logdir/*/0.log`

**Q: metrics.json missing?**
- Training must complete for metrics to save
- Periodic saves happen every eval interval
- Final save at end of training

**Q: log.txt empty?**
- Fixed in latest version! Uses `logger.print_and_log()`
- If running old version, restart training

**Q: Plots not generating?**
- Needs metrics.json to exist
- Run manually: `python analysis/plot_eval_performance.py --logdir logdir/<exp>`

**Q: Out of memory?**
- Reduce `--buffer-size` (100000 → 50000)
- Reduce `--batch-size` (32 → 16)
- Run fewer seeds in parallel

---

## ✅ **VERIFICATION CHECKLIST**

Before submission, verify:

- [ ] `run_experiment.sh` completed successfully
- [ ] All experiments have `metrics.json` files
- [ ] All experiments have plots in `plots/` subdirectory
- [ ] Comparison table exists in `results_*/comparison_table.txt`
- [ ] log.txt files contain training logs (not empty)
- [ ] At least 2-3 seeds per experiment completed
- [ ] Random baseline completed for comparison
- [ ] Source code tarball created (no checkpoints!)
- [ ] PDF presentation uses generated plots

---

## 📚 **FURTHER READING**

- **Hyperparameters:** See `HYPERPARAMETERS.md`
- **Assignment:** `docs/assignment_hw1.pdf`
- **Code Structure:** Check docstrings in `train.py`, `agent.py`, etc.
- **Crafter Benchmark:** https://github.com/danijar/crafter

---

**All set! Run `./run_experiment.sh` and wait for completion. Everything will be collected automatically!**
