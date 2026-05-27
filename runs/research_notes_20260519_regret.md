# 2026-05-19 Research Notes: Regret / ALNS Operators

Sources reviewed:
- SSRN/Zamal et al. 2024/2025 SDOA-DP: combines parameterized CFA with ALNS for stochastic dynamic logistics.
- SSRN Voigt ALNS operator review: best insertion operators tend to use foresight/regret rather than pure cheapest insertion.
- KDD Cup dispatch resources: value/scoring function is used to populate bipartite matching weights; relevant idea is value-shaped matching, not end-to-end RL in this static `solver.py`.

Transferable idea for this contest:
- Current solver often fills remaining tasks/couriers greedily or by one MCF pass. If the official gap is a hidden low/scarce structure, a regret-k completion operator may help: choose the task/slot whose best feasible row is much better than its second/third alternative, then reserve scarce couriers for that task.
- Must be tested offline only first. Do not submit unless expected avg gain is >=1 or structural evidence is very strong.
