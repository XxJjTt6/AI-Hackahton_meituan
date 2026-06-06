#!/usr/bin/env python3
import json, math, statistics
from pathlib import Path
ROOT=Path('/Users/比赛/FOR_AutoSolver_706.72')
paths=['runs/official_submit_20260518_144256_2b381cac.json','runs/official_submit_20260517_235832_bce9292a.json','runs/official_submit_20260518_130046_b80309e5.json']
print('Business objective hypothesis: minimize expected platform loss = unserved penalty + expected delivery cost + rider opportunity/over-dispatch cost')
for p in paths:
    d=json.load(open(ROOT/p))
    print('\n###',p,'avg',d['result']['avg_score'],'sha',d['sha256'][:8])
    for cr in d['result']['case_results']:
        if cr['case_file'] not in ('low_willingness_seed501.txt','scarce_couriers_seed401.txt','small_seed100.txt'): continue
        det=cr['detail']; riders=sum(len(x['couriers']) for x in det); tasks=sum(len(x['task_id_list'].split(',')) for x in det)
        pc=sum(x.get('p_complete',0) for x in det); exp=sum(x.get('expected_score',0) for x in det); cost=sum(x.get('cost',0) for x in det)
        opp=riders*2.0  # illustrative opportunity metric, not platform score
        print(f"{cr['case_file']} score={cr['total_score']:.4f} assigned={cr['assigned_count']} un={cr['unassigned_count']} groups={len(det)} riders={riders} task_groups={tasks} sum_p={pc:.2f} exp={exp:.1f} cost={cost:.1f} cost+opp={cost+opp:.1f}")
