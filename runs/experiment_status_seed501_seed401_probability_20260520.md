# Seed501/Seed401 Probability-Gain Iteration

Key quantitative insight:
- Rank 1 gap from `706.197` to `699.367` is about `68.3` total score.
- Current low501 avg p_complete ≈ `0.4729`; scarce401 avg p_complete ≈ `0.8064`.
- A uniform `+0.02` p_complete improvement on low/scarce has enough magnitude, but simple bias does not find it.

New tests:
- Official visible-column exact set partition: low/scarce observed columns cannot beat current.
- Low p/cost bias: recursive bias too slow; pool bias worsens calibrated/proxy low.
- Per-task Pareto: many local 3-courier columns dominate, but global 60-courier budget blocks naive use.
- Variable-K beam: small beam infeasible; large beam too slow. Needs a better exact allocator if revisited.

Decision:
- No submit. Current best `solver.py` remains SHA `70222083...`.
- Next plausible breakthrough is exact/efficient variable-K pricing or new hidden-case column generation, not scalar bias, T0033, K2 forcing, or historical recombination.
