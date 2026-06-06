#!/usr/bin/env python3
"""Audit official best result structures and summarize remaining leverage.
Does not submit. Reads saved judge JSON only.
"""
from __future__ import annotations
import json, pathlib, collections, statistics as stats
ROOT=pathlib.Path(__file__).resolve().parents[2]
BEST=ROOT/'runs/official_submit_20260522_034329_7046558e.json'

def case_summary(case):
    detail=case['detail']
    groups=len(detail)
    task_lens=[len(d['task_id_list'].split(',')) for d in detail]
    k_lens=[len(d['couriers']) for d in detail]
    costs=[float(d['cost']) for d in detail]
    p=[float(d['p_complete']) for d in detail]
    bundle=sum(1 for x in task_lens if x>1)
    assigned=case.get('assigned_count')
    unassigned=case.get('unassigned_count')
    high=sorted(detail,key=lambda d:float(d['cost']),reverse=True)[:5]
    return {
        'case':case['case_file'],
        'score':float(case['total_score']),
        'time_ms':case['elapsed_ms'],
        'groups':groups,
        'assigned':assigned,
        'unassigned':unassigned,
        'bundle_groups':bundle,
        'task_lens':dict(collections.Counter(task_lens)),
        'courier_lens':dict(collections.Counter(k_lens)),
        'avg_group_cost':sum(costs)/groups,
        'max_group_cost':max(costs),
        'min_p':min(p),
        'low_p_groups':sum(1 for x in p if x<0.7),
        'top_cost_groups':[(d['task_id_list'],len(d['couriers']),d['p_complete'],d['cost']) for d in high],
    }

def main():
    r=json.load(open(BEST))['result']
    print('avg',r['avg_score'],'cases',r['case_count'])
    rows=[case_summary(c) for c in r['case_results']]
    for x in sorted(rows,key=lambda z:z['score'],reverse=True):
        print('\nCASE',x['case'])
        for k in ['score','time_ms','groups','assigned','unassigned','bundle_groups','task_lens','courier_lens','avg_group_cost','max_group_cost','min_p','low_p_groups']:
            print(f'  {k}: {x[k]}')
        print('  top_cost_groups:')
        for g in x['top_cost_groups']: print('   ',g)
    print('\nLeverage estimate: one avg point requires 10 total score reduction in any case.')
    print('The only cases with obvious >10 single-case slack by structure are low501 and scarce401; normal cases need new hidden candidate rows or exact cache-level swaps.')
if __name__=='__main__': main()
