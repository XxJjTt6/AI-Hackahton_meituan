#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from autosolver.competition_audit import parse_competition_rows, group_expected_cost  # noqa: E402

# This is a structural scanner for public/synth scarce instances, not official 401 hidden input.
# It asks: around a hard-cache-like incumbent, what unobserved groups would be needed to improve?


def load_solution_from_official(path, case_file):
    data = json.load(open(path))
    for case in data['result']['case_results']:
        if case['case_file'] == case_file:
            return [(g['task_id_list'], list(g['couriers'])) for g in case['detail']]
    raise KeyError(case_file)


def metrics(solution, rows, tasks):
    covered = set()
    used = set()
    cost = 0.0
    for task_key, couriers in solution:
        group = []
        for c in couriers:
            r = rows.get((task_key, c))
            if r is None or c in used:
                return None
            used.add(c); group.append(r)
        for t in group[0].task_ids:
            if t in covered:
                return None
            covered.add(t)
        cost += group_expected_cost(group, len(group[0].task_ids))
    return cost + 100 * (len(tasks)-len(covered)), covered, used



def two_remove_two_add(inc, rows, tasks, base_cost):
    import itertools
    group_costs=[]
    for i,(tk,cs) in enumerate(inc):
        group=[rows[(tk,c)] for c in cs if (tk,c) in rows]
        group_costs.append((group_expected_cost(group,len(group[0].task_ids)),i,tk,cs))
    focus=[i for _,i,_,_ in sorted(group_costs, reverse=True)[:12]]
    best=[]
    for removed in itertools.combinations(focus,2):
        remaining=[g for j,g in enumerate(inc) if j not in removed]
        m=metrics(remaining, rows, tasks)
        if not m: continue
        rem_cost, covered, used=m
        open_tasks=tasks-covered
        pool=[]
        for r in rows.values():
            if r.courier_id in used: continue
            if not set(r.task_ids) <= open_tasks: continue
            pool.append(r)
        pool=sorted(pool,key=lambda r: group_expected_cost([r],len(r.task_ids)))[:250]
        for a,b in itertools.combinations(pool,2):
            if a.courier_id==b.courier_id: continue
            if set(a.task_ids) & set(b.task_ids): continue
            new=remaining+[(a.task_key,[a.courier_id]),(b.task_key,[b.courier_id])]
            nm=metrics(new,rows,tasks)
            if nm and nm[0] < base_cost-1e-9:
                best.append((nm[0]-base_cost, removed, (a.task_key,a.courier_id), (b.task_key,b.courier_id), nm[0], len(nm[1])))
    best.sort()
    return best

def main():
    input_file = Path(sys.argv[1])
    input_text = input_file.read_text()
    rows, tasks = parse_competition_rows(input_text)
    # Use solver baseline on this input as incumbent.
    import importlib.util
    spec=importlib.util.spec_from_file_location('solver_best', ROOT/'runs/baselines/official_best_70222083.py')
    mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    inc = mod.solve(input_text)
    base = metrics(inc, rows, tasks)
    print('inc', base[0], 'covered', len(base[1]), 'used', len(base[2]), 'groups', len(inc))
    row_by_task = defaultdict(list)
    for r in rows.values():
        row_by_task[r.task_key].append(r)
    candidates=[]
    for remove_count in [1,2,3]:
        # Focus on removing worst groups.
        group_costs=[]
        for i,(tk,cs) in enumerate(inc):
            group=[rows[(tk,c)] for c in cs if (tk,c) in rows]
            group_costs.append((group_expected_cost(group,len(group[0].task_ids)),i,tk,cs))
        for _,i,_,_ in sorted(group_costs, reverse=True)[:10]:
            removed=[i]
            remaining=[g for j,g in enumerate(inc) if j not in removed]
            m=metrics(remaining, rows, tasks)
            if not m: continue
            rem_cost, covered, used=m
            open_tasks=tasks-covered
            # Try one candidate group that covers 1-2 open tasks using unused courier.
            for r in rows.values():
                if r.courier_id in used: continue
                if not set(r.task_ids) <= open_tasks: continue
                new=remaining+[(r.task_key,[r.courier_id])]
                nm=metrics(new,rows,tasks)
                if nm and nm[0] < base[0]-1e-9:
                    candidates.append((nm[0]-base[0], removed, r.task_key, r.courier_id, nm[0], len(nm[1])))
    candidates.sort()
    print('improving one-row candidates', len(candidates))
    for item in candidates[:20]: print(item)
    best2=two_remove_two_add(inc, rows, tasks, base[0])
    print('improving two-row candidates', len(best2))
    for item in best2[:20]: print(item)

if __name__=='__main__': main()
