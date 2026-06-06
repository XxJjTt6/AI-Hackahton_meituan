"""Constrained local search under the EXACT official objective on large_seed301.

Keeps the official task grouping fixed, starts from the official solution as
incumbent, and tries add/remove/swap courier moves from the global free pool,
respecting courier-uniqueness and (already disjoint) task-uniqueness. Accepts a
move only if the exact total strictly improves.

This measures the *feasible* gain the approximate critic was leaving on large.
Offline only.
"""
import json, glob, os
from exact_score import parse_input, group_cost, score_solution

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

inp_path = os.path.join(
    ROOT,
    "Fwd_ 【美团AI Hackathon大赛】-【命题四AutoSolver：让AI Agent 自主求解配送分配问题】脱敏数据",
    "large_seed301.txt",
)
idx, tasks = parse_input(open(inp_path, encoding="utf-8").read())

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

groups = [(r["task_id_list"], list(r["couriers"])) for r in det]
base_total, base_valid, _ = score_solution(groups, idx, tasks)
print("start (official):", round(base_total, 4), "valid", base_valid)

# couriers available per task_id_list group (from input rows)
avail = {}
for (tk, c) in idx:
    avail.setdefault(tk, []).append(c)

def gcost(tk, couriers):
    k = len(tk.split(","))
    rows = [idx[(tk, c)] for c in couriers]
    return group_cost(rows, k)

# current assignment
assign = {tk: list(cs) for tk, cs in groups}
used = set()
for cs in assign.values():
    used.update(cs)

def total():
    return sum(gcost(tk, cs) for tk, cs in assign.items())

cur = total()
improved = True
rounds = 0
while improved and rounds < 200:
    improved = False
    rounds += 1
    for tk in list(assign.keys()):
        cs = assign[tk]
        base = gcost(tk, cs)
        pool = [c for c in avail.get(tk, []) if c not in used or c in cs]
        # try remove
        for c in list(cs):
            if len(cs) <= 1:
                break
            new = [x for x in cs if x != c]
            if gcost(tk, new) + 1e-9 < base:
                assign[tk] = new
                used.discard(c)
                base = gcost(tk, new)
                cs = new
                improved = True
        # try swap one courier for a free one
        best_delta = -1e-9
        best_move = None
        for ci, c in enumerate(cs):
            for nc in pool:
                if nc in cs:
                    continue
                new = list(cs)
                new[ci] = nc
                d_ = base - gcost(tk, new)
                if d_ > best_delta:
                    best_delta = d_
                    best_move = ("swap", c, nc, new)
        # try add a free courier
        for nc in pool:
            if nc in cs:
                continue
            new = cs + [nc]
            d_ = base - gcost(tk, new)
            if d_ > best_delta:
                best_delta = d_
                best_move = ("add", None, nc, new)
        if best_move:
            kind, old_c, nc, new = best_move
            assign[tk] = new
            if old_c is not None:
                used.discard(old_c)
            used.add(nc)
            improved = True

final_sol = [(tk, cs) for tk, cs in assign.items()]
ft, fv, fi = score_solution(final_sol, idx, tasks)
print("after local search:", round(ft, 4), "valid", fv, "errors", len(fi["errors"]), "rounds", rounds)
print("improvement vs official:", round(base_total - ft, 4))
