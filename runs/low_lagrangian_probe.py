#!/usr/bin/env python3
import importlib.util, itertools, random, sys, time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('solver', ROOT/'solver.py')
solver=importlib.util.module_from_spec(spec); spec.loader.exec_module(solver)
path=Path(sys.argv[1]) if len(sys.argv)>1 else ROOT/'runs/official_calibrated_low_synth.txt'
lines=path.read_text().strip().splitlines(); start=1 if lines and lines[0].startswith('task_id_list') else 0
rows=[]; tasks=set(); couriers=set()
for idx,s in enumerate(lines[start:]):
    a=s.split('\t')
    if len(a)<4: continue
    k,c,score,will=a[:4]
    row=(k,tuple(k.split(',')),c,float(score),float(will),idx)
    if len(row[1])==1:
        rows.append(row); tasks.add(k); couriers.add(c)
tasks=sorted(tasks); couriers=sorted(couriers)
base=solver.solve(path.read_text())
base_cost=solver._solution_expected_cost(base, rows, set(tasks))
print('base',base_cost,'groups',len(base),'couriers',sum(len(x) for _,x in base))
by={t:[] for t in tasks}
for r in rows: by[r[0]].append(r)
# Build columns: include k=1..4 from best single candidates by primitive and by score/will diversity.
cols={}
for t,rs in by.items():
    cand=[]; seen=set()
    pools=[]
    pools.append(sorted(rs,key=lambda r:solver._group_expected_cost([r],1))[:8])
    pools.append(sorted(rs,key=lambda r:(-r[4],r[3]))[:8])
    pools.append(sorted(rs,key=lambda r:(r[3],-r[4]))[:8])
    pool=[]
    for p in pools:
        for r in p:
            if r[2] not in seen: seen.add(r[2]); pool.append(r)
    for k in range(1,4):
        for comb in itertools.combinations(pool,k):
            cs=tuple(sorted(r[2] for r in comb))
            if len(set(cs))<k: continue
            cost=solver._group_expected_cost(list(comb),1)
            cand.append((cost,cs,comb))
    # per k prune + global prune
    keep=[]
    for k in range(1,4):
        kk=sorted([x for x in cand if len(x[1])==k], key=lambda x:x[0])[:30]
        keep.extend(kk)
    cols[t]=sorted(keep,key=lambda x:x[0])[:80]
print('cols',sum(len(v) for v in cols.values()),'per_task',min(len(v) for v in cols.values()),max(len(v) for v in cols.values()))
# Lagrangian penalties for couriers, choose one column per task minimizing cost+lambda usage; repair duplicates greedily.
lamb={c:0.0 for c in couriers}
best=None
rng=random.Random(7)
start_time=time.time()
def decode(choice):
    used=set(); out=[]; dup=0
    for t,col in choice.items():
        cost,cs,comb=col
        for c in cs:
            if c in used: dup+=1
            used.add(c)
        out.append((t,[r[2] for r in comb]))
    return out,dup,len(used)
def repair(choice):
    # iterative duplicate removal by choosing next-best feasible column for conflicted tasks
    choice=dict(choice)
    for _ in range(35):
        counts={}
        for col in choice.values():
            for c in col[1]: counts[c]=counts.get(c,0)+1
        bad={c for c,n in counts.items() if n>1}
        if not bad: break
        affected=[t for t,col in choice.items() if any(c in bad for c in col[1])]
        improved=False
        rng.shuffle(affected)
        for t in affected:
            other={c for tt,col in choice.items() if tt!=t for c in col[1]}
            feasible=[col for col in cols[t] if not any(c in other for c in col[1])]
            if feasible:
                old=choice[t]
                # prefer not too many riders and true cost
                choice[t]=min(feasible,key=lambda x:(x[0],len(x[1])))
                improved=True
                break
            else:
                old=choice[t]
                choice[t]=min(cols[t],key=lambda x:x[0]+500*sum(c in other for c in x[1]))
                improved=True
                break
        if not improved: break
    return choice
for it in range(80):
    choice={}
    use={c:0 for c in couriers}
    for t in tasks:
        temp=0.03*(1-it/220)
        ranked=sorted(cols[t], key=lambda x:x[0]+sum(lamb[c] for c in x[1]))[:4]
        col=ranked[0] if temp<=0 or rng.random()>.2 else rng.choice(ranked)
        choice[t]=col
        for c in col[1]: use[c]+=1
    repaired=repair(choice)
    out,dup,usedn=decode(repaired)
    cost=solver._solution_expected_cost(out, rows, set(tasks))
    if dup==0 and (best is None or cost<best[0]):
        best=(cost,out,it,usedn)
        print('best',cost,'it',it,'used',usedn,'kdist',{k:sum(1 for _,ls in out if len(ls)==k) for k in range(1,4)},'elapsed',round(time.time()-start_time,2), flush=True)
    # subgradient: target average 1 use per courier, penalize overuse, mildly reward underuse
    step=4.0/(1+it/30)
    for c in couriers:
        lamb[c]=max(-20,min(80,lamb[c]+step*(use[c]-1)))
print('final_best',best[0] if best else None)
if best:
    for x in best[1][:10]: print(x)
