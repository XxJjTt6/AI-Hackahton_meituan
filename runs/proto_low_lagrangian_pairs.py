#!/usr/bin/env python3
import sys,itertools,math,random,time
from pathlib import Path
sys.path.insert(0,'.'); sys.path.insert(0,'runs')
import solver, proxy_eval
text=Path(sys.argv[1] if len(sys.argv)>1 else 'runs/official_calibrated_low_synth.txt').read_text()
rows,tasks,couriers=proxy_eval.parse(text); tasks=sorted(tasks); couriers=sorted(couriers); T=set(tasks)
lut={(r[1][0],r[2]):r for r in rows if len(r[1])==1}
by={t:[] for t in tasks}
for r in rows:
    if len(r[1])==1: by[r[1][0]].append(r)
for t in tasks: by[t]=sorted(by[t],key=lambda r: solver._single_expected_cost(r))[:40]
base=solver.solve(text); base_cost=solver._solution_expected_cost(base,rows,T)
print('base',round(base_cost,6),{k:sum(len(cs)==k for _,cs in base) for k in range(1,5)})
# precompute pair options per task
opts={}
for t in tasks:
    arr=[]; rs=by[t]
    for a,b in itertools.combinations(rs,2):
        c=solver._group_expected_cost([a,b],1); arr.append((c,a[2],b[2]))
    opts[t]=sorted(arr,key=lambda x:x[0])[:260]

def repair(chosen):
    # chosen: t -> (cost,c1,c2), may conflict. Resolve by processing high regret tasks first.
    used=set(); sol={}; conflict_tasks=[]
    # compute regret under raw costs
    order=[]
    for t,ch in chosen.items():
        c1,c2=ch[1],ch[2]
        raw=ch[0]
        second=next((c for c,a,b in opts[t] if {a,b}!={c1,c2}), raw+50)
        order.append((second-raw, -raw, t))
    for _,_,t in sorted(order, reverse=True):
        c,a,b=chosen[t]
        if a not in used and b not in used:
            sol[t]=(a,b); used.add(a); used.add(b)
        else: conflict_tasks.append(t)
    # fill conflicts with best feasible pair, then if impossible leave penalty
    for t in conflict_tasks:
        best=None
        for c,a,b in opts[t]:
            if a not in used and b not in used:
                best=(c,a,b); break
        if best:
            _,a,b=best; sol[t]=(a,b); used.add(a); used.add(b)
    out=[(t,list(sol[t])) for t in tasks if t in sol]
    return out

best=(base_cost,base); price={c:0.0 for c in couriers}; rng=random.Random(19)
start=time.monotonic()
for it in range(220):
    chosen={}; load={c:0 for c in couriers}
    for t in tasks:
        # choose by reduced cost
        c,a,b=min(opts[t], key=lambda x:x[0]+price[x[1]]+price[x[2]])
        chosen[t]=(c,a,b); load[a]+=1; load[b]+=1
    out=repair(chosen); val=solver._solution_expected_cost(out,rows,T)
    if val<best[0]-1e-9:
        best=(val,out); print('improve',it,round(val,6),{k:sum(len(cs)==k for _,cs in out) for k in range(1,4)},flush=True)
    # subgradient: each courier should load<=1; raise overloaded, slightly lower unused
    step=12.0/math.sqrt(it+1)
    for c in couriers:
        price[c]=max(-8.0,min(80.0,price[c]+step*(load[c]-1)))
print('final',round(best[0],6),'time',round(time.monotonic()-start,2),'sig',hash(tuple((k,tuple(cs)) for k,cs in best[1])))
for x in best[1][:10]: print(' ',x)
