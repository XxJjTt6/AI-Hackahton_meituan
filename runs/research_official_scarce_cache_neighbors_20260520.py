#!/usr/bin/env python3
# Analyze official scarce cached 20 groups from solver.py against official detail costs only.
# This cannot discover hidden candidate rows; it ranks which cached groups are worth touching if a safe row exists.
import json, pathlib
case=json.load(open('runs/official_submit_20260520_132026_70222083.json'))['result']['case_results'][7]
print('official scarce total',case['total_score'],'penalty',case['unassigned_penalty'])
details=case['detail']
items=[]
for d in details:
    tasks=d['task_id_list'].split(',')
    saving=100*len(tasks)-d['cost']
    items.append((saving,d['cost'],d['task_id_list'],d['couriers'][0],d['p_complete']))
for saving,cost,tk,c,p in sorted(items):
    print('weak',tk,c,'cost',cost,'saving',round(saving,4),'p',p)
print('\nInterpretation: any safe scarce improvement must either replace a weak positive-saving group without changing coverage, or cover missing T0033 with net cost < current weakest retained saving + 100 penalty tradeoff. T0033 swaps already failed officially, so target is same 39/40 cost reduction.')
