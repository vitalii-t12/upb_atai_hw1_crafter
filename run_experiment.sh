#!/bin/bash
# Script to run Crafter experiments in parallel with comprehensive data collection
# Usage: ./run_experiment.sh

# Activate virtual environment
source .venv/bin/activate

# Configuration
BASE_LOGDIR="logdir"
STEPS=1000000
EVAL_INTERVAL=50000
EVAL_EPISODES=20

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Timestamp for this run
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

echo -e "${GREEN}======================================${NC}"
echo -e "${GREEN}Crafter Agent Training Experiments${NC}"
echo -e "${GREEN}======================================${NC}"
echo -e "${BLUE}Start time: $(date)${NC}"
echo -e "${BLUE}Logdir: ${BASE_LOGDIR}${NC}"
echo -e "${BLUE}Total steps per run: ${STEPS}${NC}"
echo -e "${BLUE}Eval interval: ${EVAL_INTERVAL}${NC}"
echo ""

# Function to run a single experiment with multiple seeds
run_experiment() {
    local exp_name=$1
    local args=$2
    local seeds=${3:-"0 1 2"}

    echo -e "${YELLOW}═══════════════════════════════════════${NC}"
    echo -e "${YELLOW}Experiment: ${exp_name}${NC}"
    echo -e "${YELLOW}═══════════════════════════════════════${NC}"
    echo "Arguments: ${args}"
    echo "Seeds: ${seeds}"
    echo ""

    # Create experiment directory and save config
    exp_dir="${BASE_LOGDIR}/${exp_name}"
    mkdir -p "${exp_dir}"

    # Save experiment config
    cat > "${exp_dir}/config.txt" <<EOF
Experiment: ${exp_name}
Timestamp: ${TIMESTAMP}
Steps: ${STEPS}
Eval Interval: ${EVAL_INTERVAL}
Eval Episodes: ${EVAL_EPISODES}
Seeds: ${seeds}
Arguments: ${args}
EOF

    for seed in $seeds; do
        logdir="${exp_dir}/${seed}"
        mkdir -p "${logdir}"

        echo -e "  ${GREEN}▶${NC} Launching seed ${seed}"
        echo -e "     Logdir: ${logdir}"

        # Run in background with better output handling
        python train.py \
            --steps $STEPS \
            --eval-interval $EVAL_INTERVAL \
            --eval-episodes $EVAL_EPISODES \
            --logdir $logdir \
            --seed $seed \
            $args \
            > "${exp_dir}/${seed}.log" 2>&1 &

        # Store PID
        pid=$!
        echo $pid >> "${exp_dir}/pids.txt"
        echo -e "     PID: ${pid}"

        # Small delay to avoid GPU contention at startup
        sleep 3
    done

    echo ""
}

# Create base log directory
mkdir -p $BASE_LOGDIR

# ===========================================
# Experiment 1: Random Baseline (for comparison)
# ===========================================
echo -e "${YELLOW}═══════════════════════════════════════${NC}"
echo -e "${YELLOW}Experiment 1: Random Baseline${NC}"
echo -e "${YELLOW}═══════════════════════════════════════${NC}"
echo "Random agent for comparison - Quick runs (100K steps)"
echo ""

exp_dir="${BASE_LOGDIR}/random-baseline"
mkdir -p "${exp_dir}"

# Save config
cat > "${exp_dir}/config.txt" <<EOF
Experiment: random-baseline
Timestamp: ${TIMESTAMP}
Steps: 100000
Eval Interval: 25000
Eval Episodes: ${EVAL_EPISODES}
Seeds: 0 1 2
Description: Random agent (no learning) for baseline comparison
EOF

for seed in 0 1 2; do
    logdir="${exp_dir}/${seed}"
    mkdir -p $logdir

    echo -e "  ${GREEN}▶${NC} Launching random agent seed ${seed}"
    echo -e "     Logdir: ${logdir}"

    # Random agent - use training-starts > steps to prevent learning
    python train.py \
        --steps 100000 \
        --eval-interval 25000 \
        --eval-episodes $EVAL_EPISODES \
        --logdir $logdir \
        --seed $seed \
        --training-starts 1000000 \
        > "${exp_dir}/${seed}.log" 2>&1 &

    pid=$!
    echo $pid >> "${exp_dir}/pids.txt"
    echo -e "     PID: ${pid}"
    sleep 2
done
echo ""

# ===========================================
# Experiment 2: Base DQN (Vanilla)
# ===========================================
echo -e "${YELLOW}═══════════════════════════════════════${NC}"
echo -e "${YELLOW}Experiment 2: Vanilla DQN${NC}"
echo -e "${YELLOW}═══════════════════════════════════════${NC}"
echo "Standard DQN with target network, no enhancements"
echo "Config: 1-step TD, no Double DQN, no Dueling"
echo ""

run_experiment "base-dqn" \
    "" \
    "0 1 2"

# Wait a bit before starting next experiment
sleep 5

# ===========================================
# Experiment 3: Enhanced DQN (Double + Dueling)
# ===========================================
echo -e "${YELLOW}═══════════════════════════════════════${NC}"
echo -e "${YELLOW}Experiment 3: Enhanced DQN${NC}"
echo -e "${YELLOW}═══════════════════════════════════════${NC}"
echo "DQN with Double DQN and Dueling architecture"
echo "Config: 1-step TD, Double DQN, Dueling"
echo ""

run_experiment "enhanced-dqn" \
    "--double-dqn --dueling" \
    "0 1 2"

sleep 5

# ===========================================
# Experiment 4: Enhanced DQN + N-step (n=3)
# ===========================================
echo -e "${YELLOW}═══════════════════════════════════════${NC}"
echo -e "${YELLOW}Experiment 4: DQN + N-step (n=3)${NC}"
echo -e "${YELLOW}═══════════════════════════════════════${NC}"
echo "Enhanced DQN with 3-step returns"
echo ""

run_experiment "dqn-nstep3" \
    "--double-dqn --dueling --n-step 3" \
    "0 1 2"

sleep 5

# ===========================================
# Experiment 5: Enhanced DQN + N-step (n=5)
# ===========================================
echo -e "${YELLOW}═══════════════════════════════════════${NC}"
echo -e "${YELLOW}Experiment 5: DQN + N-step (n=5)${NC}"
echo -e "${YELLOW}═══════════════════════════════════════${NC}"
echo "Enhanced DQN with 5-step returns"
echo ""

run_experiment "dqn-nstep5" \
    "--double-dqn --dueling --n-step 5" \
    "0 1 2"

sleep 5

# ===========================================
# Experiment 6: Full Enhancement (with Munchausen)
# ===========================================
echo -e "${YELLOW}═══════════════════════════════════════${NC}"
echo -e "${YELLOW}Experiment 6: Full Enhanced DQN${NC}"
echo -e "${YELLOW}═══════════════════════════════════════${NC}"
echo "All enhancements: Double + Dueling + N-step + Munchausen"
echo ""

run_experiment "full-enhanced" \
    "--double-dqn --dueling --n-step 3 --munchausen --munchausen-alpha 0.9 --munchausen-tau 0.03" \
    "0 1 2"

# ===========================================
# Wait for all jobs and report
# ===========================================
echo ""
echo -e "${GREEN}════════════════════════════════════════════════${NC}"
echo -e "${GREEN}All experiments launched!${NC}"
echo -e "${GREEN}════════════════════════════════════════════════${NC}"
echo ""
echo -e "${BLUE}Monitoring Commands:${NC}"
echo "  Monitor all experiments:   tail -f ${BASE_LOGDIR}/*/0.log"
echo "  Monitor specific:          tail -f ${BASE_LOGDIR}/full-enhanced/0.log"
echo "  Check all PIDs:            ps aux | grep train.py"
echo "  GPU usage:                 watch -n 1 nvidia-smi"
echo ""
echo -e "${BLUE}Running experiments:${NC}"
for exp in random-baseline base-dqn enhanced-dqn dqn-nstep3 dqn-nstep5 full-enhanced; do
    if [ -f "${BASE_LOGDIR}/${exp}/pids.txt" ]; then
        echo "  ${exp}: $(cat ${BASE_LOGDIR}/${exp}/pids.txt | wc -l) processes"
    fi
done
echo ""
echo -e "${YELLOW}Waiting for all experiments to complete...${NC}"
echo -e "${YELLOW}This will take several hours. Press Ctrl+C to stop.${NC}"
echo ""

# Wait for all background jobs
wait

echo ""
echo -e "${GREEN}════════════════════════════════════════════════${NC}"
echo -e "${GREEN}All training complete! Starting data collection...${NC}"
echo -e "${GREEN}════════════════════════════════════════════════${NC}"
echo ""

# ===========================================
# AUTOMATIC DATA COLLECTION AND ANALYSIS
# ===========================================
echo -e "${BLUE}Generating plots and analysis...${NC}"
echo ""

# Create results directory
RESULTS_DIR="${BASE_LOGDIR}/results_${TIMESTAMP}"
mkdir -p "${RESULTS_DIR}"

echo -e "${YELLOW}1. Generating individual experiment plots...${NC}"
for exp in base-dqn enhanced-dqn dqn-nstep3 dqn-nstep5 full-enhanced random-baseline; do
    if [ -d "${BASE_LOGDIR}/${exp}" ]; then
        echo "  Plotting ${exp}..."
        python analysis/plot_eval_performance.py \
            --logdir "${BASE_LOGDIR}/${exp}" \
            --save-dir "${BASE_LOGDIR}/${exp}/plots" \
            > "${RESULTS_DIR}/${exp}_plot.log" 2>&1
    fi
done
echo ""

echo -e "${YELLOW}2. Generating comparison table...${NC}"
python analysis/aggregate_runs.py \
    --logdir "${BASE_LOGDIR}" \
    --experiments base-dqn enhanced-dqn dqn-nstep3 dqn-nstep5 full-enhanced random-baseline \
    --save "${RESULTS_DIR}/comparison_table.txt" \
    > "${RESULTS_DIR}/aggregate.log" 2>&1
echo ""

echo -e "${YELLOW}3. Creating summary report...${NC}"

# Create comprehensive summary
cat > "${RESULTS_DIR}/SUMMARY.md" <<EOF
# Crafter Experiment Results Summary

**Run Date:** $(date)
**Total Training Steps:** ${STEPS} per agent
**Evaluation Frequency:** Every ${EVAL_INTERVAL} steps
**Seeds per Experiment:** 3 (0, 1, 2)

## Experiments Run

1. **random-baseline** - Random agent (no learning) for comparison
2. **base-dqn** - Standard DQN with Double DQN and Dueling
3. **enhanced-dqn** - DQN with Double DQN and Dueling
4. **dqn-nstep3** - Enhanced DQN with 3-step returns
5. **dqn-nstep5** - Enhanced DQN with 5-step returns
6. **full-enhanced** - All enhancements including Munchausen-DQN

## Files Generated

- Individual plots: \`${BASE_LOGDIR}/<experiment>/plots/\`
  - \`rewards.png\` - Training and evaluation rewards
  - \`training_metrics.png\` - Loss and Q-values
  - \`achievement_spectrum.png\` - Achievement success rates
  - \`summary.png\` - Comprehensive overview

- Comparison: \`${RESULTS_DIR}/comparison_table.txt\`

- Raw metrics: \`${BASE_LOGDIR}/<experiment>/<seed>/metrics.json\`

- Training logs: \`${BASE_LOGDIR}/<experiment>/<seed>/log.txt\`

## Quick Analysis

To view comparison table:
\`\`\`bash
cat ${RESULTS_DIR}/comparison_table.txt
\`\`\`

To view individual experiment results:
\`\`\`bash
ls ${BASE_LOGDIR}/*/plots/
\`\`\`

## Assignment Deliverables Checklist

- [ ] Source code archive (without checkpoints)
- [ ] Slide deck PDF with:
  - [ ] Algorithm description
  - [ ] Performance plots (eval/mean_reward)
  - [ ] Loss and Q-value plots
  - [ ] Comparison with random baseline
  - [ ] Average of 2-3 training runs
  - [ ] Achievement spectrum (bonus)

## Next Steps

1. Review plots in each experiment's \`plots/\` directory
2. Check comparison table for best performing agent
3. Select best agent for presentation
4. Create slide deck using generated plots
5. Archive source code: \`tar -czf submission.tar.gz *.py analysis/ src/ --exclude=logdir/\`

EOF

cat "${RESULTS_DIR}/SUMMARY.md"

echo ""
echo -e "${GREEN}════════════════════════════════════════════════${NC}"
echo -e "${GREEN}DATA COLLECTION COMPLETE!${NC}"
echo -e "${GREEN}════════════════════════════════════════════════${NC}"
echo ""
echo -e "${BLUE}Results saved to:${NC} ${RESULTS_DIR}"
echo ""
echo -e "${BLUE}Quick links:${NC}"
echo "  Summary:     cat ${RESULTS_DIR}/SUMMARY.md"
echo "  Comparison:  cat ${RESULTS_DIR}/comparison_table.txt"
echo "  Plots:       ls ${BASE_LOGDIR}/*/plots/"
echo ""
echo -e "${GREEN}All done! Ready for assignment submission.${NC}"