#!/usr/bin/env python3
import json, glob, itertools, os, math
from pathlib import Path
ROOT=Path('/Users/比赛/FOR_AutoSolver_706.72')
cols={}
submits=[]
for path in glob.glob(str(ROOT/'runs'/'official_submit_*.json')):
    try: data=json.load(open(path))
    except Exception: continue
    res=data.get('result') or {}; avg=res.get('avg_score')
    for cr in res.get('case_results',[]):
        if cr.get('case_file')!='scarce_couriers_seed401.txt' or cr.get('status')!='ok': continue
        sol=[]
        for d in cr.get('detail',[]):
            tasks=tuple(d['task_id_list'].split(',')); cour=tuple(d['couriers'])
            mask=0
            for t in tasks: mask|=1<<int(t[1:])
            cmask=0
            for c in cour: cmask|=1<<int(c[1:])
            key=(tasks,cour)
            cost=float(d['cost']); p=float(d.get('p_complete',0)); exp=float(d.get('expected_score',0))
            old=cols.get(key)
            if old is None or cost<old['cost']: cols[key]={'tasks':tasks,'cour':cour,'mask':mask,'cmask':cmask,'cost':cost,'p':p,'exp':exp,'sources':[]}
            cols[key]['sources'].append((os.path.basename(path),avg,cr.get('total_score')))
            sol.append(key)
        submits.append((cr.get('total_score'),avg,os.path.basename(path),sol))
print('submits',len(submits),'unique_cols',len(cols))
for score,avg,path,sol in sorted(submits)[:12]:
    print('submit',score,'avg',avg,path,'groups',len(sol),'assigned',sum(len(k[0]) for k in sol))
# exact DP over historical columns + unassigned penalty 100/task, courier disjoint, task disjoint.
allcols=list(cols.values())
# keep useful columns with cost < 100*covered+50, plus known all best groups
allcols=[c for c in allcols if c['cost'] < 100*len(c['tasks'])+80]
allcols.sort(key=lambda c:(c['cost']-100*len(c['tasks']), c['cost']))
print('filtered_cols',len(allcols))
# beam DP by task/courier masks, minimize cost + 100 unassigned at end.
states={(0,0):(0.0,())}
def pop(x): return bin(x).count('1')
for idx,c in enumerate(allcols):
    new=dict(states)
    for (tm,cm),(cost,path) in list(states.items()):
        if tm & c['mask'] or cm & c['cmask']: continue
        nt=tm|c['mask']; nc=cm|c['cmask']; val=cost+c['cost']
        old=new.get((nt,nc))
        if old is None or val<old[0]-1e-9: new[(nt,nc)]=(val,path+(idx,))
    if len(new)>120000:
        # prune by total objective lower proxy and coverage
        items=sorted(new.items(), key=lambda kv:(kv[1][0]+100*(40-pop(kv[0][0])), -pop(kv[0][0]), kv[1][0]))[:70000]
        new=dict(items)
    states=new
best=None
for (tm,cm),(cost,path) in states.items():
    obj=cost+100*(40-pop(tm))
    cov=pop(tm)
    if best is None or obj<best[0]-1e-9: best=(obj,cov,cost,path,tm,cm)
print('best_obj',best[0],'cov',best[1],'rawcost',best[2],'groups',len(best[3]))
for i in best[3]:
    c=allcols[i]
    print(','.join(c['tasks']), list(c['cour']), 'cost',c['cost'],'p',c['p'])
