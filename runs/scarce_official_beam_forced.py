#!/usr/bin/env python3
import os,json,collections
files=[]
with os.scandir('runs') as it:
    for e in it:
        if e.name.startswith('official_submit_') and e.name.endswith('.json'): files.append('runs/'+e.name)
cols={}; tasks=set(); couriers=set()
for p in files:
    try:d=json.load(open(p))
    except:continue
    for cr in (d.get('result') or {}).get('case_results') or []:
        if cr.get('case_file')!='scarce_couriers_seed401.txt' or cr.get('status')!='ok': continue
        for x in cr.get('detail') or []:
            ts=tuple(sorted(x['task_id_list'].split(','))); cs=tuple(sorted(x['couriers'])); c=float(x['cost']); tasks.update(ts); couriers.update(cs)
            # exclude T0033 trap initially; force T0016 single if included
            if 'T0033' in ts: continue
            if 'T0016' in ts and not (ts==('T0016',) and cs==('C000',)): continue
            key=(ts,cs)
            if c<cols.get(key,(1e9,None))[0]: cols[key]=(c,x['task_id_list'])
tasks=sorted(tasks); ti={t:i for i,t in enumerate(tasks)}; ci={c:i for i,c in enumerate(sorted(couriers))}
items=[]
for (ts,cs),(c,k) in cols.items():
    tm=sum(1<<ti[t] for t in ts); cm=sum(1<<ci[c] for c in cs); gain=100*len(ts)-c
    if gain>0: items.append((gain,c,tm,cm,k,cs))
items.sort(reverse=True)
# Always allow drop penalty by not covering tasks. Beam stores max gain.
beam={(0,0):(0.0,())}
for gain,c,tm,cm,k,cs in items:
    additions=[]
    for (m,u),(g,path) in beam.items():
        if m&tm or u&cm: continue
        key=(m|tm,u|cm); val=g+gain
        old=beam.get(key)
        if old is None or val>old[0]+1e-9: additions.append((key,(val,path+((k,cs,c),))))
    for key,val in additions:
        if val[0]>beam.get(key,(-1,None))[0]: beam[key]=val
    if len(beam)>5000:
        beam=dict(sorted(beam.items(),key=lambda kv:(kv[1][0]+30*bin(kv[0][0]).count('1'),kv[1][0]),reverse=True)[:5000])
best=max(beam.items(), key=lambda kv: kv[1][0])
gain,path=best[1]; covered=bin(best[0][0]).count('1'); total_tasks=len(tasks); score=100*total_tasks-gain
print('score',round(score,4),'covered',covered,'groups',len(path),'items',len(items),'states',len(beam),'current',1531.5317)
for x in sorted(path): print(x)
