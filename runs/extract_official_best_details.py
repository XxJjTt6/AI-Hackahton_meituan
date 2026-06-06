#!/usr/bin/env python3
import json, glob, os
best={}
for fp in glob.glob('runs/official_submit_*.json'):
    try:
        d=json.load(open(fp)); sha=(d.get('sha256') or '')[:8]; res=d.get('result') or {}
    except Exception: continue
    for c in res.get('case_results') or []:
        name=c.get('case_file'); score=c.get('total_score')
        if name is None or score is None: continue
        if name not in best or score<best[name][0]-1e-9:
            best[name]=(score,sha,fp,c)
for name,(score,sha,fp,c) in sorted(best.items()):
    print('\n#',name,score,sha,os.path.basename(fp),'assigned',c.get('assigned_count'),'unassigned',c.get('unassigned_count'))
    for d in c.get('detail',[])[:60]:
        print(d['task_id_list'], ','.join(d['couriers']), 'cost', d['cost'])
