#!/usr/bin/env python3
import os,json,collections
files=[]
with os.scandir('runs') as it:
    for e in it:
        n=e.name
        if n.startswith('official_submit_') and n.endswith('.json'):
            files.append('runs/'+n)
cols={}; tasks=set()
for p in files:
    try: data=json.load(open(p))
    except Exception: continue
    sha=(data.get('sha256') or '')[:8]
    for cr in (data.get('result') or {}).get('case_results') or []:
        if cr.get('case_file')!='scarce_couriers_seed401.txt' or cr.get('status')!='ok': continue
        for d in cr.get('detail') or []:
            ts=tuple(sorted(d['task_id_list'].split(','))); cs=tuple(d['couriers']); c=float(d['cost']); tasks.update(ts)
            key=(ts,tuple(sorted(cs)))
            if c<cols.get(key,(1e9,None,None))[0]: cols[key]=(c,d['task_id_list'],cs)
print('cols',len(cols),'tasks',len(tasks))
for (ts,css),(c,k,cs) in sorted(cols.items(), key=lambda x:x[1][0])[:80]: print(round(c,4),k,cs)
# exact pack allowing drop penalty 100 per task
tasks=sorted(tasks); ti={t:i for i,t in enumerate(tasks)}; arr=[]
for (ts,css),(c,k,cs) in cols.items():
    tm=sum(1<<ti[t] for t in ts); cm=frozenset(cs); arr.append((tm,cm,c,k,cs,ts))
bytask=[[] for _ in tasks]
for x in arr:
    for t in x[5]: bytask[ti[t]].append(x)
best=[1e9,None]; cur=[]
def dfs(mask,used,cost):
    # penalty for uncovered lower bound zero; incumbent includes final penalty at leaves only
    if cost>=best[0]: return
    # choose an uncovered task, but allow dropping it
    if mask==(1<<len(tasks))-1:
        if cost<best[0]: best[0]=cost; best[1]=list(cur); print('best',round(cost,4),flush=True)
        return
    # current cost + if drop all remaining
    drop_cost=cost+100*(len(tasks)-bin(mask).count("1"))
    if drop_cost<best[0]:
        best[0]=drop_cost; best[1]=list(cur); print('best_drop',round(drop_cost,4),flush=True)
    ii=None; choices=None
    for i in range(len(tasks)):
        if mask>>i&1: continue
        ch=[x for x in bytask[i] if not (x[0]&mask) and not (x[1]&used)]
        if choices is None or len(ch)<len(choices): ii=i; choices=ch
    # drop ii
    dfs(mask| (1<<ii), used, cost+100)
    for tm,cm,c,k,cs,ts in sorted(choices,key=lambda x:x[2]-100*len(x[5])):
        cur.append((k,cs,c)); dfs(mask|tm, used|cm, cost+c); cur.pop()
dfs(0,frozenset(),0.0)
print('best',best[0])
if best[1]:
    for x in sorted(best[1]): print(x)
