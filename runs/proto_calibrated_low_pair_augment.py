#!/usr/bin/env python3
import sys,itertools,time,random
from pathlib import Path
sys.path.insert(0,'.'); sys.path.insert(0,'runs')
import solver, proxy_eval
text=Path('runs/official_calibrated_low_synth.txt').read_text(); rows,tasks,couriers=proxy_eval.parse(text); T=set(tasks)
lut={(r[0],r[2]):r for r in rows}
base=solver.solve(text)
sol={k:tuple(cs) for k,cs in base}; used={c for cs in sol.values() for c in cs}
def sc(s): return sum(solver._group_expected_cost([lut[(t,c)] for c in cs],1) for t,cs in s.items())+100*(len(T)-len(s))
print('base',round(sc(sol),6))
by={t:[] for t in tasks}
for r in rows:
    if len(r[1])==1: by[r[1][0]].append(r)
pairs={}
for t in tasks:
    arr=[]
    rs=sorted(by[t], key=lambda r: solver._single_expected_cost(r))[:32]
    for a,b in itertools.combinations(rs,2):
        c=solver._group_expected_cost([a,b],1); arr.append((c,(a[2],b[2])))
    pairs[t]=sorted(arr,key=lambda x:x[0])[:80]
start=time.monotonic(); improved=True; it=0
while improved and time.monotonic()-start<25:
    improved=False; it+=1
    task_order=sorted(tasks,key=lambda t: solver._group_expected_cost([lut[(t,c)] for c in sol[t]],1), reverse=True)
    for win in [3,4,5,6]:
        for subset in itertools.combinations(task_order[:14],win):
            outside={c for t,cs in sol.items() if t not in subset for c in cs}
            old=sum(solver._group_expected_cost([lut[(t,c)] for c in sol[t]],1) for t in subset)
            best=[old,None]; cur=[]
            order=sorted(subset,key=lambda t: len([p for p in pairs[t] if not (set(p[1])&outside)]))
            mins=[min([100]+[c for c,cs in pairs[t] if not(set(cs)&outside)]) for t in order]
            suf=[0]*(len(order)+1)
            for i in range(len(order)-1,-1,-1): suf[i]=suf[i+1]+mins[i]
            def dfs(i,u,cost):
                if cost+suf[i]>=best[0]-1e-9: return
                if i==len(order): best[0]=cost; best[1]=list(cur); return
                t=order[i]
                for c,cs in pairs[t]:
                    ss=set(cs)
                    if ss&outside or ss&u: continue
                    cur.append((t,cs)); dfs(i+1,u|ss,cost+c); cur.pop()
            dfs(0,set(),0)
            if best[1] and best[0]<old-1e-9:
                for t,cs in best[1]: sol[t]=cs
                print('improve',it,win,round(sc(sol),6),flush=True); improved=True; break
        if improved: break
        if time.monotonic()-start>25: break
print('final',round(sc(sol),6),'time',round(time.monotonic()-start,2))
