#!/usr/bin/env python3
import sys,itertools,time
from pathlib import Path
sys.path.insert(0,'.'); sys.path.insert(0,'runs')
import solver, proxy_eval
text=Path('runs/official_calibrated_low_synth.txt').read_text(); rows,tasks,couriers=proxy_eval.parse(text); tasks=sorted(tasks); T=set(tasks)
base=solver.solve(text); basec=solver._solution_expected_cost(base,rows,T); print('base',round(basec,6))
by={t:[] for t in tasks}
for r in rows:
    if len(r[1])==1: by[r[1][0]].append(r)
opts=[]
for t in tasks:
    arr=[]
    rs=sorted(by[t],key=lambda r:solver._single_expected_cost(r))[:45]
    for a,b in itertools.combinations(rs,2): arr.append((solver._group_expected_cost([a,b],1),t,a[2],b[2]))
    opts.append(sorted(arr,key=lambda x:x[0])[:120])
# Branch order by regret / option scarcity
order=sorted(range(len(tasks)), key=lambda i: opts[i][8][0]-opts[i][0][0] if len(opts[i])>8 else 999, reverse=True)
mins=[opts[i][0][0] for i in order]; suf=[0]*(len(order)+1)
for i in range(len(order)-1,-1,-1): suf[i]=suf[i+1]+mins[i]
best=[basec,None]; cur=[]; nodes=0; deadline=time.monotonic()+25
def dfs(pos,used,cost):
    global nodes
    nodes+=1
    if nodes%200000==0: print('nodes',nodes,'pos',pos,'best',round(best[0],4),'cost',round(cost,2),flush=True)
    if time.monotonic()>deadline: return
    if cost+suf[pos]>=best[0]-1e-9: return
    if pos==len(order): best[0]=cost; best[1]=list(cur); print('improve exact',cost,flush=True); return
    i=order[pos]
    # dynamic feasible sorted; try only those below incumbent margin
    for c,t,a,b in opts[i]:
        if a in used or b in used: continue
        cur.append((t,a,b,c)); dfs(pos+1,used|{a,b},cost+c); cur.pop()
dfs(0,set(),0.0)
print('done nodes',nodes,'best',round(best[0],6),'improved',best[1] is not None)
