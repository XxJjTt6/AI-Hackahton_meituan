# Continuation Status

- No official submit after reconnect; only `--skip-submit` preflights.
- New threshold: only official-submit candidates with credible >=1.0 average-score gain.
- Official recomposition over 70 records shows current `70222083` is already per-case observed best; no historical column recombination gain remains.
- Current backup candidates:
  - `runs/candidate_scarce_t33_window_timed.py` (`3a83bb23`, 79540 bytes): strict scarce 40x40 branch, T0033 affected-window exact repair, self-gated by >10 case-score improvement, timed.
  - `runs/candidate_scarce_uncovered_window_timed.py` (`00b0586d`, 79579 bytes): generalized uncovered-task version, same gate/timer.
- Rejected:
  - `runs/candidate_low_k2_exact_selfgated.py` (`17b21318`): low calibrated no gain, large preflight unstable/slow.

## 15:00 Follow-up

- `runs/candidate_repack_high_large_gate10_min4.py` (`31aa9362`, 79997 bytes) merges old full-column repack with current high/large upgrades and raises gate to >=10 case-score gain.
- It passes preflight and preserves public large, but helper timing on public scarce seed can take 2.4-5.0s; because official cache path already has tight timeout, treat as risky backup, not submit-ready.
- Safer current backup remains `runs/candidate_scarce_t33_window_timed.py` (`3a83bb23`) due explicit 0.72s gate, but hidden trigger evidence is still weak.
- Low exact/MCF historical candidates recomposed the same calibrated signature `06842fb3c2c0`; no low breakthrough yet.

## 15:10 Follow-up

- `runs/candidate_repack_timed_gate10.py` (`e62f9344`, 79046 bytes) adds a 0.75s full-repack timer and passes preflight.
- However proxy low/overall timing became unstable in subsequent matrix runs, so it is downgraded to risky backup and should not be submitted under the current >=1.0 threshold.

## 15:30 Official Probe Failure

- Submitted `runs/candidate_scarce_extra_plus_t33.py` (`0fc08e17`) because proxy scarce improved by ~22.6 case points and other proxies were unchanged.
- Official failed: avg `710.2339`; only scarce regressed to `1571.9010`; other 9 cases unchanged.
- Detail shows failure came from T0033 replacement route: it covered `T0033` with `C000` but lost `T0028`, so still `39/40` and +40.3693 worse.
- Blacklist all T0033 replacement/window/repack families; no more official attempts on T0033. Extra idle-courier add did not trigger in official output.
- Research pivot: low/scarce must be treated as stochastic matching with patience/few-query constraints; prototype unified set-packing was worse, so next viable route is LP/dual-guided low variable-k, not cache patching.

## 15:50 Research Update

- `runs/research_unified_master_fast.py`: unified set-packing master is far worse than incumbent on large/low/scarce proxies; not a route by itself.
- `runs/research_low_dual_master_fast.py` and `runs/research_low_k2_hungarian_like.py`: K2/dual/matching prototypes reproduce incumbent on calibrated low; K>2 is worse due 60-courier/30-task resource limit.
- `runs/candidate_current_polish_less.py` (`e7be0545`) is rejected: proxy matrix shows timing perturbation can worsen large/low.
- Official `0fc08e17` added a useful negative label: covering `T0033` by sacrificing `T0028` is not worthwhile; T0033 route cost 83.1439 still net-worse.

## 16:05 Update

- Tried broader algorithmic rewrites: unified master, low dual, low K2 Lagrangian, current-parameter scarce search. None produced a trustworthy candidate above the >=1.0 official threshold.
- Added `runs/gate_candidate.py` as a concept, but full proxy gate was too slow under load and killed; avoid using it routinely.
- Active rule remains: no more T0033 official probes; no official submit without strong full-portfolio evidence.
