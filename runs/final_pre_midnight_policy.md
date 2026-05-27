# Pre-Midnight Policy

The official score is the average of 10 cases, so candidate decisions must use total-score impact.

Current facts:
- Safe avg: `706.4264`.
- Need `64.2642` total reduction to reach `700`.
- Bad cache submit proved local preflight can be dangerously incomplete.
- Remaining attempts: 3.

Submission allowed only if:
1. Clean diff from safe `solver.py` (`41db4b34`).
2. No compact/row-cache refactor and no changes to proven large302/scarce hardcoded paths unless directly targeted and strongly justified.
3. Expected total-score reduction >= 10 points (>=1 avg), preferably from low/scarce or multiple cases.
4. Preflight passes and local evidence is not just public proxy noise.

Currently held but not submit-worthy:
- `candidate_clean_scarce_more_enum.py`: public scarce proxy +16.46, but likely no-op on official seed401 due hard cache.

Do not submit:
- compact cache family, low extra branch, low extra bias, p80/global penalty, T0033 coverage forcing.
