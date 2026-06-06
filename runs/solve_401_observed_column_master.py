#!/usr/bin/env python3
from __future__ import annotations

import glob
import json
from collections import defaultdict

CASE = 'scarce_couriers_seed401.txt'
ALL_TASKS = [f'T{i:04d}' for i in range(40)]
TASK_INDEX = {task: index for index, task in enumerate(ALL_TASKS)}
ALL_COURIERS = [f'C{i:03d}' for i in range(40)]
COURIER_INDEX = {courier: index for index, courier in enumerate(ALL_COURIERS)}


def iter_case_results():
    for path in glob.glob('runs/official_submit_*.json'):
        try:
            data = json.load(open(path))
            result = data.get('result') or {}
            for case in result.get('case_results', []):
                if case.get('case_file') == CASE:
                    yield path, data, result, case
        except Exception:
            continue


def collect_columns():
    by_signature = {}
    sources = defaultdict(list)
    for path, data, result, case in iter_case_results():
        for group in case.get('detail', []):
            task_key = group['task_id_list']
            couriers = tuple(group['couriers'])
            tasks = tuple(task_key.split(','))
            if any(task not in TASK_INDEX for task in tasks):
                continue
            if any(courier not in COURIER_INDEX for courier in couriers):
                continue
            task_mask = 0
            for task in tasks:
                task_mask |= 1 << TASK_INDEX[task]
            courier_mask = 0
            ok = True
            for courier in couriers:
                bit = 1 << COURIER_INDEX[courier]
                if courier_mask & bit:
                    ok = False
                    break
                courier_mask |= bit
            if not ok:
                continue
            signature = (task_key, couriers)
            cost = float(group['cost'])
            old = by_signature.get(signature)
            if old is None or cost < old['cost']:
                by_signature[signature] = {
                    'task_key': task_key,
                    'couriers': couriers,
                    'tasks': tasks,
                    'task_mask': task_mask,
                    'courier_mask': courier_mask,
                    'cost': cost,
                    'p': group.get('p_complete'),
                    'expected_score': group.get('expected_score'),
                }
            sources[signature].append((path, result.get('avg_score'), case.get('total_score')))
    return list(by_signature.values()), sources


def solve_beam(columns, beam_width=200000):
    columns = sorted(columns, key=lambda c: (100 * len(c['tasks']) - c['cost'], len(c['tasks']), -len(c['couriers'])), reverse=True)
    states = [(0.0, 0, 0, [])]
    best = (100.0 * 40, 0, 0, [])
    for col in columns:
        new = []
        for cost, task_mask, courier_mask, path in states:
            if task_mask & col['task_mask'] or courier_mask & col['courier_mask']:
                continue
            nt = task_mask | col['task_mask']
            nc = courier_mask | col['courier_mask']
            ncost = cost + col['cost']
            npath = path + [col]
            new.append((ncost, nt, nc, npath))
            total = ncost + 100.0 * (40 - nt.bit_count())
            best_total = best[0] + 100.0 * (40 - best[1].bit_count())
            if total < best_total - 1e-9 or (abs(total - best_total) < 1e-9 and nt.bit_count() > best[1].bit_count()):
                best = (ncost, nt, nc, npath)
        if new:
            states.extend(new)
            states.sort(key=lambda s: (s[0] + 100.0 * (40 - s[1].bit_count()), -s[1].bit_count(), s[2].bit_count()))
            pruned = []
            seen = set()
            for st in states:
                key = (st[1], st[2])
                if key in seen:
                    continue
                seen.add(key)
                pruned.append(st)
                if len(pruned) >= beam_width:
                    break
            states = pruned
    return best


def main():
    columns, sources = collect_columns()
    print('observed columns', len(columns))
    print('task-key count', len({c['task_key'] for c in columns}))
    for width in [1000, 10000, 50000, 200000]:
        best = solve_beam(columns, beam_width=width)
        cost, task_mask, courier_mask, path = best
        total = cost + 100.0 * (40 - task_mask.bit_count())
        missing = [task for task in ALL_TASKS if not (task_mask >> TASK_INDEX[task]) & 1]
        print('\nbeam', width, 'total', round(total, 4), 'group_cost', round(cost, 4), 'covered', task_mask.bit_count(), 'missing', missing, 'groups', len(path), 'couriers', courier_mask.bit_count())
        for col in sorted(path, key=lambda c: c['task_key']):
            print(' ', col['task_key'], list(col['couriers']), col['cost'])


if __name__ == '__main__':
    main()
