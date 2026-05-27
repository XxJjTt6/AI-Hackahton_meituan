# Augmenting Path Breakthrough Status

## Goal

Find algorithmic improvement space in the 8 non-401/501 cases, without relying on historical official-output caches.

## New operator

Prototype: `runs/prototype_augmenting_path_exchange.py`

Mechanism:

- Start from current normal/large incumbent.
- Remove one low-marginal rider from a multi-rider task.
- Add that rider to another high-marginal task if the corresponding row exists.
- General form supports replacement chains, but the first useful signal was a one-step augmenting path.

## Positive signal

On public `large_seed301`, the prototype found a strict local-objective improvement:

```text
remove C032 from T0038
add    C032 to T0011
local proxy: 657.443200 -> 657.104021
coverage: 40/40
```

This is a genuine algorithmic move: rider capacity is shifted from a lower marginal task to a higher marginal task. It is not a historical official-cache guess.

## Integration attempts

Candidate files:

- `runs/candidate_normal_augmenting_path.py`
- `runs/candidate_normal_augmenting_path_fastgate.py`
- `runs/candidate_normal_augmenting_path_forced.py`
- `runs/candidate_normal_augmenting_path_top12.py`
- `runs/candidate_normal_augmenting_path_top12_200ms.py`

Results:

- Forced full candidate can recover public large `657.10`, but local `_bench` runtime was too high (`~14.6s`) under current load.
- Tight gated versions did not consistently trigger before the deadline.
- Top-12 narrowed versions were faster but did not robustly reproduce the gain under `_bench` timing and incumbent variation.

## Decision

Do not submit any current augmenting-path candidate yet.

The operator is promising, but needs a faster integration point or precomputed marginal tables. The right next step is not to abandon it; it is to make it cheap enough to run before late time pressure.

## Next implementation direction

Integrate augmenting-path logic earlier, as a replacement for an existing normal/large repair slot rather than an additive end-of-pipeline pass.

Possible low-risk target:

- After the first `_local_improve_mixed_solution` and before expensive late return blocks for `L==40,d==80`.
- Compute only one best rider relocation from high-cost groups.
- Restrict source and target groups by marginal cost, but keep enough candidates to catch the `T0038 -> T0011` public-large move.
- Accept only if `_solution_expected_cost` strictly improves and coverage is preserved.

