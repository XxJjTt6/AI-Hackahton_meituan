#!/usr/bin/env python3
import sys,time,itertools
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT)); sys.path.insert(0,str(ROOT/'runs'))
import solver, proxy_eval

def improve(text, max_tasks=6):
    rows,tasks,couriers=proxy_eval.parse(text); T=set(tasks); out=solver.solve(text)
    base=solver._solution_expected_cost(out,rows,T); lut={(r[0],r[2]):r for r in rows}; selected={k:[lut[(k,c)] for c in cs if (k,c) in lut] for k,cs in out}
    singles={}
    for r in rows:
        if len(r[1])==1: singles.setdefault(r[0],[]).append(r)
    ranked=[]
    for k,rs in selected.items():
        if len(k.split(','))==1:
            ranked.append((solver._group_expected_cost(rs,1),k))
    ranked=sorted(ranked, reverse=True)[:max_tasks]
    keys=[k for _,k in ranked]
    fixed=[(k,cs) for k,cs in out if k not in keys]
    used={c for k,cs in fixed for c in cs}
    best=out; bestc=base
    # enumerate top k=1..3 replacements for selected worst single-task groups only
    options=[]
    for k in keys:
        opts=[]
        pool=sorted([r for r in singles.get(k,[]) if r[2] not in used], key=lambda r: solver._single_expected_cost(r))[:14]
        for m in (1,2,3):
            for comb in itertools.combinations(pool,m):
                if len({r[2] for r in comb})<m: continue
                opts.append((solver._group_expected_cost(comb,1), k, tuple(r[2] for r in sorted(comb,key=lambda r:(r[3],-r[4],r[5])))))
        opts=sorted(opts)[:10]
        options.append(opts)
    def rec(i,cur,used2):
        nonlocal best,bestc
        if i==len(options):
            cand=fixed+[(k,list(cs)) for _,k,cs in cur]
            c=solver._solution_expected_cost(cand,rows,T)
            if c<bestc-1e-9: bestc=c; best=cand
            return
        for cost,k,cs in options[i]:
            if any(c in used2 for c in cs): continue
            rec(i+1,cur+[(cost,k,cs)],used2|set(cs))
    rec(0,[],set(used))
    return base,bestc,len(out),len(best)
for scale in [.2,.25,.3,.35]:
    text=proxy_eval.make_low(scale)
    print('scale',scale,'result',improve(text))
