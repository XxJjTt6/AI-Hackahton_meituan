#!/usr/bin/env python3
# Mine public scarce pairing patterns and compare to official scarce pairing distances; no submit, research only.
import sys, itertools, json
from pathlib import Path
sys.path.insert(0,'.'); sys.path.insert(0,'runs')
import solver, proxy_eval
text=proxy_eval.make_scarce(); rows,tasks,couriers=proxy_eval.parse(text); T=set(tasks)
# Build best single-courier two-task bundles in public scarce.
arr=[]
for r in rows:
    if len(r[1])==2:
        cost=solver._group_expected_cost([r],2); arr.append((cost,r[0],r[2]))
arr=sorted(arr)[:30]
print('top public scarce bundles')
for x in arr[:20]: print(x)
# Official worst pairs for contrast.
cr=next(c for c in json.load(open('runs/official_submit_20260519_171310_41db4b34.json'))['result']['case_results'] if c['case_file']=='scarce_couriers_seed401.txt')
print('\nofficial scarce worst')
for d in sorted(cr['detail'], key=lambda d:d['cost'], reverse=True)[:10]: print(d['cost'],d['task_id_list'],d['couriers'])
