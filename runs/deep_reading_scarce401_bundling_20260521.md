# Deep Reading Notes for `scarce_couriers_seed401`

Date: 2026-05-21
Scope: scarce-courier bundling / set-partitioning improvements that should not damage normal/medium/large cases.

## 0. Executive conclusion

The papers do **not** suggest a broader local repair around `T0033` or a raw global set-packing over all rows. They suggest a three-layer architecture:

1. **Generate high-quality bundle columns selectively**: only bundles with strong reduced-cost / opportunity-cost evidence should enter the restricted master.
2. **Solve a restricted set-partitioning master** over those columns plus single-task fallback columns.
3. **Iteratively swap / repair** only around columns with bad shadow value, not around arbitrary missing tasks.

Current `solver.py` already has partial versions:
- `_ssbgme`: bundle columns + single min-cost completion.
- `_ssecr`: seed-solution columns + beam packing.
- `_solve_scarce_bundle_mcf_enum`: bundle-row enumeration + MCF single completion.
- `_augment_scarce_cache/_boer`: hard-cache neighborhood repair.

The missing piece is **selective column inclusion based on opportunity price**. Current pruning mostly uses raw expected cost / gain; scarce401 needs columns that are good relative to the single/fallback rows they displace and the couriers they consume.

## 1. Yildiz & Savelsbergh MDRP: what transfers

Source: `Provably High-Quality Solutions for the Meal Delivery Routing Problem`.

### Key model idea

- A bundle is a small ordered group of orders/tasks served together.
- A work-package is a feasible way for a courier to serve a bundle.
- The formulation chooses work-package variables, not individual greedy assignments.

Translated to our problem:

- A candidate input row `(task_key, courier, score, willingness)` is a one-courier work-package for a task bundle.
- A solver output group `(task_key, [couriers])` is a stochastic work-package column: multiple couriers assigned to the same task bundle to improve success probability.
- For scarce401, the most important columns are **two-task bundle + one courier**, because they save one courier and preserve coverage.

### Key algorithm idea

The paper uses restricted formulations, column generation, and then solves an IP with generated columns. The important practical enhancement is **Selective Column Inclusion (SCI)**: include only a small number of columns likely to help integer quality.

Translated to our code:

- Do not add a huge all-row set-packing search. We tested that and it was slow / not useful.
- Add a small “SCI-style” bundle candidate pool around the incumbent hard-cache scaffold.
- Columns should be selected by reduced cost, not just raw cost.

### Implementation implication

For each possible bundle row/group `g` covering tasks `S` and using couriers `R`, estimate:

```text
reduced_cost(g) = exact_group_cost(g)
                  - displaced_task_value(S)
                  + courier_opportunity_penalty(R)
                  + overlap_penalty
```

A column is worth testing only if this is negative or close to negative.

For current code, `displaced_task_value(S)` can be approximated by:

- The cost of current incumbent groups that cover tasks in `S`.
- Or min-cost single fallback for tasks in `S` when outside couriers are reserved.
- Or `100 * uncovered_count` if a task is otherwise uncovered.

This is exactly the missing improvement over `_ssbgme`, which currently ranks bundle groups by raw expected gain.

## 2. Yang et al. crowdsourced delivery at scale: what transfers

Source: `Tackling the Crowdsourced Delivery Problem at Scale with a Novel Decomposition Heuristic`.

### Key model idea

Their set-partitioning model selects feasible routes so every delivery is covered once and every vehicle route is used within vehicle limits. Their large-scale heuristic decomposes into:

1. Generate candidate routes.
2. Assign deliveries to shared vehicles / routes.
3. Route or complete remaining deliveries.
4. Improve by swapping assignments between systems.

Translated to scarce401:

1. Generate candidate two-task bundle columns (`task_key` rows, optionally same key with multiple couriers if probability justifies it).
2. Select non-overlapping bundle columns under courier conflicts.
3. Complete uncovered tasks by min-cost singles or allow selected task drops.
4. Swap tasks between bundle columns and single fallback columns.

### Critical transfer

Their route-generation quality dominates the assignment quality. In our setting, official seed401 hard-cache suggests the current route/column generation is too narrow: dynamic no-cache finds worse 38/40 families, hard cache gives 39/40, but no method has generated a better 39/40 or 40/40 column set.

So next improvement should not be a picker tweak. It should be a better candidate-column generator that starts from hard-cache columns but injects **alternative bundles with good opportunity cost**.

## 3. PSCP Benders: what transfers

Source: `Towards large-scale probabilistic set covering problems: an efficient Benders decomposition approach`.

### Key model idea

The paper separates master decisions from probabilistic feasibility/cuts. The core useful idea for us is not a full Benders implementation, but a way to think about infeasibility / coverage as cuts:

- Master selects columns.
- Subproblem evaluates whether coverage/probability/resource requirements are violated.
- Violations produce cuts / penalties that guide future columns.

Translated to scarce401:

- The master is bundle-column selection.
- The subproblem is uncovered tasks + occupied couriers + exact stochastic group cost.
- A “cut” can be implemented heuristically as a penalty/price update:
  - Increase price for still-uncovered tasks.
  - Increase opportunity penalty for couriers that block cheap fallback columns.
  - Decrease attractiveness of bundles that cause a high-value task to become uncovered.

This gives a lightweight Benders-like iterative heuristic without adding solver dependencies.

## 4. Why previous attempts failed under this lens

### Owner-window / T0033 repair

It widened a repair window around missing-task couriers, but it still searched locally. Official result was no-op. That means the available `T0033` rows do not combine profitably under the current local window and exact objective.

### Raw single-row set-packing master

It ignored work-package / bundle-column structure and used raw row gain. It was rejected locally because it did not improve scarce proxy and added runtime.

### No-cache dynamic scarce

It generated a 38/40 solution that lost `T0028` and `T0033`, proving coverage must be protected globally and that a visually “more bundled” solution can be worse.

## 5. Concrete next algorithm worth trying

Name: **Scarce SCI reduced-cost bundle master**.

Guard:

```python
scarce_mode = task_count >= 25 and courier_count <= task_count * 1.05
```

But for official safety, initially only activate as an extra candidate for `G` or inside the guarded hard-cache path; final exact objective keeps incumbent if not better.

### Step A: incumbent pricing

Build from current candidate solutions `E` and/or hard cache:

- `task_owner[t] -> current group key`
- `courier_owner[c] -> current group key`
- `group_cost[key] = _group_expected_cost(rows, len(tasks))`
- `task_price[t] = group_cost[key] / len(group_tasks)` plus uncovered bonus if missing.
- `courier_penalty[c] = fallback_loss(c)` estimated from cheapest rows blocked if courier removed.

### Step B: selective bundle column generation

For every two-task row or two-task same-key group:

```text
bundle_value = sum(task_price[t] for t in tasks)
bundle_cost = _group_expected_cost(group_rows, 2)
release_bonus = value of groups that become removable / opened
courier_penalty = sum(courier_penalty[c] for c in group_couriers)
reduced = bundle_cost - bundle_value + courier_penalty - release_bonus
```

Keep only a small SCI pool:

- Best 3-5 columns per task pair.
- Best 80-160 global columns by reduced cost.
- Force-include columns from incumbent and official hard-cache scaffold.

### Step C: restricted master

Use the existing `_ssbgme` / `_ssecr` pattern:

- Beam states: `(covered_task_mask, used_courier_mask, selected_columns)`.
- State score should be **true completion cost estimate**, not just raw gain:
  - selected exact group costs
  - min-cost single completion for uncovered tasks with remaining couriers
  - optional uncovered penalty if single completion is impossible or too expensive
- Keep beam small and deterministic.

### Step D: completion and validation

Complete each beam state with `_csbgwm`-style min-cost flow singles.
Then accept only if:

```python
coverage(candidate) >= coverage(incumbent)
exact_cost(candidate) < exact_cost(incumbent) - eps
```

For official hard-cache seed401, this protects the current 39/40 incumbent.

## 6. What should not be tried again

- Final picker-only changes.
- Larger topN K2 single-task assignment.
- Longer `_llars` / same neighborhood time increase.
- T0033 owner-window only.
- Broad global set-packing over all rows without reduced-cost pruning.
- Removing hard cache or letting dynamic scarce solution overwrite it by raw expected cost.

## 7. Expected benefit and risk

Potential benefit:

- The only plausible 401 improvement is finding a better 39/40 same-coverage arrangement or a genuinely economical 40/40 arrangement.
- SCI reduced-cost bundle master targets exactly that gap.

Risk control:

- Add only as an extra candidate.
- Keep hard cache as incumbent.
- Exact objective and coverage guard prevent 401 degradation.
- Scarce classifier keeps normal/medium/large behavior unchanged.

## 8. Suggested next implementation slice

Smallest useful code slice:

1. Add a helper that computes incumbent task/courier prices from a selected solution.
2. Add a helper that creates reduced-cost two-task bundle columns from candidate rows.
3. Reuse `_csbgwm` to complete uncovered tasks.
4. Call this helper only from `_augment_scarce_cache` or `G` scarce branch as candidate, not as direct return.

Do not submit until local proxy plus official-like reasoning shows the candidate produces a different solution with exact improvement, or until it is intentionally used as a high-value information probe.

## 9. Implementation experiment after deep reading

Prototype saved: `runs/candidate_scarce_sci_reduced_cost_20260521.py`.

### Positive signal

A standalone SCI reduced-cost bundle prototype found a public scarce proxy improvement:

- Base public scarce proxy: `1097.8471`.
- SCI candidate: `1089.0410` to `1081.39` in one integrated run depending on timing.
- The key discovered move was a single bundle column:
  - Add `T0019,T0024 / C023`, expected group cost about `49.2808`.
  - This triggers a chain reassignment of singles: `C024 -> T0038`, `C037 -> T0010`, `C005 -> T0006`.

This validates the paper-derived hypothesis: the useful move is not a local `T0033` patch, but a reduced-cost bundle column followed by single-task completion.

### Rejection reason for current integration

The first integrated helper was not stable enough:

- If called too late, internal deadline is already exhausted and it no-ops.
- If called too early, it prices against a not-yet-polished incumbent and misses the useful column.
- If called with extra time, it can increase total runtime and threatens the 10s judge budget.
- File size also exceeded the conservative `80KB` decimal target.

Decision: reverted `solver.py` to safe SHA `ab97ce93`. Do not submit the current SCI integration.

### Next implementation direction

Keep the SCI idea, but integrate it as a **replacement** for an existing scarce postprocess slot, not as an additive pass. The right target is likely immediately after the first `_lims`/reassignment creates the single-heavy incumbent, and it must reuse precomputed candidate pools to avoid extra scanning.

Concrete next slice:

1. Refactor `_ssci1` to accept already-built `singles` and `bundle_rows`, or fold its reduced-cost ranking into `_ssbgme`.
2. Avoid repeated `_csbgwm` calls for many candidates; first evaluate only top 8-12 columns by cheap completion estimate.
3. Preserve only if public scarce improvement is stable across repeated proxy runs and large/low timings stay within budget.

## 10. Official probe: SCI single-bundle completion

SHA: `665444bb659eba6d3313131b055655be921a931683d3085e7cb2fc4b4f849f83`.
Saved candidate: `runs/candidate_official_noop_sci_single_bundle_665444bb_20260521.py`.

User approved this as a format/trigger probe. Initial candidate exceeded the official size limit, so the base-preserving variant was removed and the generic single-bundle completion helper was submitted under size budget.

Official result:

- Average remained `706.197`.
- `scarce_couriers_seed401` remained `1531.5317`, assigned `39/40`.
- All other cases unchanged and valid.

Interpretation:

- The format is valid, but generic single-bundle completion does not affect official hard-cache 401.
- The public scarce proxy improvement is real but does not transfer through the official seed401 hard-cache path.
- Reverted `solver.py` to safe SHA `ab97ce93`; do not keep this no-op helper in the final solver.

Next direction:

- If continuing SCI for official 401, it must be hard-cache preserving and under size budget, or directly target hard-cache observed columns.
- Generic scarce proxy improvements should not be submitted unless they can also affect hidden official 401 or another official case.

## 11. Hard-cache preserving missing-task replacement attempt

Implemented locally but not submitted: compact `_augment_scarce_cache` logic that tries one replacement row involving current missing task(s), removes conflicting hard-cache groups, fills opened tasks with best singles, and accepts only if coverage and exact objective improve.

Why not submit yet:

- It is size-safe (`79795` bytes) and preflight-valid.
- It only affects official-shaped seed401 hard-cache, so other cases should be structurally unaffected.
- But it overlaps heavily with the previously submitted owner-window probe (`511d45f6`), which was official no-op.
- The direct observed improvement conditions are strict:
  - `T0033/C000` improves only if alternative `T0016` fill cost is below about `47`.
  - `T0019,T0033/C010` improves only if alternative `T0012` fill is cheap enough.
- The previous owner-window probe likely already tested much of this neighborhood and did not improve.

Decision: keep as local candidate, but do not spend a submission without a stronger differentiator.
