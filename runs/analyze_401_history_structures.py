#!/usr/bin/env python3
from __future__ import annotations

import json
import glob
import os
from collections import defaultdict

BEST_PATH = 'runs/official_submit_20260520_132026_70222083.json'
CASE = 'scarce_couriers_seed401.txt'


def case_result(path):
    try:
        data = json.load(open(path))
        result = data.get('result') or {}
        for case in result.get('case_results', []):
            if case.get('case_file') == CASE:
                return data, result, case
    except Exception:
        return None
    return None


def group_map(case):
    return {g['task_id_list']: g for g in case.get('detail', [])}


def covered(case):
    tasks = set()
    for g in case.get('detail', []):
        tasks.update(g['task_id_list'].split(','))
    return tasks


def main():
    best_data, best_result, best_case = case_result(BEST_PATH)
    best_groups = group_map(best_case)
    all_tasks = {f'T{i:04d}' for i in range(best_case['total_tasks'])}
    rows = []
    for path in glob.glob('runs/official_submit_*.json'):
        item = case_result(path)
        if not item:
            continue
        data, result, case = item
        groups = group_map(case)
        add = sorted(k for k in groups if k not in best_groups)
        rem = sorted(k for k in best_groups if k not in groups)
        common_changed = []
        for k in sorted(set(groups) & set(best_groups)):
            if groups[k]['couriers'] != best_groups[k]['couriers'] or abs(groups[k]['cost'] - best_groups[k]['cost']) > 1e-6:
                common_changed.append(k)
        rows.append({
            'path': path,
            'sha': data.get('sha256', '')[:8],
            'note': data.get('note', '')[:100],
            'avg': result.get('avg_score'),
            'score': case.get('total_score'),
            'assigned': case.get('assigned_count'),
            'missing': sorted(all_tasks - covered(case)),
            'added': add,
            'removed': rem,
            'changed': common_changed,
            'groups': groups,
        })
    rows.sort(key=lambda r: (r['score'], r['path']))
    print('BEST', best_case['total_score'], 'missing', sorted(all_tasks - covered(best_case)))
    print('best groups')
    for k, g in sorted(best_groups.items()):
        print(' ', k, g['couriers'], g['cost'])
    print('\nNEAR STRUCTURES')
    for r in rows:
        if r['score'] == best_case['total_score']:
            continue
        if r['score'] <= 1589.34:
            print('\n', r['score'], os.path.basename(r['path']), r['sha'], 'assigned', r['assigned'], 'missing', r['missing'])
            print(' note', r['note'])
            print(' added')
            for k in r['added']:
                g = r['groups'][k]
                print('  +', k, g['couriers'], g['cost'])
            print(' removed')
            for k in r['removed']:
                g = best_groups[k]
                print('  -', k, g['couriers'], g['cost'])
            if r['changed']:
                print(' changed', r['changed'])
    # Frequency of added/removed groups among regressions.
    add_freq = defaultdict(int)
    rem_freq = defaultdict(int)
    for r in rows:
        if r['score'] != best_case['total_score']:
            for k in r['added']:
                add_freq[k] += 1
            for k in r['removed']:
                rem_freq[k] += 1
    print('\nADD FREQ')
    for k, n in sorted(add_freq.items(), key=lambda x: (-x[1], x[0]))[:30]:
        print(n, k)
    print('\nREMOVE FREQ')
    for k, n in sorted(rem_freq.items(), key=lambda x: (-x[1], x[0]))[:30]:
        print(n, k)


if __name__ == '__main__':
    main()
