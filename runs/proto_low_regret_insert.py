#!/usr/bin/env python3
import sys, random, time
from pathlib import Path
sys.path.insert(0,'.')
sys.path.insert(0,'runs')
import solver, proxy_eval

def solve_regret(text, lam=0.5, max_per_task=3):
    rows,tasks,couriers=proxy_eval.parse(text); tasks=set(tasks)
    by={t:[] for t in tasks}
    for r in rows:
        if len(r[1])==1: by[r[1][0]].append(r)
    selected={t:[] for t in tasks}; used=set(); cost={t:100.0 for t in tasks}
    # force one per task by regret of best vs second
    while any(not selected[t] for t in tasks):
        best=None
        for t in tasks:
            if selected[t]: continue
            opts=[]
            for r in by[t]:
                if r[2] in used: continue
                c=solver._group_expected_cost([r],1); opts.append((c,r))
            if not opts: continue
            opts.sort(key=lambda x:x[0]); regret=(opts[1][0]-opts[0][0]) if len(opts)>1 else 50
            key=(regret, -opts[0][0], t, opts[0][1])
            if best is None or key>best: best=key
        if best is None: break
        r=best[3]; selected[r[1][0]].append(r); used.add(r[2]); cost[r[1][0]]=solver._group_expected_cost(selected[r[1][0]],1)
    # add extras by regret/marginal benefit
    while True:
        cand=[]
        for t in tasks:
            if len(selected[t])>=max_per_task: continue
            vals=[]
            base=cost[t]
            for r in by[t]:
                if r[2] in used: continue
                nc=solver._group_expected_cost(selected[t],1,extra=r); gain=base-nc
                if gain>1e-9: vals.append((gain,nc,r))
            if not vals: continue
            vals.sort(reverse=True,key=lambda x:x[0])
            regret=vals[0][0]-(vals[1][0] if len(vals)>1 else 0)
            cand.append((vals[0][0]+lam*regret, vals[0][0], -vals[0][1], vals[0][2], vals[0][1]))
        if not cand: break
        cand.sort(reverse=True); _,gain,_,r,nc=cand[0]
        if gain<=1e-9: break
        selected[r[1][0]].append(r); used.add(r[2]); cost[r[1][0]]=nc
    return solver._format_selected({t:v for t,v in selected.items() if v}), rows, tasks

if __name__=='__main__':
    text=proxy_eval.make_low(.25)
    base_mod=solver
    base=base_mod.solve(text); rows,tasks,couriers=proxy_eval.parse(text)
    print('base', base_mod._solution_expected_cost(base,rows,set(tasks)), {k:sum(len(cs)==k for _,cs in base) for k in range(1,5)})
    for lam in [0,0.25,0.5,1,2]:
        for m in [2,3,4]:
            t=time.monotonic(); res,rows,tasks=solve_regret(text,lam,m); dt=time.monotonic()-t
            print('regret',lam,m,round(solver._solution_expected_cost(res,rows,tasks),6),round(dt,3),{k:sum(len(cs)==k for _,cs in res) for k in range(1,5)})
