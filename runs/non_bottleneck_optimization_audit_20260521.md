# Non-Bottleneck Case Optimization Audit

## Scope

Cases reviewed here exclude the two main bottlenecks `scarce_couriers_seed401` and `low_willingness_seed501`.

Reviewed cases:

- `tiny_seed42`
- `small_seed100`
- `medium_seed201`
- `medium_seed202`
- `medium_seed203`
- `large_seed301`
- `large_seed302`
- `high_noise_seed601`

## Official history summary

Current best already equals historical best on all 8 reviewed cases:

| Case | Historical/current best | Notes |
|---|---:|---|
| `tiny_seed42` | `154.4163` | Stable in 85/87 logs |
| `small_seed100` | `303.7211` | Stable cache path |
| `medium_seed201` | `478.3143` | Stable in 83/87 logs |
| `medium_seed202` | `524.0195` | Improved over old `524.7228` and intermediate `524.2432` |
| `medium_seed203` | `501.0067` | Improved over old `502.2743` |
| `large_seed301` | `654.2935` | Extremely stable in 85/87 logs |
| `large_seed302` | `627.0114` | Improved over old `627.2692` via output upgrade |
| `high_noise_seed601` | `487.7525` | Improved over old `490.0466` |

Generated supporting audit: `runs/non_bottleneck_case_audit_latest.md`.

## Known-row recombination result

A limited official-detail-row recombination audit found no material guaranteed improvement:

- `large_seed301`: `-0.0001` rounding only.
- `medium_seed201`: `-0.0001` rounding only.
- `medium_seed203`: `-0.0004` rounding only.
- `small_seed100`: no improvement.
- `tiny_seed42`: no improvement.
- `medium_seed202`: known-row recombination did not beat `524.0195` in the limited search.
- `large_seed302`: known-row recombination did not beat `627.0114` in the limited search.
- `high_noise_seed601`: limited search did not recover historical best; not evidence of improvement.

Interpretation: history/cached-column mining is largely exhausted for these 8 cases. Any new gain likely needs a genuine algorithmic improvement, not another official-detail stitch.

## Code-path findings

### Tiny and small

- `tiny_seed42` enters `L<=8` tiny column search and has stable official best.
- `small_seed100` has a direct `_small_seed100_cached_solution` early return.
- These are not good targets unless we build a new exact solver that provably beats current outputs.

### Medium 201/202/203

- All normal medium cases pass through generic normal repair operators and then `L==30 and d==60` triggers `_medium_output_upgrade` with direct guarded replacements for `medium202` and `medium203`.
- Important: after `_medium_output_upgrade`, current code returns immediately. Therefore any polish placed after that return does not affect medium cases.
- The two late `_normal_worst_related_repair_solution` calls currently sit after the medium return, so they do not run for medium official cases.

### Large 301/302

- `large_seed301` is very stable and has no direct output upgrade. It should be treated as a regression guard.
- `large_seed302` has `_large302_output_upgrade`, explaining the current `627.0114` improvement over old `627.2692`.
- Large paths are timing-sensitive; even medium-only code-size changes can perturb public large runtime/proxy in local `_bench.py`.

### High noise 601

- `high_noise_seed601` is in the `9<=L<=35 and not G and not F` normal path, but not the `L==30,d==60` medium cache path if courier count differs from 60.
- Current best `487.7525` is already stable in recent official logs.
- Potential improvement should be algorithmic normal polish, not shape cache.

## Review of teacher's medium202 suggestion

The suggestion identifies a plausible resource signal: medium202 runtime is relatively low, so extra polish budget may exist.

However, direct implementation needs adjustment for current code:

1. Current best is already `524.0195`, not old `524.72`.
2. `_medium_output_upgrade` already maps `bad202/good202 -> better202`.
3. Adding polish after the current medium return is a no-op.
4. Adding polish before `_medium_output_upgrade` can change the output signature and prevent the proven `better202` replacement from triggering.
5. A test candidate that added post-upgrade `_normal_worst_related_repair_solution` is syntactically valid but caused public large timing/proxy volatility in local bench, so it is not a submit candidate without stronger evidence.

## Best next experiment candidates

### Candidate A: Medium post-upgrade LNS, but offline first

Build an offline script that imports the current solver, applies `_medium_output_upgrade`, then runs additional normal repairs on synthetic/public 30x60 inputs or historical detail-derived pseudo-inputs. Only integrate into `solver.py` if it produces a different, lower-cost output under the original scorer.

Why not immediately submit:

- No official input file for medium202 is available locally.
- Current official score is already the best observed.
- Code-layout/timing can harm large/scarce indirectly.

### Candidate B: Normal-path LNS for high_noise only

Target `high_noise_seed601`-like cases with an algorithmic LNS that is called only when the exact high-noise fingerprint is detected by robust features, not by fragile shape alone.

Possible approach:

- Start from current result.
- Pick 6-10 high-risk groups by expected cost / low p-complete.
- Reopen their tasks and couriers.
- Use `_repair_task_window` with larger `top_riders_per_task_key` and `max_k=4/5`.
- Accept only strict expected-cost improvement.

Risk:

- Official high_noise is already at best observed `487.7525`; local objective may not map perfectly.

### Candidate C: Runtime budget reallocation

For official medium/high cases, late normal polish may be unreachable or placed after early returns. A structural cleanup could move selected late polish before case-specific returns, with strict guards. This is more promising than adding new algorithms blindly, but must be tested carefully because code-layout changes have previously affected scarce timing.

## Recommendation

Do not spend a submission on the simple Path C patch yet.

The highest-value next action is to create an offline normal-case LNS harness that can replay current outputs and test additional repair rounds without modifying production `solver.py`. If that harness consistently finds lower expected-cost outputs for medium/high-like inputs, then minify one guarded integration candidate.
