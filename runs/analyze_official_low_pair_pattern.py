#!/usr/bin/env python3
import json,statistics,math
f='runs/official_submit_20260518_175316_f65d16ac.json'
data=json.load(open(f))
for cr in data['result']['case_results']:
    if cr['case_file']=='low_willingness_seed501.txt': ds=cr['detail']; break
print('task c1 c2 sum diff cost p score')
for d in ds:
    c=[int(x[1:]) for x in d['couriers']]
    print(d['task_id_list'],c[0],c[1],sum(c),abs(c[0]-c[1]),d['cost'],d['p_complete'],d['expected_score'])
print('courier used sorted',sorted(x for d in ds for x in d['couriers']))
print('pairs by task index:')
for d in ds:
    t=int(d['task_id_list'][1:]); c=[int(x[1:]) for x in d['couriers']]
    print(t,c)
