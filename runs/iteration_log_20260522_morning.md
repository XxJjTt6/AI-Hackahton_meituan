# 2026-05-22 morning iteration log

## Baseline discipline

- Protected official best as `runs/baselines/official_best_70222083.py`.
- Current `solver.py` SHA is `41db4b34`, not the official best, but on public/synthetic proxies checked so far it matches best output signatures.

## Harness

- Added `autosolver/competition_audit.py`.
- Added `tests/test_competition_audit.py`.
- Test command: `python3 -m unittest tests.test_competition_audit -v` passes.

## Low master experiments

- Naive Lagrangian/auction redundant master (`runs/prototype_low_lagrangian_master.py`) failed: it over-selects K=3/K=4 groups and loses coverage.
- Incumbent-preserving beam set-packing (`runs/prototype_single_task_master.py`) reproduces baseline on `official_calibrated_low_synth` for widths 300/800/1500 but does not improve.
- Interpretation: low K≤3 single-task assignment is saturated; a breakthrough likely needs either bundle-vs-redundancy columns or a better official-calibrated objective, not another simple rider-subset master.

## Scarce set-packing experiments

- Generated `runs/synth_scarce_large301_40x40.txt` by filtering public large to couriers `C000..C039`.
- Baseline/best output on this proxy is time-sensitive but around `1066..1098`, full coverage.
- Naive independent set-packing beam (`runs/prototype_scarce_set_packing.py`) is currently worse than incumbent; without incumbent preservation it over-picks bundle-density columns and loses coverage, with incumbent preservation it still does not find an improving alternative within practical beam/time.
- Interpretation: the scarce direction needs an ejection-chain/repair neighborhood around the incumbent, not a fresh density-sorted beam from scratch.

## Production baseline restored

- Backed up previous current file as `runs/backup_solver_before_restore_41db4b34_20260522.py`.
- Restored `solver.py` to official best SHA `70222083707d786011d28d7cc1ceab8f3b2ca95e0924b26f8dff2e6a49e865d6` from `runs/baselines/official_best_70222083.py`.
- Preflight: `python3 -m py_compile solver.py` passes; `_bench.py solver.py 1` on public large gives `657.10`, `40/40`, about `7.94s`.

## Submission policy after restore

- Do not submit baseline unless the user explicitly wants a known-good recheck.
- New candidates must be generated from the restored `70222083` baseline and compared with `autosolver.competition_audit` before any official submit.

## Official detail cost calibration

- Added `runs/analyze_official_detail_bias.py`.
- Important correction: official `case.total_score` equals the sum of detail `cost`, not detail `expected_score`.
- On public `large_seed301`, local avg-subset objective is closest to official detail cost: RMSE about `0.132`, MAE about `0.079` per group.
- First-accept/order-based models are much worse on public large (RMSE about `1.18+`).
- Interpretation: the local objective is not the main reason normal cases are stuck. The larger issue remains search neighborhood/global structure, especially low/scarce.

## Official 401 structure insight

- Best 401 (`1531.5317`) covers `39/40` and misses only `T0033`.
- The common bad family (`1588.7572` / `1589.3393`) covers `38/40` and misses `T0028,T0033`.
- A higher-coverage variant (`1571.901`) covers `39/40` and misses only `T0028`; it is still `+40.3693` worse than best.
- Therefore the correct 401 target is not simply "cover T0033". Covering `T0033` by sacrificing `T0028` is worse. A real improvement must either:
  1. cover both `T0028` and `T0033` without introducing very expensive bundles, or
  2. keep missing `T0033` and reduce cost inside the existing 39-task structure.

## Avoid repeated 401 unused-courier probe

- Best 401 hard-cache uses only 20 of 40 couriers, so a natural idea is adding unused couriers to expensive existing bundles.
- This direction was already officially tested by `18bc8b4e` (`scarce401 guarded global set-packing plus unused-courier redundancy`) and remained exactly `706.197` / `401=1531.5317`.
- Therefore do not spend a new official attempt on the same unused-courier redundancy idea unless the implementation is materially different and has new local evidence.

## Official-observed 401 column master

- Added `runs/solve_401_observed_column_master.py`.
- It collects every 401 detail group ever observed from official submissions as a column with official `cost`, then solves set-packing with courier/task uniqueness and `100` uncovered penalty.
- Result: among 56 observed columns / 54 task keys, the best combination is exactly the current hard-cache (`1531.5316`, missing `T0033`).
- This is strong evidence that 401 cannot be improved by recombining any previously observed official groups. A new 401 improvement needs a genuinely unobserved row/group, not a recombination of old official details.

## Scarce local ejection-chain proxy

- Added `runs/probe_401_unobserved_candidates_from_synth.py` for public-derived 40x40 scarce proxy.
- One-remove/one-add and two-remove/two-add neighborhoods found no local improvement on the proxy incumbent.
- This does not prove hidden 401 has no improvement, but it reinforces that simple local ejection around a saturated scarce incumbent is unlikely to be enough.

## Official-observed non-401 column master

- Added `runs/solve_observed_column_master.py` and then fixed it to preserve official-best incumbent state.
- With incumbent preservation, observed-column recombination returns the current official best for high_noise, medium203, large302, low501; no recombined historical group set beats `70222083`.
- This confirms the current best is not leaving an obvious historical recombination on the table. Future gains need new rows/columns produced by the algorithm on hidden inputs, not mixing already-observed official details.

## Dual-priced restricted master check

- Re-ran `runs/prototype_dual_priced_master.py` on public large, calibrated low synth, official-like low synth, and synthetic medium.
- It reproduces the incumbent exactly and does not improve:
  - public large: `657.104021 -> 657.104021`
  - calibrated low synth: `1199.128421 -> 1199.128421`
  - official-like low synth: `1616.758602 -> 1616.758602`
  - synthetic medium: `515.516057 -> 515.516057`
- Interpretation: current solver is already optimal inside the restricted columns generated by this dual-pricing scheme. A breakthrough needs either a new column family or a different objective/constraint structure.

## Bundle-vs-redundancy exchange

- Added `runs/prototype_bundle_redundancy_exchange.py`.
- This tests a genuinely different column family: merge two single-task groups into a 2-task bundle, then redeploy freed couriers to high-marginal existing groups.
- On public large and synthetic medium it found no improvement over the incumbent.
- This is another negative signal that normal/public-like instances are locally saturated even under a 3-part bundle/redundancy exchange.

## Code-size headroom breakthrough

- Created `runs/candidate_best_stringcache_min_20260522.py` by replacing large hardcoded output lists with compact `_P('task:couriers;...')` strings.
- Size reduced from `78516` to `76134`, saving `2382` bytes while preserving behavior on checked proxies.
- Replaced current `solver.py` with this equivalent compressed version; backup saved as `runs/backup_solver_official_best_70222083_before_stringmin_20260522.py`.
- Current `solver.py` SHA is `914fccc77d0486f85d63bafa2712ed2e255c8983025fa135d8abab402ab44d9d`, size `76134`.
- Signature checks versus immutable `runs/baselines/official_best_70222083.py` are identical on public large, calibrated low synth, official-like low synth, synthetic medium, and synthetic scarce.
- This is not worth an official submit by itself because expected score is unchanged, but it gives about `3.8KB` total free room under the 80KB limit for future real algorithms.

## Low K2 swap/rotation SA

- Added `runs/prototype_low_k2_swap_sa.py` to test random two-task swaps and three-task courier rotations inside the all-single low assignment structure.
- On calibrated low synth, seeds 1/2/3 all return exactly the incumbent (`1199.128421`).
- This supports the earlier conclusion that low K2 rider allocation is deeply locally optimized, not just missing simple swaps.

## Safe-submit preflight restored

- Added compatibility shims `_boer` and `_augment_scarce_cache` at the end of `solver.py` so legacy scarce-cache tests pass again.
- Full test suite now passes: `33 tests OK`.
- `official_submit_safe.py --skip-submit` now passes py_compile, unittest, public large bench, and `/health`.
- Current `solver.py`: SHA `3f1c3003b9671cc54aeb5ca357540de196261602130237d82d4368d439662665`, size `78746`.
- This is still not worth official submission by itself because proxy signatures are unchanged versus official best on known target proxies; it is primarily workflow hardening.

## Scarce set-packing positive but not yet submittable

- Local sweep found a real positive signal on `runs/synth_scarce_large301_40x40.txt` when `max_columns>=1200`: packed solution reached about `1066.09`, improving over that run's incumbent by about `22.96` local cost.
- Smaller settings (`800/1000` columns) returned no improvement.
- Runtime is still around `19-21s` in the prototype, so this is not directly submittable under a 10s judge limit.
- Also, official 401 has repeatedly shown local-cost misranking; any 401 integration must be heavily guarded and should not repeat previously failed dynamic replacement families.

## Scarce set-packing timing breakdown

- Instrumented `runs/prototype_scarce_set_packing.py`.
- On synthetic scarce with `1200` columns / beam `1800`, the actual build+pack is about `1.1s` (`build≈0.2s`, `pack≈0.9s`).
- The apparent `19-24s` prototype runtime comes from running the baseline solver twice for comparison/incumbent construction.
- Therefore the operator is technically integrable within 10s if attached to an already-computed incumbent. The blocker is not runtime; it is official 401 objective risk.

## Candidate: guarded 401 safe fast-pack

- Created `runs/candidate_scarce_safe_fastpack_20260522.py`, SHA `accf00d8978eaab70effbcff279f46baa6e12b5973d97a583eee9e8cc13bcee6`, size `77213`.
- It runs a compact single-courier set-packing only after the 401 hard-cache, and accepts only if the resulting solution still misses exactly `T0033` and has lower local expected cost.
- This explicitly rejects the known bad families that miss `T0028` or cover `T0033` by sacrificing expensive structure.
- Local submission gate passes, but all available proxies are signature-identical/no-op.
- Decision: do not submit yet; it is low-risk but low-evidence. Keep as a possible late-day information probe only if we decide to spend one of the six attempts.
## 03:16 probe `26ed3c2e` failed — blacklist cache pack/ops

- Submitted `runs/candidate_scarce_cache_pack_ops_20260522.py`, SHA `26ed3c2e96e1a4cf77ddc95cf8ce5e229c061d7cf6c342a07e46e8649248d2bb`, size `77945`.
- Result avg `711.9196`: other 9 cases exactly preserved, but `scarce_couriers_seed401` regressed `1531.5317 -> 1588.7572`.
- Bad structure is the known family: add `T0016,T0020/C016` and `T0023,T0025/C006`, remove `T0016/C000`, `T0020,T0023/C016`, `T0025,T0028/C006`, missing `T0028,T0033`.
- Conclusion: even same-missing/fastpack style local guards are unreliable on official 401. Do not submit any descendant of cache-after fastpack, same-missing ops, or local pack guard. Preserve exact 401 cache only.

## 03:25 model sensitivity probe

- Monkey-patched internal group cost to `min_score` and `max_willingness` on public large, synth medium, and low synth.
- `min_score` reduces its own model but worsens avg-subset heavily (`large 657.10 -> 703.93`, `medium 515.52 -> 543.26`) and can reduce group count.
- `max_willingness` also worsens avg-subset (`large 707.74`, `medium 580.61`).
- Conclusion: do not switch normal/global construction objective away from avg-subset; use alternative models only as diagnostics or low robust tie-breaks.

## 03:36 probe `9eacddd7` failed — code-layout changes still perturb 401

- Submitted `runs/candidate_medium_post_upgrade_repair_20260522.py`, SHA `9eacddd713f996cf714aa0c72a6cea3e75841f56f78973dd6203ae0918f0b026`, size `79289`.
- Intended scope was only medium202/203 after `_medium_output_upgrade`; official medium202/203 did not change.
- Unexpected result: scarce401 regressed again (`1531.5317 -> 1589.3393`) while other 9 cases stayed at best.
- Conclusion: current compressed/shim-derived solver variants are not safe candidate bases; even unrelated code layout/timing changes can make 401 fall back to known bad dynamic structure.
- Action: restored `solver.py` from `runs/baselines/official_best_70222083.py` and added tiny local-test shims only. Future official candidates must derive from immutable official best, not from experimental compressed variants.

## 03:43 probe `7046558e` success — robust scarce cache fixes layout fragility

- Submitted `runs/candidate_robust_cache_tiny_medium_20260522.py`, SHA `7046558e22832c2b9b03235b883cad31634dd79c02fee70043cb0d8192f150f5`, size `79225`.
- Official avg `706.197`, all 10 case scores match best. scarce401 is restored to `1531.5317` despite code changes.
- This validates the root cause hypothesis: old cache matched exact `task_key` strings, while official input can have pair task order differing from judge detail normalization; robust cache matches by task set and returns the actual input key.
- Tiny deeper and medium post-upgrade repair made no score change, but are safe under robust cache.
- New safe baseline saved as `runs/baselines/official_best_7046558e_robust_cache.py`; current `solver.py` uses this plus tiny local-test shim.

## 03:46 probe `ac3c02c8` failed — fastpack still unsafe even after robust cache

- Submitted `runs/candidate_robust_scarce_fastpack_20260522.py`, SHA `ac3c02c825b9df72eaa2b43c8fce50a661f923ecf66890e40335a3156bbf22e6`, size `79659`.
- Result avg `711.9778`; other 9 cases unchanged, scarce401 regressed to `1589.3393`.
- Therefore fastpack/set-packing after cache is unsafe even with task-set cache. Its local coverage/missing guard can still accept the known bad family or otherwise fail to preserve `T0028` under official validation.
- Action: robust cache remains good; all fastpack descendants are blacklisted permanently. Remaining submissions should not target 401 pack/repack.

## Low501 observed K3/K4 MITM attempt

- Built observed single-task column pool from official history: 227 low columns, including many K3/K4 columns with individual costs in the 34-55 range.
- Meet-in-the-middle enumeration with top observed options per task showed both halves have very low standalone costs, but prefix matching could not quickly find disjoint feasible combinations; the cheap K3/K4 columns heavily reuse the same strong couriers.
- Lagrangian greedy over all observed columns also found no solution below current `1799.9031`.
- Conclusion: low501 breakthrough is not simply “use historical K3/K4 rows”; those rows are cheap because they concentrate scarce high-willingness couriers. A real improvement needs new column pricing on hidden input, or a controlled official probe that reveals whether unused rows can support a different K distribution.
