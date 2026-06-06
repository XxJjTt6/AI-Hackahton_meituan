#!/usr/bin/env python3
import json, math
p='runs/official_submit_20260519_171310_41db4b34.json'
cr=next(x for x in json.load(open(p))['result']['case_results'] if x['case_file']=='low_willingness_seed501.txt')
ds=cr['detail']
print('score',cr['total_score'],'groups',len(ds))
print('avg group cost',sum(d['cost'] for d in ds)/len(ds))
print('needed for 700 if only low improves: target low <=',cr['total_score']-64.264)
print('current reductions sum',sum(100-len(d['task_id_list'].split(','))*0 - d['cost'] for d in ds))
print('top bad by cost:')
for d in sorted(ds,key=lambda x:x['cost'],reverse=True):
    print(d['task_id_list'],d['couriers'],'cost',d['cost'],'p',d['p_complete'],'expected',d['expected_score'])
