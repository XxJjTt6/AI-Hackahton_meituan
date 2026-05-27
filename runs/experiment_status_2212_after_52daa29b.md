# Status after 52daa29b official failure

Submitted `runs/candidate_minify_high_compact.py` by user request.

Official result:
- avg `712.2072` (worse than safe `706.4264`)
- high stayed `490.0466`; compact patch did not trigger
- scarce regressed `1531.5317 -> 1589.3393`
- remaining attempts: `2`

Decision:
- Blacklist sha prefix `52daa29b`.
- Do not submit high-only/layout micro patches again.
- Continue only with direct low/scarce evidence.
