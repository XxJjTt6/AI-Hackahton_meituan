"""Reverse-engineered exact official scoring for AutoSolver.

Verified against all 264 detail rows of
runs/official_submit_20260520_132026_70222083.json with max abs error 0.0077
(pure rounding).

Per group with selected couriers and their (score, willingness) rows:
    p_complete    = 1 - prod(1 - w_i)
    expected_score = sum(w_i * s_i) / sum(w_i)
    cost          = expected_score * p_complete + (1 - p_complete) * 100 * k
where k = number of tasks in the task_id_list bundle.

Case total = sum(group cost) + 100 * (#uncovered tasks).

This module is offline-only (lives under runs/) and never imported by solver.py.
"""
from __future__ import annotations

import json
import os
import sys

PENALTY = 100.0
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)


def group_cost(rows, k):
    """rows: list of (score, willingness). k: task count in the bundle."""
    if not rows:
        return PENALTY * k
    prod_reject = 1.0
    num = 0.0
    den = 0.0
    for s, w in rows:
        prod_reject *= (1.0 - w)
        num += w * s
        den += w
    p = 1.0 - prod_reject
    exp = (num / den) if den > 0 else 0.0
    return exp * p + (1.0 - p) * PENALTY * k


def parse_input(text):
    """Return dict[(task_id_list, courier)] -> (score, willingness) and the set
    of all atomic task ids."""
    idx = {}
    tasks = set()
    lines = [l for l in text.replace("\r\n", "\n").split("\n") if l.strip()]
    for line in lines[1:]:
        parts = line.split("\t")
        if len(parts) < 4:
            continue
        tk, cid, sc, wl = parts[0], parts[1], parts[2], parts[3]
        try:
            idx[(tk, cid)] = (float(sc), float(wl))
        except ValueError:
            continue
        for t in tk.split(","):
            tasks.add(t)
    return idx, tasks


def score_solution(solution, idx, all_tasks):
    """solution: list[(task_id_list, [couriers])]. Returns (total, valid, info).

    Enforces official validity: a courier may not appear across multiple groups,
    and an atomic task may not be covered by more than one group.
    """
    used_couriers = set()
    covered = set()
    total = 0.0
    errors = []
    for tk, couriers in solution:
        atoms = tk.split(",")
        k = len(atoms)
        rows = []
        for c in couriers:
            if c in used_couriers:
                errors.append(f"duplicate courier {c}")
            used_couriers.add(c)
            rc = idx.get((tk, c))
            if rc is None:
                errors.append(f"missing row ({tk},{c})")
            else:
                rows.append(rc)
        for a in atoms:
            if a in covered:
                errors.append(f"duplicate task {a}")
            covered.add(a)
        total += group_cost(rows, k)
    uncovered = all_tasks - covered
    total += PENALTY * len(uncovered)
    valid = not errors
    return total, valid, {"covered": len(covered), "uncovered": sorted(uncovered), "errors": errors}


def _self_test_against_official():
    """Verify formula reproduces large_seed301 official total from raw input."""
    inp_path = os.path.join(
        ROOT,
        "Fwd_ 【美团AI Hackathon大赛】-【命题四AutoSolver：让AI Agent 自主求解配送分配问题】脱敏数据",
        "large_seed301.txt",
    )
    with open(inp_path, encoding="utf-8") as f:
        idx, tasks = parse_input(f.read())
    # find an official json with large_seed301 detail
    import glob

    det = None
    target = None
    for f in sorted(glob.glob(os.path.join(ROOT, "runs", "official_submit_*.json"))):
        try:
            d = json.load(open(f, encoding="utf-8"))
        except Exception:
            continue
        for cr in d.get("result", {}).get("case_results", []):
            if cr.get("case_file", "").startswith("large_seed301") and cr.get("detail"):
                det = cr["detail"]
                target = cr["total_score"]
                break
        if det:
            break
    sol = [(r["task_id_list"], list(r["couriers"])) for r in det]
    total, valid, info = score_solution(sol, idx, tasks)
    print(f"large_seed301 official={target} recomputed={round(total,4)} valid={valid}")
    print(f"  delta={round(abs(total-target),5)} covered={info['covered']} uncovered={info['uncovered']}")
    assert abs(total - target) < 0.05, "formula mismatch"
    print("OK: exact scorer reproduces official large_seed301 from raw input")


if __name__ == "__main__":
    _self_test_against_official()
