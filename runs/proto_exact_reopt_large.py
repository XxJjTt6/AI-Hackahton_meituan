"""Prototype: under the EXACT official objective, re-optimize courier selection
per task-group on large_seed301 (keeping the official task grouping), starting
from the official solution as incumbent. Can we beat official 654.2935?

This tests whether the old (approximate) critic left courier-selection value on
the table. Offline only.
"""
import json, glob, os, itertools
from exact_score import parse_input, group_cost, score_solution

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

inp_path = os.path.join(
    ROOT,
    "Fwd_ 【美团AI Hackathon大赛】-【命题四AutoSolver：让AI Agent 自主求解配送分配问题】脱敏数据",
    "large_seed301.txt",
)
idx, tasks = parse_input(open(inp_path, encoding="utf-8").read())

# official solution
det = None
for f in sorted(glob.glob(os.path.join(ROOT, "runs", "official_submit_*.json"))):
    try:
        d = json.load(open(f, encoding="utf-8"))
    except Exception:
        continue
    for cr in d.get("result", {}).get("case_results", []):
        if cr.get("case_file", "").startswith("large_seed301") and cr.get("detail"):
            det = cr["detail"]
            break
    if det:
        break
official_sol = [(r["task_id_list"], list(r["couriers"])) for r in det]
base_total, _, _ = score_solution(official_sol, idx, tasks)
print("official large total:", round(base_total, 4))

# couriers available per task_id_list group
avail = {}
for (tk, c) in idx:
    avail.setdefault(tk, []).append(c)

# For each official group, search best courier subset (size 1..4) for that exact
# task_id_list minimizing exact cost, ignoring global uniqueness first.
def best_subset_for_group(tk):
    k = len(tk.split(","))
    cands = avail.get(tk, [])
    rows = [(c, idx[(tk, c)]) for c in cands]
    best = None
    best_cost = float("inf")
    # limit subset size to 4
    for size in range(1, min(4, len(rows)) + 1):
        for combo in itertools.combinations(rows, size):
            cs = [r[1] for r in combo]
            cost = group_cost(cs, k)
            if cost < best_cost:
                best_cost = cost
                best = [r[0] for r in combo]
    return best, best_cost

improved = []
ub_total = 0.0
for tk, couriers in official_sol:
    sub, cost = best_subset_for_group(tk)
    improved.append((tk, sub))
    ub_total += cost

print("per-group exact-optimal (ignoring courier uniqueness) total:", round(ub_total, 4))

# check courier-uniqueness conflicts in the unconstrained optimum
seen = {}
conflicts = 0
for tk, cs in improved:
    for c in cs:
        if c in seen:
            conflicts += 1
        seen[c] = tk
print("courier conflicts in unconstrained optimum:", conflicts)

t2, valid2, info2 = score_solution(improved, idx, tasks)
print("unconstrained-improved scored:", round(t2, 4), "valid:", valid2, "errors:", len(info2["errors"]))
