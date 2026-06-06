#!/usr/bin/env python3
import json, sys
files=['runs/official_submit_20260518_175316_f65d16ac.json','runs/official_submit_20260519_005340_8a67c77f.json','runs/official_submit_20260517_235832_bce9292a.json']
for f in files:
    data=json.load(open(f)); print('\nFILE',f)
    for cr in data['result']['case_results']:
        if cr['case_file']=='scarce_couriers_seed401.txt':
            cov=set(); rows=[]
            for d in cr['detail']:
                ts=[x for x in d['task_id_list'].split(',') if x]
                cov.update(ts)
                rows.append((d['cost'],d['task_id_list'],d.get('couriers'),d.get('p_complete'),d.get('expected_score')))
            print('score',cr['total_score'],'n',len(rows),'cov',len(cov),'miss',[f'T{i:04d}' for i in range(40) if f'T{i:04d}' not in cov])
            for r in sorted(rows, reverse=True)[:25]: print(' ',r)
