#!/bin/bash
# Script to test EXTENDED EPSILON EXPLORATION
# Runs experiments with longer epsilon decay to test exploration improvements
# Usage: ./run_experiment_extended_exploration.sh

# Activate virtual environment
source .venv/bin/activate

# Configuration
BASE_LOGDIR="logdir_extended_exploration"
STEPS=1000000
EVAL_INTERVAL=50000
EVAL_EPISODES=20

# Extended exploration settings
EPSILON_DECAY_STEPS=200000  # 4x longer than default (50K -> 200K)
EPSILON_END=0.05            # Keep higher minimum exploration (0.01 -> 0.05)

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Timestamp for this run
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Extended Epsilon Exploration Experiments${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e "${BLUE}Start time: $(date)${NC}"
echo -e "${BLUE}Logdir: ${BASE_LOGDIR}${NC}"
echo -e "${BLUE}Total steps per run: ${STEPS}${NC}"
echo -e "${BLUE}Eval interval: ${EVAL_INTERVAL}${NC}"
echo -e "${BLUE}Epsilon decay steps: ${EPSILON_DECAY_STEPS}${NC}"
echo -e "${BLUE}Epsilon end: ${EPSILON_END}${NC}"
echo -e "${BLUE}Mode: ONE SEED AT A TIME (memory safe)${NC}"
echo ""

# Function to run a single experiment with ONE SEED at a time
run_experiment_single_seed() {
    local exp_name=$1
    local args=$2
    local seeds=${3:-"0 1 2"}

    echo -e "${YELLOW}═══════════════════════════════════════${NC}"
    echo -e "${YELLOW}Experiment: ${exp_name}${NC}"
    echo -e "${YELLOW}═══════════════════════════════════════${NC}"
    echo "Arguments: ${args}"
    echo "Seeds: ${seeds}"
    echo "Running SEQUENTIALLY (one seed at a time)"
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
Epsilon Decay Steps: ${EPSILON_DECAY_STEPS}
Epsilon End: ${EPSILON_END}
Description: Extended epsilon exploration experiment
EOF

    local exp_start_time=$(date +%s)

    # Run each seed SEQUENTIALLY
    for seed in $seeds; do
        logdir="${exp_dir}/${seed}"
        mkdir -p "${logdir}"

        echo -e "  ${GREEN}▶${NC} Running seed ${seed}..."
        echo -e "     Logdir: ${logdir}"

        local seed_start_time=$(date +%s)

        # Run and WAIT for completion
        python train.py \
            --steps $STEPS \
            --eval-interval $EVAL_INTERVAL \
            --eval-episodes $EVAL_EPISODES \
            --logdir $logdir \
            --seed $seed \
            --epsilon-decay-steps $EPSILON_DECAY_STEPS \
            --epsilon-end $EPSILON_END \
            $args \
            > "${exp_dir}/${seed}.log" 2>&1

        local seed_end_time=$(date +%s)
        local seed_duration=$((seed_end_time - seed_start_time))
        local hours=$((seed_duration / 3600))
        local minutes=$(((seed_duration % 3600) / 60))
        local seconds=$((seed_duration % 60))

        echo -e "  ${GREEN}✓${NC} Seed ${seed} completed in ${hours}h ${minutes}m ${seconds}s"
        echo ""
    done

    local exp_end_time=$(date +%s)
    local exp_duration=$((exp_end_time - exp_start_time))
    local hours=$((exp_duration / 3600))
    local minutes=$(((exp_duration % 3600) / 60))
    local seconds=$((exp_duration % 60))

    echo ""
    echo -e "${GREEN}════════════════════════════════════════${NC}"
    echo -e "${GREEN}Experiment ${exp_name} COMPLETE!${NC}"
    echo -e "${GREEN}Total time: ${hours}h ${minutes}m ${seconds}s${NC}"
    echo -e "${GREEN}════════════════════════════════════════${NC}"
    echo ""
}

# Create base log directory
mkdir -p $BASE_LOGDIR

# Track overall progress
TOTAL_EXPERIMENTS=3
CURRENT_EXP=0
OVERALL_START_TIME=$(date +%s)

# ===========================================
# Experiment 1: Base DQN with Extended Exploration
# ===========================================
CURRENT_EXP=$((CURRENT_EXP + 1))
echo -e "${BLUE}╔════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║ [${CURRENT_EXP}/${TOTAL_EXPERIMENTS}] Base DQN + Extended Epsilon      ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════╝${NC}"
echo ""
echo "Testing vanilla DQN with:"
echo "  - Epsilon decay over 200K steps (vs 50K default)"
echo "  - Minimum epsilon 0.05 (vs 0.01 default)"
echo ""
run_experiment_single_seed "base-dqn-extended" "" "0 1 2"

# ===========================================
# Experiment 2: Enhanced DQN with Extended Exploration
# ===========================================
CURRENT_EXP=$((CURRENT_EXP + 1))
echo -e "${BLUE}╔════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║ [${CURRENT_EXP}/${TOTAL_EXPERIMENTS}] Enhanced DQN + Extended Epsilon  ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════╝${NC}"
echo ""
echo "Testing Double DQN + Dueling with extended exploration"
echo ""
run_experiment_single_seed "enhanced-dqn-extended" "--double-dqn --dueling" "0 1 2"

# ===========================================
# Experiment 3: Full Enhancement with Extended Exploration
# ===========================================
CURRENT_EXP=$((CURRENT_EXP + 1))
echo -e "${BLUE}╔════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║ [${CURRENT_EXP}/${TOTAL_EXPERIMENTS}] Full Enhanced + Extended Epsilon ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════╝${NC}"
echo ""
echo "Testing all enhancements with extended exploration:"
echo "  - Double DQN + Dueling + N-step + Munchausen"
echo "  - Extended epsilon exploration"
echo ""
run_experiment_single_seed "full-enhanced-extended" "--double-dqn --dueling --n-step 3 --munchausen --munchausen-alpha 0.9 --munchausen-tau 0.03" "0 1 2"

# ===========================================
# All experiments complete
# ===========================================
OVERALL_END_TIME=$(date +%s)
OVERALL_DURATION=$((OVERALL_END_TIME - OVERALL_START_TIME))
OVERALL_HOURS=$((OVERALL_DURATION / 3600))
OVERALL_MINUTES=$(((OVERALL_DURATION % 3600) / 60))
OVERALL_SECONDS=$((OVERALL_DURATION % 60))

echo ""
echo -e "${GREEN}════════════════════════════════════════════════${NC}"
echo -e "${GREEN}ALL EXTENDED EXPLORATION EXPERIMENTS COMPLETE!${NC}"
echo -e "${GREEN}Total time: ${OVERALL_HOURS}h ${OVERALL_MINUTES}m ${OVERALL_SECONDS}s${NC}"
echo -e "${GREEN}════════════════════════════════════════════════${NC}"
echo ""
echo -e "${BLUE}Generating plots and comparison...${NC}"
echo ""

# ===========================================
# DATA COLLECTION AND ANALYSIS
# ===========================================

# Create results directory
RESULTS_DIR="${BASE_LOGDIR}/results_${TIMESTAMP}"
mkdir -p "${RESULTS_DIR}"

echo -e "${YELLOW}1. Generating individual experiment plots...${NC}"
for exp in base-dqn-extended enhanced-dqn-extended full-enhanced-extended; do
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
    --experiments base-dqn-extended enhanced-dqn-extended full-enhanced-extended \
    --save "${RESULTS_DIR}/comparison_table.txt" \
    > "${RESULTS_DIR}/aggregate.log" 2>&1
echo ""

echo -e "${YELLOW}3. Creating summary report...${NC}"

# Create comprehensive summary
cat > "${RESULTS_DIR}/SUMMARY.md" <<EOF
# Extended Epsilon Exploration Results

**Run Date:** $(date)
**Total Training Time:** ${OVERALL_HOURS}h ${OVERALL_MINUTES}m ${OVERALL_SECONDS}s
**Total Training Steps:** ${STEPS} per agent
**Evaluation Frequency:** Every ${EVAL_INTERVAL} steps
**Seeds per Experiment:** 3 (0, 1, 2)

## Extended Exploration Configuration

- **Epsilon Decay Steps:** ${EPSILON_DECAY_STEPS} (vs 50K default)
- **Minimum Epsilon:** ${EPSILON_END} (vs 0.01 default)
- **Goal:** Test if longer exploration period improves Crafter performance

## Epsilon Schedule Comparison

### Default Schedule (baseline experiments):
- Steps 0-50K: ε decays from 1.0 → 0.01
- Steps 50K-1M: ε = 0.01 (99% exploitation)

### Extended Schedule (these experiments):
- Steps 0-200K: ε decays from 1.0 → 0.05
- Steps 200K-1M: ε = 0.05 (95% exploitation, 5x more exploration)

## Experiments Run

1. **base-dqn-extended** - Vanilla DQN with extended exploration
2. **enhanced-dqn-extended** - Double DQN + Dueling with extended exploration
3. **full-enhanced-extended** - All enhancements + extended exploration

## Expected Benefits

- More time to discover achievements and strategies
- Better coverage of state space
- Potentially higher final performance
- May help avoid local optima

## Files Generated

- Individual plots: \`${BASE_LOGDIR}/<experiment>/plots/\`
- Comparison: \`${RESULTS_DIR}/comparison_table.txt\`
- Training logs: \`${BASE_LOGDIR}/<experiment>/<seed>/log.txt\`
- Metadata: \`${BASE_LOGDIR}/<experiment>/<seed>/metadata.json\`

## How to Compare with Baseline

Compare these results with the baseline experiments in \`logdir/\`:
- \`logdir/base-dqn/\` vs \`logdir_extended_exploration/base-dqn-extended/\`
- \`logdir/enhanced-dqn/\` vs \`logdir_extended_exploration/enhanced-dqn-extended/\`
- \`logdir/full-enhanced/\` vs \`logdir_extended_exploration/full-enhanced-extended/\`

## Quick Analysis

\`\`\`bash
# View results
cat ${RESULTS_DIR}/comparison_table.txt

# Compare with baseline
cat logdir/results_*/comparison_table.txt
\`\`\`

EOF

cat "${RESULTS_DIR}/SUMMARY.md"

echo ""
echo -e "${GREEN}════════════════════════════════════════════════${NC}"
echo -e "${GREEN}RESULTS SUMMARY COMPLETE!${NC}"
echo -e "${GREEN}════════════════════════════════════════════════${NC}"
echo ""
echo -e "${BLUE}Results saved to:${NC} ${RESULTS_DIR}"
echo ""
echo -e "${BLUE}Next steps:${NC}"
echo "  1. Compare with baseline experiments in logdir/"
echo "  2. Check if extended exploration improves final performance"
echo "  3. Look for higher achievement rates"
echo ""
echo -e "${GREEN}Done!${NC}"
