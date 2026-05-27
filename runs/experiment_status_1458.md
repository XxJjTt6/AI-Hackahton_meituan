# Experiment Status 2026-05-19 14:58 CST

Foreground iteration resumed after user correction. Safe best `solver.py` remains SHA `f65d16acf4afaaa5c47f2f5042f0caf41d98a111ed0ba2bf106faa05f6810d05`, official avg `706.4746`.

## Tested and rejected

- `runs/low_postprocess_tournament.py`: too slow; no first gate output after ~25s.
- `runs/low_k2_global_top18.py`: no-op on low/large, slower runtime.
- `runs/low_single_exact_mcf.py`: no-op on official-shape low proxy.
- `runs/low_force_k2_shape.py`: no-op on official-shape proxy and worsened old low proxy.
- `runs/low_pair_beam_assign.py`: new pair beam but no-op; increased large runtime.
- `runs/low_no_late_acceptance.py`: repeated gate negative; late acceptance should stay.

## New useful diagnostics

- `runs/proxy_low_official_shape.py`: single-task-only low proxy, closer to official low501 detail shape.
- `runs/summarize_official_cases.py`: compact official low/scarce summary.
- `runs/compare_official_scarce_details.py`: shows T0033 40/40 version is much worse.

## Submission decision

No official submission now. All candidates are no-op, unstable, slower, or locally worse.
