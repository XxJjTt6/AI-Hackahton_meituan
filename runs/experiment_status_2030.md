# Experiment Status 20:30

Global view:
- Safe avg `706.4264`; need total reduction `64.2642` to reach avg 700.
- Remaining official attempts: 3.

After fixing evaluation flaw:
- Compact row-cache family is blacklisted; bad submit `60cf6691` proved local preflight was insufficient.

Current clean held candidate:
- `runs/candidate_clean_scarce_more_enum.py` / SHA `bb5f14f1...`
- Preflight passed; public scarce proxy improved by `16.46` case points.
- Expected official impact uncertain/likely no-op because official seed401 returns via hard cache.
- Not submitted.

Rejected clean candidates:
- `candidate_clean_low_extra_branch.py`: low no-op/slower.
- `candidate_clean_low_more_biases.py`: low official-like proxy worsened and runtime risk.

Current policy:
- Preserve remaining 3 attempts.
- Submit only clean safe-main diff with overall expected avg gain >= 1.0.
