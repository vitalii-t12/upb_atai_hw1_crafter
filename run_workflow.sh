# 1. Clean old data
rm -rf logdir/*
mkdir -p logs

# 2. Start tmux session
tmux new -s crafter_experiments

# 3. Run experiments with logging
./run_experiment.sh 2>&1 | tee logs/run_$(date +%Y%m%d_%H%M%S).log

# 4. Detach safely (Ctrl+B, D)
# You can now disconnect from SSH

# 5. Hours later, reconnect
#ssh your_server
#tmux attach -t crafter_experiments
#
## 6. Check results when done
#cat logdir/results_*/SUMMARY.md