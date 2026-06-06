#!/usr/bin/env python3
import json, glob, os, statistics
from pathlib import Path
ROOT=Path('/Users/比赛/FOR_AutoSolver_706.72')
BASE=ROOT/'runs/official_submit_20260517_024422_812ea145.json'

def load_official_cases(path=BASE):
    data=json.load(open(path))['result']['case_results']
    return {c['case_file']:c for c in data}

def official_signature(case):
    details=case.get('detail',[])
    return {
        'score':case['total_score'],
        'assigned':case.get('assigned_count'),
        'unassigned':case.get('unassigned_count'),
        'groups':len(details),
        'avg_cost':sum(d['cost'] for d in details)/max(1,len(details)),
        'max_cost':max((d['cost'] for d in details), default=0),
        'k_hist':hist(len(d['couriers']) for d in details),
        'bundle_hist':hist(len(d['task_id_list'].split(',')) for d in details),
    }

def hist(vals):
    h={}
    for v in vals:h[v]=h.get(v,0)+1
    return dict(sorted(h.items()))

if __name__=='__main__':
    cases=load_official_cases()
    for name in sorted(cases):
        print(name, official_signature(cases[name]))
