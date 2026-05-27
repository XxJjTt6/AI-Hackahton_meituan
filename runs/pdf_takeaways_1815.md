# PDF Takeaways Applied to AutoSolver

Paper idea: maximize profit with hard/quantile time feasibility filter, then value-based action selection.

Mapping to this contest:
- `willingness` is closer to success probability than ETA feasibility.
- `total_score` is cost/score conditional on success.
- For low501, all official good outputs use every courier exactly once in 30 K=2 groups; filtering low willingness would reduce coverage or force worse replacements.
- For scarce401, there are too few couriers; filtering can only drop tasks, and current best already deliberately drops T0033.

Conclusion:
- Direct action filtering is unlikely to yield 700-level improvement without a better hidden evaluator.
- The transferable part is value-aware matching (opportunity cost), which needs an exact low K=2 assignment solver to be useful.
