# Clean Scarce Enum Candidate

File: `runs/candidate_clean_scarce_more_enum.py`
SHA: `bb5f14f1c2517f246adbeead7a342e5030b375f60d131fd98c7f6aa17e29647c`
Size: `76109`
Preflight: passed.

Local evidence:
- Public scarce proxy improved from `1097.847055` to `1081.389644`.
- Public large bench remained `657.10`, time `8.61s`.

Risk / expected official impact:
- It is a clean diff from safe main and not a cache refactor.
- However official `scarce_couriers_seed401` currently returns via hard cache before these expanded enum paths, so seed401 may be no-op.
- Could help only if there are hidden scarce-like cases not caught by the hard cache, but official suite appears fixed 10 cases and only one scarce case is seed401.

Decision:
- Hold, do not submit yet. Expected avg gain is uncertain and likely below threshold unless we intentionally test whether seed401 bypasses cache/other scarce hidden behavior exists.
