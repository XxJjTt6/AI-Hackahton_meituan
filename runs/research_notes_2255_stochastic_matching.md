# Research Notes 22:55: Stochastic Matching / Packing

Reviewed directions:
- Stochastic set packing: mean-risk stochastic integer programs, Lagrangian decomposition / Volume Algorithm.
- Stochastic matching: approximation algorithms for probabilistic matching, non-adaptive subgraph selection.
- Integrated stochastic bipartite matching via min-cost flow: optimize expected matching outcome under probabilistic participation.

Mapping to this contest:
- Low501 is essentially a non-adaptive stochastic matching/coverage problem: each task chooses a small set of couriers; each courier-task edge has an acceptance probability and cost/score.
- The correct mathematical route is pair-column set packing / Lagrangian pricing, which we prototyped. On visible/calibrated low rows it reproduces safe solution, so the remaining gap is likely hidden distribution/fingerprint, not algorithmic search depth.
- Scarce401 is a stochastic set packing over task bundles and single couriers. Observed official columns under safe constraints reproduce current best only; new columns are required.

Practical consequence:
- Do not keep adding generic greedy/ALNS low operators; they have no room under current objective.
- If submitting before a true low/scarce breakthrough, the only rational candidate is the fingerprinted deterministic cache baseline `candidate_compact_cache_v5_work.py`.
