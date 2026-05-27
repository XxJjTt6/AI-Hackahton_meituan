# Business Objective Reframe 22:15

User correction: optimize whole 10-case portfolio, not one case. A local improvement can regress another case, as `52daa29b` did.

Business interpretation:
- Each assignment group has expected business cost: `100 * P(fail all) + P(success) * expected_score`.
- Enterprise objective is portfolio-level expected loss minimization under time and validity constraints.
- The correct solver should maximize expected marginal profit per courier/task while controlling downside risk and runtime stability.

Implications for next candidates:
1. No more high-only/layout micro submissions.
2. Any candidate must explicitly preserve scarce hard-cache and large302 paths.
3. Optimize by scenario portfolio:
   - low: 30 tasks / 60 couriers, optimal structure is stable two-courier dispatch; search is saturated under current objective.
   - scarce: 40 tasks / 40 couriers, business trade-off is not full coverage at any cost; current 39/40 is better than known 40/40.
   - large/medium: avoid runtime-induced bad signatures, because business SLA timeout/regression outweighs micro gains.
4. Submit only with whole-portfolio evidence: expected total score reduction >= 10 and no known case regression.

Remaining attempts: 2.
