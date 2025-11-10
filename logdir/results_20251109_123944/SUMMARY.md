# Crafter Experiment Results Summary

**Run Date:** Mon Nov 10 14:00:06 UTC 2025
**Total Training Time:** 25h 12m 39s
**Total Training Steps:** 1000000 per agent
**Evaluation Frequency:** Every 50000 steps
**Seeds per Experiment:** 3 (0, 1, 2)
**Execution Mode:** Safe parallel (3 seeds at a time, one experiment at a time)

## Experiments Run

1. **random-baseline** - Random agent (no learning) for comparison
2. **base-dqn** - Standard DQN with target network
3. **enhanced-dqn** - DQN with Double DQN and Dueling
4. **dqn-nstep3** - Enhanced DQN with 3-step returns
5. **dqn-nstep5** - Enhanced DQN with 5-step returns
6. **full-enhanced** - All enhancements including Munchausen-DQN

## Files Generated

- Individual plots: `logdir/<experiment>/plots/`
  - `rewards.png` - Training and evaluation rewards
  - `training_metrics.png` - Loss and Q-values
  - `achievement_spectrum.png` - Achievement success rates
  - `summary.png` - Comprehensive overview

- Comparison: `logdir/results_20251109_123944/comparison_table.txt`

- Raw metrics: `logdir/<experiment>/<seed>/metrics.json`

- Metadata: `logdir/<experiment>/<seed>/metadata.json`

- Training logs: `logdir/<experiment>/<seed>/log.txt`

## Quick Analysis

To view comparison table:
```bash
cat logdir/results_20251109_123944/comparison_table.txt
```

To view individual experiment results:
```bash
ls logdir/*/plots/
```

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

1. Review plots in each experiment's `plots/` directory
2. Check comparison table for best performing agent
3. Select best agent for presentation
4. Create slide deck using generated plots
5. Archive source code: `tar -czf submission.tar.gz *.py analysis/ src/ --exclude=logdir/`

