#!/usr/bin/env python3
import json, glob, os, statistics
BEST='runs/official_submit_20260518_175316_f65d16ac.json'
TRUE40={f'T{i:04d}' for i in range(40)}

def load_case(path, case):
    data=json.load(open(path))
    return next(c for c in data['result']['case_results'] if c['case_file']==case)

def print_case(case):
    cr=load_case(BEST, case)
    print('\nCASE', case, 'score', cr['total_score'], 'assigned', cr['assigned_count'], 'missing', sorted({f'T{i:04d}' for i in range(cr['total_tasks'])} - {t for g in cr['detail'] for t in g['task_id_list'].split(',')}))
    rows=[]
    for g in cr['detail']:
        tasks=g['task_id_list'].split(',')
        save=100*len(tasks)-g['cost']
        rows.append((save, g['cost']/len(tasks), g['task_id_list'], g['couriers'], g['cost'], g['p_complete'], g['expected_score']))
    for save, per, key, cs, cost, p, exp in sorted(rows)[:12]:
        print(f' low_margin save={save:8.4f} per={per:7.3f} key={key:15s} c={cs} cost={cost:8.4f} p={p:.4f} exp={exp:8.3f}')
    for save, per, key, cs, cost, p, exp in sorted(rows, reverse=True)[:5]:
        print(f' high_margin save={save:8.4f} per={per:7.3f} key={key:15s} c={cs}')

for case in ['scarce_couriers_seed401.txt','low_willingness_seed501.txt','large_seed301.txt','large_seed302.txt','medium_seed201.txt']:
    print_case(case)
