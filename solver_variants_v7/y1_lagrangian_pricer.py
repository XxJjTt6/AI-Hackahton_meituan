"""
Path Y — Lagrangian column pricing heuristic for AutoSolver.

Self-contained module. Drop in alongside solver.py and call:

    from solver_variants_v7.y1_lagrangian_pricer import lagrangian_columns
    extra_solution = lagrangian_columns(C, B, deadline)   # B = set of all task ids
    if extra_solution: E.append(extra_solution)

Algorithm
---------
Given the existing candidate pool (no new columns generated — competition rule),
use subgradient ascent on the Lagrangian dual to discover NEW combinations of
existing columns that the greedy / repair-window heuristics miss.

1. Initialize multiplier lambda_t = avg_cost_per_task from a quick greedy solve.
2. For up to `max_iter` rounds (or until deadline):
   a. Compute reduced cost  rc(S) = est_cost(S) - sum_{t in S.tasks} lambda_t
      for every candidate S.
   b. Greedy-pick disjoint candidates with most-negative rc to build a feasible
      assignment x. (One courier per task; one task per courier.)
   c. Compute Lagrangian lower bound; track best primal feasible.
   d. Subgradient update:  lambda_t += step * (1 - covered_t),  step decays 1/k.
3. Return the best feasible primal solution found.

Key properties
--------------
- DOES NOT INVENT NEW COLUMNS — only re-prioritises the input candidates.
- Strictly additive: returns None on failure; caller decides whether to use it.
- Deadline-respected: every loop checks time.monotonic().
- Cost evaluation reuses solver._group_expected_cost for consistency with the
  competition's scoring proxy.
"""

import time
import math


def _cand_atomic_cost(group_cost_fn, c):
    """Expected cost if just this candidate covers its task set, single rider."""
    return group_cost_fn([c], len(c[1]))


def _greedy_assign(cands_with_rc, all_tasks):
    """Greedy pick: most negative rc first; skip conflicts.

    Returns (selected_list, uncovered_set).
    Conflict rule: courier reused across groups => skipped; task reused => skipped.
    """
    used_couriers = set()
    used_tasks = set()
    picked = []
    # cands_with_rc: list of (rc, idx, cand_tuple)
    for rc, _, c in cands_with_rc:
        courier = c[2]
        tasks = c[1]
        if courier in used_couriers:
            continue
        if any(t in used_tasks for t in tasks):
            continue
        picked.append(c)
        used_couriers.add(courier)
        for t in tasks:
            used_tasks.add(t)
    uncovered = set(all_tasks) - used_tasks
    return picked, uncovered


def _result_from_picked(picked):
    """Convert list of cand tuples to competition result format
    [(task_str, [courier_id]), ...]
    Group by task_str so same task set with multiple riders becomes one entry.
    """
    by_key = {}
    for c in picked:
        key = c[0]  # task_str
        by_key.setdefault(key, []).append(c[2])
    return [(k, v) for k, v in by_key.items()]


def lagrangian_columns(candidates, all_tasks, deadline,
                       base_result=None,
                       max_iter=24,
                       solver_module=None,
                       robust_pick=False):
    """
    Returns a result list, or None if infeasible / no time.

    Parameters
    ----------
    candidates : list of (T, tasks_tuple, courier_id, score, willingness, idx)
    all_tasks  : set/iterable of task ids
    deadline   : time.monotonic() float deadline
    base_result: optional existing solution; used to seed lambda
    max_iter   : subgradient rounds
    solver_module: optional ref to solver module (for cost fns); auto-imported
    robust_pick: if True, also score solutions with min-score and max-willingness
                 models and average — robust against avg-subset bias
    """
    if solver_module is None:
        import solver as solver_module
    S = solver_module

    if time.monotonic() > deadline - 0.05:
        return None

    cands = list(candidates)
    all_tasks_set = set(all_tasks)
    n_tasks = len(all_tasks_set)
    if not cands or not n_tasks:
        return None

    # task -> list of candidate indices covering it
    task_to_cands = {t: [] for t in all_tasks_set}
    atomic_costs = [None] * len(cands)
    for i, c in enumerate(cands):
        atomic_costs[i] = _cand_atomic_cost(S._group_expected_cost, c)
        for t in c[1]:
            if t in task_to_cands:
                task_to_cands[t].append(i)

    # Init lambda: for each task, cheapest atomic cost among covering candidates
    lam = {}
    for t in all_tasks_set:
        ids = task_to_cands[t]
        if not ids:
            lam[t] = 100.0  # uncovered task penalty
        else:
            best = min(atomic_costs[i] / max(1, len(cands[i][1])) for i in ids)
            lam[t] = max(0.0, best)

    best_primal = None
    best_primal_cost = float("inf")

    for it in range(max_iter):
        if time.monotonic() > deadline - 0.05:
            break

        # Compute reduced costs
        rc_list = []
        for i, c in enumerate(cands):
            rc = atomic_costs[i] - sum(lam.get(t, 0.0) for t in c[1])
            rc_list.append((rc, i, c))
        rc_list.sort(key=lambda x: x[0])

        picked, uncovered = _greedy_assign(rc_list, all_tasks_set)
        result = _result_from_picked(picked)

        # Score primal (add 100 penalty per uncovered task)
        try:
            primal_cost = S._solution_expected_cost(result, cands, all_tasks_set)
        except Exception:
            primal_cost = float("inf")

        if robust_pick:
            try:
                c_min = S._solution_expected_cost_by_model(result, cands, all_tasks_set, "min_score")
                c_max = S._solution_expected_cost_by_model(result, cands, all_tasks_set, "max_willingness")
                primal_cost = 0.45 * primal_cost + 0.45 * c_min + 0.10 * c_max
            except Exception:
                pass

        if primal_cost < best_primal_cost:
            best_primal_cost = primal_cost
            best_primal = result

        # Subgradient update
        step = 2.0 / (1.0 + it)
        covered_count = {t: 0 for t in all_tasks_set}
        for c in picked:
            for t in c[1]:
                if t in covered_count:
                    covered_count[t] += 1
        for t in all_tasks_set:
            g = 1 - covered_count[t]  # +1 if uncovered, -k if multi-covered (won't happen here)
            lam[t] = max(0.0, lam[t] + step * g)

    return best_primal


# ---------- Local sanity test ----------
if __name__ == "__main__":
    import os, sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import solver as S

    data_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "Fwd_ 【美团AI Hackathon大赛】-【命题四AutoSolver：让AI Agent 自主求解配送分配问题】脱敏数据",
        "large_seed301.txt",
    )
    text = open(data_path).read()
    lines = text.strip().splitlines()
    start = 1 if lines and lines[0].startswith("task") else 0
    C = []
    B = set()
    for idx, ln in enumerate(lines[start:]):
        parts = ln.strip().split("\t")
        if len(parts) < 4:
            continue
        T, U, sc, w = parts[:4]
        T = T.strip()
        U = U.strip()
        tasks = tuple(x.strip() for x in T.split(",") if x.strip())
        if not tasks or not U:
            continue
        try:
            sc_f = float(sc)
            w_f = float(w)
        except ValueError:
            continue
        C.append((T, tasks, U, sc_f, w_f, idx))
        for t in tasks:
            B.add(t)

    print(f"loaded {len(C)} cands, {len(B)} tasks")
    t0 = time.monotonic()
    res = lagrangian_columns(C, B, t0 + 5.0)
    t1 = time.monotonic()
    if res is None:
        print("infeasible / no time")
    else:
        cost = S._solution_expected_cost(res, C, B)
        covered = set()
        for k, _ in res:
            for t in k.split(","):
                covered.add(t.strip())
        print(f"lagrangian: groups={len(res)} covered={len(covered)}/{len(B)} proxy={cost:.2f} time={t1-t0:.2f}s")
