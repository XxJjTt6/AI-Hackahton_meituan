# Algorithmic Pivot: Stop Score Guessing, Improve Search Architecture

## User correction

Do not keep guessing official scoring. The right path is: learn OR literature, identify current algorithmic ceiling, implement structural solver improvements, and validate cautiously.

## Relevant literature takeaways

### Set-partitioning decomposition for crowdsourced shared-trip delivery

Yang, Hyland, Jayakrishnan (arXiv:2203.14719) uses a set-partitioning formulation over pre-generated feasible shared-trip routes, then a decomposition heuristic and switching/local-improvement procedure. This maps directly to our input rows as candidate columns.

Applicable idea: build a stronger master selection layer over candidate columns, then run structured switching / LNS rather than isolated greedy repairs.

### Meal delivery bundling with column/row generation

Yildiz & Savelsbergh (Transportation Science 2019) solve meal delivery routing with simultaneous column and row generation and explicitly study bundling benefits.

Applicable idea: scarce cases should not be handled as local T0033 patches. We need reduced-cost bundle pricing based on incumbent task/courier shadow prices, then choose bundles through a master packer.

### Probabilistic set covering and Benders

Chen et al. (arXiv:2402.18795) solve large-scale probabilistic set covering via Benders decomposition and scenario/sample structure.

Applicable idea: low-willingness cases should be viewed as probabilistic multi-cover. Instead of fixed K=2 heuristics only, use marginal failure-probability reductions as pricing signals.

## Current code bottleneck

The current `solver.py` already has pieces:

- `_search_column_window`: exact-ish column selection, but only over per-task-key top riders and a limited recursive task window.
- `_ssecr`: scarce column extraction from seed solutions plus canonical candidates, then beam packing.
- `_ssbgme`: bundle generation plus single completion using min-cost flow.
- `_pick_hard_scarce_best`: shadow cost selector, but not a true dual-pricing master.

The missing part is a proper iterative loop:

1. Start from incumbent.
2. Compute task/courier shadow prices from incumbent and uncovered penalties.
3. Price many candidate bundles by reduced cost, not raw expected cost.
4. Re-solve a restricted master over incumbent columns plus priced columns.
5. Complete/repair with min-cost flow.
6. Iterate 2-3 times under deadline.

## Proposed next algorithm slice

Implement a standalone prototype first, not in `solver.py`:

File: `runs/prototype_dual_priced_master.py`

Inputs:
- any solver input text
- current incumbent from `solver.solve(input_text)`

Steps:
1. Parse candidate rows.
2. Convert incumbent result to selected groups.
3. Estimate task prices:
   - uncovered task price = 100
   - covered task price = current group expected cost / task_count, plus scarcity premium if the group is single and task is high-conflict
4. Estimate courier prices:
   - used courier price = opportunity cost of current group
   - unused courier price = 0
5. Generate reduced-cost columns:
   - all two-task bundle rows
   - selected incumbent groups
   - selected high-quality single rows
6. Restricted master search:
   - branch by undecided task
   - enforce task/courier conflicts
   - objective = exact expected cost + uncovered penalty
7. Output candidate score and diff vs incumbent.

Why standalone first:
- avoids touching 80KB `solver.py`
- allows repeated experiments on public/proxy cases
- tells us whether dual-pricing improves actual local objective before minifying

## Success criterion before integration

Do not submit or integrate unless prototype finds one of:

- stable scarce proxy improvement across repeated runs without hurting large proxy timing
- low proxy improvement with same coverage and runtime below budget
- a deterministic official-shaped 401 candidate that differs for algorithmic reasons, not score-table guessing

