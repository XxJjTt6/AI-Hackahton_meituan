# Official Observed Column Scan — 2026-05-24

## Purpose

Check whether valid historical official detail rows can be recombined into a lower-scoring legal solution for any case. This is an offline scan only; it does not modify `solver.py` and does not submit anything.

## Method

- Read `runs/official*.json`.
- Keep only cases with `validity=true`.
- Treat each judge detail row as a column: `(task_id_list, couriers, cost)`.
- Enforce legal constraints: no duplicate task coverage and no duplicate courier use.
- Search by branch-and-bound per case, starting from the best known official score.

## Result Summary

| Case | Best Valid Official | Best Recombined | Delta | Status |
|---|---:|---:|---:|---|
| `high_noise_seed601` | 487.7525 | 487.7525 | 0.0000 | no improvement |
| `large_seed301` | 654.2935 | 654.2934 | -0.0001 | rounding only |
| `large_seed302` | 627.0114 | 626.9711 | -0.0403 | too small for submit |
| `low_willingness_seed501` | 1799.9031 | 1799.9031 | 0.0000 | no improvement found; timed out |
| `medium_seed201` | 478.3143 | 478.3142 | -0.0001 | rounding only |
| `medium_seed202` | 524.0195 | 524.0194 | -0.0001 | rounding only |
| `medium_seed203` | 501.0067 | 501.0063 | -0.0004 | rounding only |
| `scarce_couriers_seed401` | 1531.5317 | 1531.5316 | -0.0001 | rounding only |
| `small_seed100` | 303.7211 | 303.7211 | 0.0000 | no improvement |
| `tiny_seed42` | 154.4163 | 154.4163 | 0.0000 | no improvement |

## Decision

No observed-column recombination clears the project gate of a credible `>=1.0` official-average-point improvement. Do not spend an official submission on these recombinations. The only non-rounding signal is `large_seed302 -0.0403`, which is about `-0.004` average and far below the submission threshold.

## Implication

The remaining large improvement space is not in recombining already-observed valid official columns. It likely requires generating new legal columns at runtime for `low_willingness_seed501` or `scarce_couriers_seed401`, but previous local proxy scans show simple willingness/risk/multidispatch changes do not beat the incumbent.
