#!/usr/bin/env python3
import os,json,collections
files=[]
with os.scandir('runs') as it:
    for e in it:
        n=e.name
        if n.startswith('official_submit_') and n.endswith('.json'):
            files.append('runs/'+n)
cols=[]; tasks=set()
for p in files:
    try: data=json.load(open(p))
    except Exception: continue
    for cr in (data.get('result') or {}).get('case_results') or []:
        if cr.get('case_file')!='low_willingness_seed501.txt' or cr.get('status')!='ok': continue
        for d in cr.get('detail') or []:
            ts=tuple(d['task_id_list'].split(',')); cs=tuple(d['couriers']); cost=float(d['cost'])
            tasks.update(ts); cols.append((ts,cs,cost,d['task_id_list']))
# dedupe min cost per (tasks,couriers unordered)
best={}
for ts,cs,c,k in cols:
    key=(tuple(sorted(ts)),tuple(sorted(cs)))
    if c<best.get(key,(1e9,None))[0]: best[key]=(c,k,cs)
cols=[]
for (ts,css),(c,k,cs) in best.items(): cols.append((ts,cs,c,k))
tasks=sorted(tasks); ti={t:i for i,t in enumerate(tasks)}
for idx,(ts,cs,c,k) in enumerate(cols):
    pass
bytask=[[] for _ in tasks]
for col in cols:
    ts,cs,c,k=col; tm=sum(1<<ti[t] for t in ts)
    for t in ts: bytask[ti[t]].append((tm,set(cs),c,k,cs,ts))
mins=[min([100]+[x[2]/len(x[5]) for x in bytask[i]]) for i in range(len(tasks))]
suf=[0]*(len(tasks)+1)
for i in range(len(tasks)-1,-1,-1): suf[i]=suf[i+1]+mins[i]
bestv=[1e9,None]; cur=[]
def dfs(mask,used,cost):
    # lower bound by uncovered tasks as best per-task cost (weak)
    lb=0
    for i in range(len(tasks)):
        if not (mask>>i)&1: lb+=mins[i]
    if cost+lb>=bestv[0]-1e-9: return
    if mask==(1<<len(tasks))-1:
        bestv[0]=cost; bestv[1]=list(cur); print('best',round(cost,4),flush=True); return
    # choose uncovered with fewest feasible options
    choices=None; ii=None
    for i in range(len(tasks)):
        if (mask>>i)&1: continue
        ch=[]
        for x in bytask[i]:
            tm,cs,c,k,cst,ts=x
            if tm&mask: continue
            if cs&used: continue
            ch.append(x)
        ch.append((1<<i,set(),100,tasks[i],(),(tasks[i],)))
        if choices is None or len(ch)<len(choices): choices=ch; ii=i
    for tm,cs,c,k,cst,ts in sorted(choices,key=lambda x:x[2]):
        cur.append((k,cst,c,ts)); dfs(mask|tm, used|cs, cost+c); cur.pop()
dfs(0,set(),0.0)
print('tasks',len(tasks),'cols',len(cols),'best',bestv[0])
if bestv[1]:
    for x in sorted(bestv[1]): print(x)
