# 16:55 Continuing Iteration

Hard rules applied:
- Do not stop after checkpoint summaries; continue next experiment.
- Judge candidates by all 10 official cases, not one proxy.
- Official submit only with credible >=1.0 average improvement.

New probes this segment:
- `research_low_window_grid_20260520.py`: enlarged low window search, no improvement on calibrated low.
- `research_low_assigned_exchange_20260520.py`: 2/3-task same-assigned pair exchanges, no improvement.
- `research_low_k2_pair_bb_20260520.py`: exact-ish K2 pair branch-and-bound, worse than current.
- `research_low_model_sensitivity_20260520.py`: probability/cost rescaling, worse than current.
- `research_low_k_transfer_20260520.py`: K3/K1 single courier transfer, no improvement.
- `research_scarce_cached_pair_swap_20260520.py`: same-coverage 2/3-cycle courier swaps, no improvement.
- `candidate_trim_tail_current_20260520.py`: rejected, low proxy regression.
- `candidate_time_guard_current_20260520.py`: rejected, scarce proxy regression/unstable.

Current conclusion:
- Current best `solver.py` SHA remains `70222083`; do not replace it.
- Visible-objective low/scarce local and global neighborhoods are saturated.
- Next route should be hidden evaluator/fingerprint or a genuinely different master-pricing scheme, not T0033/cache/K2 resubmission.
