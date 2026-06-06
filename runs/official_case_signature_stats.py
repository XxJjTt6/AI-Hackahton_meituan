#!/usr/bin/env python3
import json, glob, os, statistics
for fp in sorted(glob.glob('runs/official_submit_*.json')):
    try:
        d=json.load(open(fp)); res=d.get('result') or {}; sha=(d.get('sha256') or '')[:8]
    except Exception: continue
    if sha!='f65d16ac': continue
    for c in res.get('case_results') or []:
        det=c.get('detail') or []
        ks=[len(x['couriers']) for x in det]
        bundle=sum(1 for x in det if ',' in x['task_id_list'])
        costs=[x['cost'] for x in det]
        print(c['case_file'], 'score', c['total_score'], 'assigned', c['assigned_count'], 'groups', len(det), 'bundle_groups', bundle, 'kdist', {k:ks.count(k) for k in sorted(set(ks))}, 'cost_mean', round(statistics.mean(costs),4), 'cost_minmax', (round(min(costs),4),round(max(costs),4)))
