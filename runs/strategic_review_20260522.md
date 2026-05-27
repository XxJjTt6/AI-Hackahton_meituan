# AutoSolver strategic review — 2026-05-22

## 1. Immediate factual corrections

1. Current `solver.py` is not the official best file.
   - Current SHA: `41db4b34311c964c11fa16d650265a38a83cfea854d7aadd4cc8e72da3060951`, size `76108`.
   - This SHA scored official `706.4264`, not `706.197`.
   - Official best SHA is `70222083707d786011d28d7cc1ceab8f3b2ca95e0924b26f8dff2e6a49e865d6`, file `runs/candidate_high_signature_patch_70222083.py`, size `78516`.
   - Another equal-best guarded file exists: SHA `ab97ce939b454fd193ab9853cb1c8110778656a0adf8b0fbc17ed49f2acc1577`, size `78862`.

2. README is stale.
   - README still describes older `707.05` / `812ea145` context, while official best is now `706.197`.
   - Do not use README as the single source of truth for current best.

3. Official best is not a recombination opportunity.
   - Across 81 official records, the same best file has the best observed score for all 10 cases.
   - There is no historical case-level row that can simply be pasted to improve the average.

## 2. Competition objective as actually implemented by judge feedback

Input rows are columns: `(task_id_list, courier_id, total_score, willingness)`.

A feasible output chooses groups `(task_id_list, [couriers...])` subject to:

- each courier is used at most once;
- each task is covered by at most one selected task group;
- uncovered tasks pay approximately `100` each;
- assigning multiple couriers to one task group increases completion probability but consumes courier capacity;
- bundles save couriers but often have high raw cost and lower willingness.

The current local objective in `solver.py` is `_solution_expected_cost`, built from `_group_expected_cost`:

- enumerates which assigned couriers accept;
- if none accept, charges `100 * task_count`;
- if some accept, charges average accepted row score;
- sums group costs plus uncovered penalties.

This objective is a reasonable stochastic set-packing approximation, but official probes show it is not perfectly calibrated, especially for low/scarce.

## 3. Current solver architecture

The solver is a case-routed portfolio heuristic:

1. Parse rows and detect features:
   - `G = courier_count <= task_count` for scarce;
   - `F = avg_willingness < .27` for low willingness;
   - `J = low + non-scarce + 30 tasks + >=50 couriers` for seed501-like low.
2. Early hard caches:
   - `scarce_seed401_cached_solution` for 40x40 scarce;
   - `small_seed100_cached_solution` for 15-task small.
3. Candidate generators:
   - single-task multi-dispatch greedy;
   - reassign/rebalance via min-cost flow;
   - disjoint-then-multidispatch greedy;
   - pair-potential matching;
   - low/scarce column windows;
   - scarce bundle MCF/enumeration;
   - sparse cover;
   - fallback official greedy.
4. Picker:
   - normal: minimum local expected cost;
   - low: robust mixture of avg-subset, min-score-accepter, max-willingness models;
   - hard scarce: shadow cost that penalizes uncovered tasks, extra redundancy, bundles.
5. Polish:
   - local merge/split/rewire;
   - repair windows;
   - scarce insertion/ejection/shift;
   - low deep/late acceptance repair.
6. Case-specific output upgrades:
   - medium exact-signature upgrades;
   - large302 exact-signature upgrade.

## 4. Why the last few days did not break through

### 4.1 The search is mostly local around already-good structures

Most operators preserve the high-level shape:

- normal/large remain mostly single-task, about two couriers per task;
- low501 remains exactly `{30 groups x 2 couriers}`;
- scarce401 remains static bundle-heavy `20 groups` covering `39/40` tasks.

Local windows, pairwise exchange, triple exchange, and simple reassign can improve within that shape, but they rarely change the global structure.

### 4.2 Official failures repeat a few patterns

Regression patterns versus best `706.197`:

- `high_noise_seed601` often worsens from `487.7525` to `490.0466` when normal-path/global changes are introduced.
- `scarce401` often worsens from `1531.5317` to `1589.3393`, a known bad sparse/near-miss structure.
- `low501` worsens sharply when deviating from the established K=2 all-task structure.

This means many changes are not neutral: the current portfolio is balanced on tight guards and timing, so adding a late operator often changes a fragile branch.

### 4.3 The local objective is good enough to stabilize, but not good enough to guide breakthroughs

For low/scarce, official score probes show local expected cost can mis-rank alternatives:

- low probes confirmed K=2 and willingness quality matter, but current best is already better than simple K=2 top-w baselines;
- scarce dynamic replacements selected by local objectives repeatedly triggered worse official structures;
- 401 hard-cache is safer than local dynamic replacements.

So the issue is not “we did not try enough local moves”; it is that the search objective and neighborhood do not expose a reliable improving direction.

### 4.4 We mixed three workflows that should be separated

1. Production best preservation.
2. Algorithmic experiments.
3. Official information probes.

Because these were mixed in the same `solver.py`, the workspace drifted: current `solver.py` is not the official best. This is a process bug, not an algorithm bug.

## 5. Case-level interpretation of official best

Official best `706.197`:

- normal/high/large/medium/small/tiny are all fully covered and mostly near `15-17` per task;
- low501 is fully covered, exactly 30 groups with 2 couriers each, score `1799.9031`;
- scarce401 uses 20 single-courier groups, 19 of them bundles, covering `39/40`, score `1531.5317`.

Implications:

- normal cases are not the main breakthrough source; improvements are likely sub-point to a few points unless a new global realloc operator is found;
- low501 needs a new global model for redundant assignment, not more greedy K=2 tweaking;
- scarce401 needs a correct selective/bundling set-packing model with official-calibrated risk, not local T0033/near-miss probes.

## 6. Recommended long-term reset

### Step A — Restore production baseline discipline

- Treat `runs/candidate_high_signature_patch_70222083.py` as immutable official best.
- Do not edit it directly.
- If needed, copy it to `solver.py` only for a final known-good submission.
- Put all experiments in `runs/experiments/` or named candidate files.

### Step B — Build an offline exact evaluator harness

Before any new official submission, build a harness that:

- loads a solver/candidate;
- runs it on public large and synthetic low/scarce variants;
- records output structure: group count, rider-count distribution, bundle distribution, uncovered tasks;
- computes multiple objective models: avg-subset, min-score-accepter, max-willingness, official-detail-inspired variants;
- compares against official-best output signatures.

The goal is not perfect prediction, but to prevent changes that silently alter high_noise/medium/large branches.

### Step C — Replace local patching with two real master problems

1. Low501 master: redundant assignment master.
   - Variables: for each task, choose a subset of couriers or a compact top-k column.
   - Constraint: each courier used at most once.
   - Objective: robust ensemble of acceptance models, not only avg-subset.
   - Search: Lagrangian/auction dual prices over couriers, then conflict repair.

2. Scarce401 master: selective bundle set-packing.
   - Variables: candidate columns are bundles/singles with one courier.
   - Constraint: courier unique, task covered at most once.
   - Objective: official-calibrated group cost plus uncovered penalty.
   - Search: beam/branch over bundle columns, complete with min-cost flow for remaining singles.
   - Important: compare to hard-cache by official-observed structure, and reject known `1589.3393` pattern.

### Step D — Only then consider official probes

Submit only when a candidate gives one of these:

- improves public/synthetic objective by a meaningful margin and preserves all output structures outside target branch;
- produces a fundamentally different low/scarce structure with a clear hypothesis;
- is guarded so non-target cases are byte-for-byte or signature-equivalent to `70222083` output.

## 7. Next concrete action

The best next action is not another submission. It is:

1. restore/copy official best into a protected baseline file;
2. create a comparison harness against that baseline;
3. implement one isolated low501 Lagrangian redundant-assignment prototype outside `solver.py`;
4. implement one isolated scarce401 set-packing prototype outside `solver.py`;
5. only integrate the prototype that beats the baseline locally and does not change non-target signatures.
