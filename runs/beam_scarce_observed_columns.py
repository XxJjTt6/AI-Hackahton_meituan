#!/usr/bin/env python3
import os,json
files=[]
with os.scandir('runs') as it:
    for e in it:
        n=e.name
        if n.startswith('official_submit_') and n.endswith('.json'):
            files.append('runs/'+n)
cols={}; tasks=set(); couriers=set()
for p in files:
    try: data=json.load(open(p))
    except Exception: continue
    for cr in (data.get('result') or {}).get('case_results') or []:
        if cr.get('case_file')!='scarce_couriers_seed401.txt' or cr.get('status')!='ok': continue
        for d in cr.get('detail') or []:
            ts=tuple(sorted(d['task_id_list'].split(','))); cs=tuple(sorted(d['couriers'])); c=float(d['cost']); tasks.update(ts); couriers.update(cs)
            key=(ts,cs)
            if c<cols.get(key,(1e9,None))[0]: cols[key]=(c,d['task_id_list'])
tasks=sorted(tasks); ti={t:i for i,t in enumerate(tasks)}; ci={c:i for i,c in enumerate(sorted(couriers))}
items=[]
for (ts,cs),(c,k) in cols.items():
    tm=sum(1<<ti[t] for t in ts); cm=sum(1<<ci[c] for c in cs); gain=100*len(ts)-c
    if gain>0: items.append((gain,c,tm,cm,k,cs))
items.sort(reverse=True)
beam={(0,0):(0.0,())}
for gain,c,tm,cm,k,cs in items:
    new=dict(beam)
    for (m,u),(g,path) in list(beam.items()):
        if m&tm or u&cm: continue
        key=(m|tm,u|cm); val=g+gain
        if val>new.get(key,(-1,None))[0]: new[key]=(val,path+((k,cs,c),))
    if len(new)>2000:
        keep=sorted(new.items(), key=lambda kv:(kv[1][0]+2*bin(kv[0][0]).count('1'), kv[1][0]), reverse=True)[:2000]
        beam=dict(keep)
    else: beam=new
best=max(beam.items(), key=lambda kv: kv[1][0])
gain,path=best[1]; covered=bin(best[0][0]).count('1'); score=100*len(tasks)-gain
print('observed_beam_score',round(score,4),'gain',round(gain,4),'covered',covered,'groups',len(path),'current',1531.5317)
for x in sorted(path): print(x)
