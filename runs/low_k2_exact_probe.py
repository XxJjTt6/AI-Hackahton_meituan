#!/usr/bin/env python3
import importlib.util, itertools, sys, time, heapq
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
tasks=sorted(tasks); couriers=sorted(couriers); ci={c:i for i,c in enumerate(couriers)}
base=solver.solve(text); base_cost=solver._solution_expected_cost(base,rows,set(tasks))
print('base',base_cost,'kdist',{k:sum(1 for _,ls in base if len(ls)==k) for k in range(1,5)})
by={t:[] for t in tasks}
for r in rows: by[r[0]].append(r)
# DP over tasks, mask couriers, exactly two per task. 60 couriers => too big; use beam with exact pair costs and high width.
states={0:(0.0,())}
for ti,t in enumerate(tasks):
    pairs=[]
    rs=by[t]
    # keep candidate pairs by actual group cost; include top singles cross product enough to capture optimum-like shape
    top=sorted(rs,key=lambda r:solver._group_expected_cost([r],1))[:22]
    for a,b in itertools.combinations(top,2):
        mask=(1<<ci[a[2]])|(1<<ci[b[2]])
        cost=solver._group_expected_cost([a,b],1)
        pairs.append((cost,mask,(a[2],b[2])))
    pairs=sorted(pairs)[:90]
    new={}
    for mask,(cost,path0) in states.items():
        for pc,pm,cs in pairs:
            if mask&pm: continue
            nm=mask|pm; val=cost+pc
            old=new.get(nm)
            if old is None or val<old[0]: new[nm]=(val,path0+((t,cs),))
    if len(new)>8000:
        # lower bound: optimistic remaining best pair ignoring courier conflicts
        rem=tasks[ti+1:]
        lb=sum(min(solver._group_expected_cost(list(p),1) for p in itertools.combinations(sorted(by[rt],key=lambda r:solver._group_expected_cost([r],1))[:14],2)) for rt in rem)
        keep=sorted(new.items(), key=lambda kv:kv[1][0]+lb)[:8000]
        new=dict(keep)
    states=new
    print('task',ti+1,'states',len(states),'best_partial',min(v[0] for v in states.values()), flush=True)
best=min(states.values(), key=lambda x:x[0])
out=[(t,list(cs)) for t,cs in best[1]]
full=solver._solution_expected_cost(out,rows,set(tasks))
print('best_raw',best[0],'full',full,'delta',full-base_cost,'groups',len(out))
for x in out[:10]: print(x)
