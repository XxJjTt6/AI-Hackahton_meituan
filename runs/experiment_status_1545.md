# Experiment Status 2026-05-19 15:45 CST

Official probes since 15:25:
- `7bc511c6` low official pair 2-opt: exact no-op.
- `f4ade6b4` low official worst10 3-opt: exact no-op.
- `0c8d5ace` low official one-courier K-mix move: exact no-op.
- `95581ea7` low official deterministic random larger-neighborhood search: exact no-op.

Latest remaining official attempts: `9/20`.

Updated conclusion:
- Hidden low501 official assignment is saturated across the tested local-search neighborhoods.
- Hidden scarce401 exact cache is saturated across T0033 single/triple/superset and same-key extra routes.
- Stop submitting cache-local-search variants; need a fundamentally different generator or save attempts for later.
