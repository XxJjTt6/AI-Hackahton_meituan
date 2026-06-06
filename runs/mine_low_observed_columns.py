#!/usr/bin/env python3
import os,json,collections,time
files=[]
with os.scandir('runs') as it:
    for e in it:
        n=e.name
        if n.startswith('official_submit_') and n.endswith('.json'):
            files.append('runs/'+n)
cols=collections.defaultdict(dict)
solutions=[]
for p in files:
    try: data=json.load(open(p))
    except Exception: continue
    sha=(data.get('sha256') or '')[:8]
    for cr in (data.get('result') or {}).get('case_results') or []:
        if cr.get('case_file')!='low_willingness_seed501.txt' or cr.get('status')!='ok': continue
        sol=[]
        for d in cr.get('detail') or []:
            k=d['task_id_list']; cs=tuple(d['couriers']); cost=float(d['cost'])
            cols[k][cs]=min(cost, cols[k].get(cs, 1e9)); sol.append((k,cs,cost))
        solutions.append((cr['total_score'],sha,sol))
print('solutions',len(solutions),'unique cols/tasks',sum(len(v) for v in cols.values()),len(cols))
for k in sorted(cols):
    arr=sorted((c,cs) for cs,c in cols[k].items())
    print(k,'n',len(arr),'best',arr[:4])
# DFS observed columns exact complete no courier overlap
order=sorted(cols, key=lambda k: len(cols[k]))
best=[1e9,None]; cur=[]; mincost=[]
for k in order: mincost.append(min(cols[k].values()))
suf=[0]*(len(order)+1)
for i in range(len(order)-1,-1,-1): suf[i]=suf[i+1]+mincost[i]
def dfs(i, used, cost):
    if cost+suf[i]>=best[0]-1e-9: return
    if i==len(order): best[0]=cost; best[1]=list(cur); return
    k=order[i]
    for cs,c in sorted(cols[k].items(), key=lambda x:x[1]):
        if any(x in used for x in cs): continue
        cur.append((k,cs,c)); dfs(i+1, used|set(cs), cost+c); cur.pop()
dfs(0,set(),0.0)
print('best observed exact',best[0], 'current official', min(s[0] for s in solutions))
if best[1]:
    print('cols')
    for x in sorted(best[1]): print(x)
