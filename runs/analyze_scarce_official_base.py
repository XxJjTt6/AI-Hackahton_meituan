#!/usr/bin/env python3
import json
p='runs/official_submit_20260520_132026_70222083.json'
d=json.load(open(p))['result']['case_results']
case=[c for c in d if c['case_file']=='scarce_couriers_seed401.txt'][0]
used=set(); covered=set(); cost=0
for x in case['detail']:
    used.update(x['couriers']); covered.update(x['task_id_list'].split(',')); cost+=x['cost']
print('total',case['total_score'],'detail_sum',cost,'penalty',case['total_score']-cost)
print('used',len(used),sorted(used))
print('unused',len(set(f'C{i:03d}' for i in range(40))-used),sorted(set(f'C{i:03d}' for i in range(40))-used))
print('covered',len(covered),'missing',sorted(set(f'T{i:04d}' for i in range(40))-covered))
for x in sorted(case['detail'],key=lambda z:z['cost'],reverse=True):print(x['cost'],x['task_id_list'],x['couriers'])
