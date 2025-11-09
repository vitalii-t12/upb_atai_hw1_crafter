#!/bin/bash
# Script to run Crafter experiments in parallel
# Usage: ./run_experiments.sh

# Configuration
BASE_LOGDIR="logdir"
STEPS=1000000
EVAL_INTERVAL=50000

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}======================================${NC}"
echo -e "${GREEN}Crafter Agent Training Experiments${NC}"
echo -e "${GREEN}======================================${NC}"
echo ""

# Function to run a single experiment with multiple seeds
run_experiment() {
    local exp_name=$1
    local args=$2
    local seeds=${3:-"0 1 2"}

    echo -e "${YELLOW}Starting experiment: ${exp_name}${NC}"
    echo "Arguments: ${args}"
    echo "Seeds: ${seeds}"
    echo ""

    for seed in $seeds; do
        logdir="${BASE_LOGDIR}/${exp_name}/${seed}"

        echo -e "  ${GREEN}▶${NC} Launching seed ${seed} (logdir: ${logdir})"

        # Run in background
        python train.py \
            --steps $STEPS \
            --eval-interval $EVAL_INTERVAL \
            --logdir $logdir \
            --seed $seed \
            $args \
            > "${logdir}.log" 2>&1 &

        # Store PID
        echo $! >> "${BASE_LOGDIR}/${exp_name}/pids.txt"

        # Small delay to avoid GPU contention at startup
        sleep 2
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
echo "For comparison only - Quick runs"
echo ""

mkdir -p "${BASE_LOGDIR}/random-baseline"
for seed in 0 1 2; do
    logdir="${BASE_LOGDIR}/random-baseline/${seed}"
    mkdir -p $logdir

    echo -e "  ${GREEN}▶${NC} Running random agent (seed ${seed})"

    # Random agent - use simpler evaluation for speed
    python train.py \
        --steps 100000 \
        --eval-interval 25000 \
        --logdir $logdir \
        --seed $seed \
        --training-starts 1000000 \
        > "${logdir}.log" 2>&1 &

    echo $! >> "${BASE_LOGDIR}/random-baseline/pids.txt"
    sleep 1
done
echo ""

# ===========================================
# Experiment 2: Base DQN
# ===========================================
echo -e "${YELLOW}═══════════════════════════════════════${NC}"
echo -e "${YELLOW}Experiment 2: Base DQN${NC}"
echo -e "${YELLOW}═══════════════════════════════════════${NC}"
echo "Standard DQN with target network"
echo ""

run_experiment "base-dqn" \
    "--double-dqn --dueling --n-step 1" \
    "0 1 2"

# Wait a bit before starting next experiment
sleep 5

# ===========================================
# Experiment 3: DQN + Double DQN + Dueling
# ===========================================
echo -e "${YELLOW}═══════════════════════════════════════${NC}"
echo -e "${YELLOW}Experiment 3: Enhanced DQN${NC}"
echo -e "${YELLOW}═══════════════════════════════════════${NC}"
echo "DQN with Double DQN and Dueling architecture"
echo ""

run_experiment "enhanced-dqn" \
    "--double-dqn --dueling --n-step 1" \
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
echo -e "${GREEN}======================================${NC}"
echo -e "${GREEN}All experiments launched!${NC}"
echo -e "${GREEN}======================================${NC}"
echo ""
echo "Monitor progress with:"
echo "  tail -f ${BASE_LOGDIR}/*/0.log"
echo ""
echo "Or for a specific experiment:"
echo "  tail -f ${BASE_LOGDIR}/full-enhanced/0.log"
echo ""
echo "Check GPU usage with:"
echo "  watch -n 1 nvidia-smi"
echo ""
echo "After training completes, generate plots with:"
echo "  python analysis/plot_eval_performance.py --logdir ${BASE_LOGDIR}/full-enhanced"
echo ""
echo "Compare all experiments with:"
echo "  python analysis/aggregate_runs.py --logdir ${BASE_LOGDIR}"
echo ""
echo -e "${YELLOW}Press Ctrl+C at any time to terminate all experiments${NC}"
echo ""

# Wait for all background jobs
wait

echo -e "${GREEN}All experiments completed!${NC}"