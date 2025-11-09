#!/bin/bash
# End-to-end pipeline test
# Quick test run to validate everything works before long experiments

set -e  # Exit on any error

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${GREEN}======================================${NC}"
echo -e "${GREEN}End-to-End Pipeline Test${NC}"
echo -e "${GREEN}======================================${NC}"
echo ""

# Test configuration
TEST_LOGDIR="logdir_test"
TEST_STEPS=5000
TEST_EVAL_INTERVAL=2500

# Clean test directory
if [ -d "$TEST_LOGDIR" ]; then
    echo -e "${YELLOW}Cleaning old test directory...${NC}"
    rm -rf "$TEST_LOGDIR"
fi

echo -e "${BLUE}Test Configuration:${NC}"
echo "  Steps: $TEST_STEPS"
echo "  Eval Interval: $TEST_EVAL_INTERVAL"
echo "  Test dir: $TEST_LOGDIR"
echo ""

# ===========================================
# Test 1: Basic Training Run
# ===========================================
echo -e "${YELLOW}[1/6] Testing basic training run...${NC}"

python train.py \
    --logdir "$TEST_LOGDIR/test-run/0" \
    --seed 42 \
    --steps $TEST_STEPS \
    --eval-interval $TEST_EVAL_INTERVAL \
    --eval-episodes 5 \
    --double-dqn \
    --dueling \
    --n-step 3

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Training completed successfully${NC}"
else
    echo -e "${RED}✗ Training failed!${NC}"
    exit 1
fi
echo ""

# ===========================================
# Test 2: Verify File Generation
# ===========================================
echo -e "${YELLOW}[2/6] Verifying file generation...${NC}"

TEST_DIR="$TEST_LOGDIR/test-run/0"
REQUIRED_FILES=(
    "metadata.json"
    "metrics.json"
    "log.txt"
    "final_model.pt"
)

ALL_FILES_OK=true
for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "$TEST_DIR/$file" ]; then
        size=$(stat -f%z "$TEST_DIR/$file" 2>/dev/null || stat -c%s "$TEST_DIR/$file" 2>/dev/null)
        echo -e "${GREEN}✓${NC} $file (${size} bytes)"
    else
        echo -e "${RED}✗${NC} $file (missing!)"
        ALL_FILES_OK=false
    fi
done

if [ "$ALL_FILES_OK" = false ]; then
    echo -e "${RED}Some required files are missing!${NC}"
    exit 1
fi
echo ""

# ===========================================
# Test 3: Validate JSON Format
# ===========================================
echo -e "${YELLOW}[3/6] Validating JSON file formats...${NC}"

python - <<EOF
import json
import sys

test_dir = "$TEST_DIR"

# Test metadata.json
try:
    with open(f'{test_dir}/metadata.json') as f:
        metadata = json.load(f)

    # Check required fields
    required_fields = ['timestamp_start', 'timestamp_end', 'duration', 'git', 'system', 'arguments']
    missing = [f for f in required_fields if f not in metadata]

    if missing:
        print(f"✗ metadata.json missing fields: {missing}")
        sys.exit(1)

    print(f"✓ metadata.json valid")
    print(f"  Duration: {metadata['duration']['human_readable']}")
    print(f"  Commit: {metadata['git']['commit_short']}")
    print(f"  GPU: {metadata['gpu'][0]['name'] if metadata['gpu'] else 'N/A'}")

except Exception as e:
    print(f"✗ metadata.json validation failed: {e}")
    sys.exit(1)

# Test metrics.json
try:
    with open(f'{test_dir}/metrics.json') as f:
        metrics = json.load(f)

    # Check structure
    if 'metrics' not in metrics or 'steps' not in metrics:
        print("✗ metrics.json missing 'metrics' or 'steps' keys")
        sys.exit(1)

    # Check for required metrics
    required_metrics = ['eval/mean_reward', 'train/loss', 'train/q_values_mean']
    found_metrics = [m for m in required_metrics if m in metrics['metrics']]

    print(f"✓ metrics.json valid")
    print(f"  Metrics tracked: {len(metrics['metrics'])}")
    print(f"  Required metrics found: {len(found_metrics)}/{len(required_metrics)}")

    # Show sample data
    if 'eval/mean_reward' in metrics['metrics']:
        rewards = metrics['metrics']['eval/mean_reward']
        print(f"  Eval rewards: {rewards}")

except Exception as e:
    print(f"✗ metrics.json validation failed: {e}")
    sys.exit(1)

EOF

if [ $? -ne 0 ]; then
    echo -e "${RED}JSON validation failed!${NC}"
    exit 1
fi
echo ""

# ===========================================
# Test 4: Validate log.txt Content
# ===========================================
echo -e "${YELLOW}[4/6] Validating log.txt content...${NC}"

LOG_FILE="$TEST_DIR/log.txt"

# Check if log has content
if [ ! -s "$LOG_FILE" ]; then
    echo -e "${RED}✗ log.txt is empty!${NC}"
    exit 1
fi

# Check for expected content
LOG_CHECKS=(
    "Training DQN agent on Crafter"
    "Experiment: training_run"
    "Git Info"
    "System Info"
    "Eval - Mean Reward"
    "TRAINING COMPLETE"
)

MISSING_CONTENT=false
for check in "${LOG_CHECKS[@]}"; do
    if grep -q "$check" "$LOG_FILE"; then
        echo -e "${GREEN}✓${NC} Found: \"$check\""
    else
        echo -e "${RED}✗${NC} Missing: \"$check\""
        MISSING_CONTENT=true
    fi
done

if [ "$MISSING_CONTENT" = true ]; then
    echo -e "${RED}log.txt is missing expected content!${NC}"
    exit 1
fi

# Show log stats
LINES=$(wc -l < "$LOG_FILE")
echo -e "${GREEN}✓ log.txt has $LINES lines${NC}"
echo ""

# ===========================================
# Test 5: Test Plotting
# ===========================================
echo -e "${YELLOW}[5/6] Testing plot generation...${NC}"

python analysis/plot_eval_performance.py \
    --logdir "$TEST_LOGDIR/test-run" \
    --save-dir "$TEST_LOGDIR/test-run/plots" \
    2>&1 | tee "$TEST_LOGDIR/plot_test.log"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Plotting script executed successfully${NC}"
else
    echo -e "${RED}✗ Plotting script failed!${NC}"
    cat "$TEST_LOGDIR/plot_test.log"
    exit 1
fi

# Check if plots were created
PLOT_DIR="$TEST_LOGDIR/test-run/plots"
EXPECTED_PLOTS=(
    "rewards.png"
    "training_metrics.png"
    "summary.png"
)

PLOTS_OK=true
for plot in "${EXPECTED_PLOTS[@]}"; do
    if [ -f "$PLOT_DIR/$plot" ]; then
        echo -e "${GREEN}✓${NC} Generated: $plot"
    else
        echo -e "${RED}✗${NC} Missing: $plot"
        PLOTS_OK=false
    fi
done

if [ "$PLOTS_OK" = false ]; then
    echo -e "${RED}Some plots were not generated!${NC}"
    exit 1
fi
echo ""

# ===========================================
# Test 6: Run Two More Seeds for Aggregation Test
# ===========================================
echo -e "${YELLOW}[6/6] Testing multi-seed aggregation...${NC}"

echo "Running seed 1..."
python train.py \
    --logdir "$TEST_LOGDIR/test-run/1" \
    --seed 43 \
    --steps $TEST_STEPS \
    --eval-interval $TEST_EVAL_INTERVAL \
    --eval-episodes 5 \
    --double-dqn \
    --dueling \
    --n-step 3 \
    > "$TEST_LOGDIR/seed1.log" 2>&1

echo "Running seed 2..."
python train.py \
    --logdir "$TEST_LOGDIR/test-run/2" \
    --seed 44 \
    --steps $TEST_STEPS \
    --eval-interval $TEST_EVAL_INTERVAL \
    --eval-episodes 5 \
    --double-dqn \
    --dueling \
    --n-step 3 \
    > "$TEST_LOGDIR/seed2.log" 2>&1

echo "Testing aggregation..."
python analysis/plot_eval_performance.py \
    --logdir "$TEST_LOGDIR/test-run" \
    --save-dir "$TEST_LOGDIR/test-run/plots_aggregated" \
    2>&1 | tee "$TEST_LOGDIR/aggregate_test.log"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Multi-seed aggregation successful${NC}"

    # Verify it found all seeds
    FOUND_SEEDS=$(grep -o "Found [0-9]* run" "$TEST_LOGDIR/aggregate_test.log" | grep -o "[0-9]*")
    if [ "$FOUND_SEEDS" = "3" ]; then
        echo -e "${GREEN}✓ Found all 3 seeds${NC}"
    else
        echo -e "${YELLOW}⚠ Found $FOUND_SEEDS seeds (expected 3)${NC}"
    fi
else
    echo -e "${RED}✗ Aggregation failed!${NC}"
    exit 1
fi
echo ""

# ===========================================
# Summary
# ===========================================
echo -e "${GREEN}======================================${NC}"
echo -e "${GREEN}ALL TESTS PASSED! ✓${NC}"
echo -e "${GREEN}======================================${NC}"
echo ""
echo -e "${BLUE}Test Results:${NC}"
echo "  ✓ Training completes successfully"
echo "  ✓ All required files generated"
echo "  ✓ JSON files valid and complete"
echo "  ✓ log.txt has proper content"
echo "  ✓ Plots generated successfully"
echo "  ✓ Multi-seed aggregation works"
echo ""
echo -e "${BLUE}Generated Test Data:${NC}"
echo "  Location: $TEST_LOGDIR/"
echo "  Logs: $TEST_DIR/log.txt"
echo "  Metadata: $TEST_DIR/metadata.json"
echo "  Metrics: $TEST_DIR/metrics.json"
echo "  Plots: $PLOT_DIR/"
echo ""
echo -e "${GREEN}Your pipeline is ready for the long run!${NC}"
echo ""
echo -e "${YELLOW}To clean up test data:${NC}"
echo "  rm -rf $TEST_LOGDIR"
echo ""
