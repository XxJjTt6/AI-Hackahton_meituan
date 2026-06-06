#!/usr/bin/env python3
import json, glob, itertools, collections
p='runs/official_submit_20260518_144256_2b381cac.json'
cr=[c for c in json.load(open(p))['result']['case_results'] if c['case_file']=='scarce_couriers_seed401.txt'][0]
print('current scarce score',cr['total_score'])
for d in sorted(cr['detail'], key=lambda x:x['cost']-100*len(x['task_id_list'].split(',')), reverse=True):
    tasks=d['task_id_list'].split(','); net=d['cost']-100*len(tasks)
    print(f"{d['task_id_list']:11s} {d['couriers']} cost={d['cost']:8.4f} p={d['p_complete']:.4f} exp={d['expected_score']:7.3f} net_vs_unserved={net:8.4f}")
print('\nGroups with worst business net are still below unserved penalty except T0001,T0035 slightly saves 92.10 over rejecting both; missing one task penalty makes replacement hard.')
