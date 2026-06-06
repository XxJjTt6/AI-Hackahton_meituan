#!/usr/bin/env python3
import importlib.util, itertools, sys, time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('solver', ROOT/'solver.py')
solver=importlib.util.module_from_spec(spec); spec.loader.exec_module(solver)
path=Path(sys.argv[1]) if len(sys.argv)>1 else ROOT/'runs/official_calibrated_low_synth.txt'
text=path.read_text(); lines=text.strip().splitlines(); start=1 if lines and lines[0].startswith('task_id_list') else 0
rows=[]; tasks=set(); couriers=set()
for idx,s in enumerate(lines[start:]):
    a=s.split('\t')
    if len(a)<4: continue
    k,c,score,will=a[:4]
    if ',' in k: continue
    r=(k,(k,),c,float(score),float(will),idx)
    rows.append(r); tasks.add(k); couriers.add(c)
tasks=sorted(tasks); couriers=sorted(couriers)
base=solver.solve(text); incumbent=solver._solution_expected_cost(base,rows,set(tasks)); best=(incumbent,base)
print('incumbent',incumbent, flush=True)
by={t:[] for t in tasks}
for r in rows: by[r[0]].append(r)
opts={}
for t,rs in by.items():
    pool=[]; seen=set()
    for key in [lambda r:solver._group_expected_cost([r],1), lambda r:(-r[4],r[3]), lambda r:(r[3],-r[4])]:
        for r in sorted(rs,key=key)[:18]:
            if r[2] not in seen: seen.add(r[2]); pool.append(r)
    pairs=[]
    for a,b in itertools.combinations(pool,2):
        c=solver._group_expected_cost([a,b],1)
        pairs.append((c,(a[2],b[2]),(a,b)))
    pairs=sorted(pairs)[:120]
    opts[t]=pairs
# order by constrained/options and cheapness gap; start with tasks whose good pairs use scarce couriers heavily
order=sorted(tasks,key=lambda t:(len({c for _,cs,_ in opts[t][:35] for c in cs}), min(c for c,_,_ in opts[t])))
print('order',order, flush=True)
# suffix optimistic lower bound ignoring conflicts
mincost={t:min(c for c,_,_ in opts[t]) for t in tasks}
suffix=[0]*(len(order)+1)
for i in range(len(order)-1,-1,-1): suffix[i]=suffix[i+1]+mincost[order[i]]
nodes=0; start_time=time.time(); deadline=start_time+20
best_path=[]
def dfs(i,used,cost,path0):
    global nodes,best,best_path
    nodes+=1
    if nodes%200000==0: print('nodes',nodes,'i',i,'cost',cost,'best',best[0],'elapsed',round(time.time()-start_time,1), flush=True)
    if time.time()>deadline: return
    if cost+suffix[i]>=best[0]-1e-9: return
    if i==len(order):
        out=[(t,list(cs)) for t,cs in sorted(path0)]
        full=solver._solution_expected_cost(out,rows,set(tasks))
        if full<best[0]:
            best=(full,out); best_path=list(path0); print('NEW',full,'nodes',nodes,'elapsed',round(time.time()-start_time,2), flush=True)
        return
    t=order[i]
    # dynamic option ordering: prefer feasible and lower cost; cap branches adaptively
    branch=0
    for c,cs,comb in opts[t]:
        if cs[0] in used or cs[1] in used: continue
        branch+=1
        # deeper tasks need enough unused couriers for remaining exactly 2 each
        if len(couriers)-len(used)-2 < 2*(len(order)-i-1): continue
        dfs(i+1, used|set(cs), cost+c, path0+[(t,cs)])
        if branch>=70: break
        if time.time()>deadline: break

dfs(0,set(),0.0,[])
print('done nodes',nodes,'best',best[0],'delta',best[0]-incumbent)
for x in best[1][:10]: print(x)
