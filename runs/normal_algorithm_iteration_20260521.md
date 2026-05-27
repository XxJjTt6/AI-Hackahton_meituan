# Normal/Medium/High Algorithm Iteration

## User correction

Do not rely on historical best/caches. Look for algorithmic improvements in the other 8 cases.

## Prototypes built

### 1. `runs/prototype_normal_lns.py`

Algorithmic idea: large-neighborhood search around the incumbent.

- Select worst-cost windows, related-task windows, bundle-attractor windows, and deterministic random windows.
- Reopen 4-14 tasks.
- Re-solve the window with `_repair_task_window` using richer parameters (`top=14`, `max_k=5`, `option_limit=120`).
- Reassign couriers inside the repaired solution.
- Accept only strict expected-cost improvement with no coverage loss.

Results:

- Public `large_seed301`: tried 24 windows, no improvement.
- Synthetic `30x60` medium-like subset from public large: tried 27 windows, no improvement.

Interpretation: simply repeating or widening existing repair-window logic is not enough. Current normal path is locally saturated under this neighborhood.

### 2. `runs/prototype_single_task_master.py`

Algorithmic idea: treat normal/large output as a single-task multi-dispatch master problem.

- For each task, generate columns = combinations of top riders, `k=1..4`.
- Solve a beam set-packing master with unique-courier constraints.
- Force incumbent-prefix preservation so beam cannot lose the current solution.

Results:

- Public `large_seed301`, `maxk=3/4`: no improvement over incumbent.
- Synthetic `30x60` medium-like subset: no improvement over incumbent.

Interpretation: the current solver's single-task multi-dispatch distribution is already strong on public/synthetic normal cases. A naive task-column beam is not a breakthrough.

## Important algorithmic findings

1. The other-8-case current solution is not weak in the obvious local neighborhoods.
2. Extra polish rounds are unlikely to help unless the neighborhood/operator is genuinely different.
3. For normal cases, current solution structure is mostly single-task multi-dispatch; improving it requires global cardinality/courier allocation, not just task-window repair.
4. Public large and synthetic medium both appear locally saturated under:
   - current repair window,
   - expanded LNS windows,
   - single-task column beam master.

## Next stronger algorithm ideas

### A. Lagrangian/auction cardinality optimizer

Instead of fixed beam over task columns, introduce courier dual prices and iteratively choose each task's best rider subset under prices. Then update courier prices for overused riders. This is closer to Lagrangian relaxation and may escape beam pruning limits.

Sketch:

1. Initialize courier prices from incumbent marginal contribution.
2. For each task independently, choose best subset by `group_cost + sum(price[c])`.
3. Penalize couriers selected by multiple tasks; reward unused high-value couriers.
4. Iterate 30-80 rounds with subgradient/auction updates.
5. Recover feasible assignment by conflict repair / min-cost flow.

Why it may help: it changes the global allocation mechanism, not just local windows.

### B. Cardinality redistribution local search

Current repair mostly preserves or locally changes groups. A targeted operator should move from distributions like `{1:3,2:34,3:3}` to alternative count distributions, e.g. choose which tasks deserve 3 riders and which can survive with 1.

Operator:

1. Drop one rider from low-marginal 2/3-rider tasks.
2. Add that rider to high-marginal 1/2-rider tasks.
3. Evaluate exact group expected cost delta.
4. Use augmenting paths of length 2-5, not one-shot swaps.

Why it may help: public large has all 80 couriers used; improvement requires reallocating scarce rider capacity.

### C. Bundle-vs-redundancy tradeoff master

Normal cases may have useful bundles but current public large incumbent is all single-task. Build a master that compares:

- one bundle courier covering 2 tasks,
- freed rider used as redundancy on another task,
- single-task baseline.

This requires a 3-part exchange, not just replacing a window with lower raw cost.

## Recommendation

Do not submit the current LNS or single-task master prototypes; they are negative/neutral experiments.

Next real implementation should be **cardinality redistribution via augmenting paths**, because it targets the actual normal-case bottleneck: all couriers are already used, so gains require moving rider capacity between tasks based on marginal probability benefit.
