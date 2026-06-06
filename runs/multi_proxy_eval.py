#!/usr/bin/env python3
import importlib.util, random, time, sys, statistics
from pathlib import Path
from collections import Counter
ROOT=Path('/Users/比赛/FOR_AutoSolver_706.72')
DATA=ROOT/'Fwd_ 【美团AI Hackathon大赛】-【命题四AutoSolver：让AI Agent 自主求解配送分配问题】脱敏数据'/'large_seed301.txt'

def load(p):
    spec=importlib.util.spec_from_file_location('m'+str(abs(hash(str(p)))), ROOT/p)
    m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m

def parse(text):
    rows=[]; tasks=set(); cour=set()
    for i,ln in enumerate(text.strip().splitlines()[1:]):
        p=ln.split('\t'); key,c,sc,w=p[:4]; ts=tuple(key.split(',')); rows.append((key,ts,c,float(sc),float(w),i)); tasks.update(ts); cour.add(c)
    return rows,sorted(tasks),sorted(cour)
rows,tasks,cours=parse(DATA.read_text())

def serialize(sel):
    return 'task_id_list\tcourier_id\tscore\twillingness\n'+'\n'.join(f'{k}\t{c}\t{sc:.6f}\t{w:.6f}' for k,ts,c,sc,w,i in sel)+'\n'

def make_case(kind, seed):
    rng=random.Random(seed)
    nt=30 if kind.startswith('low') or kind.startswith('normal') else 40
    nc=60 if kind.startswith('low') or kind.startswith('normal') else 40
    ts=set(rng.sample(tasks, nt)); cs=set(rng.sample(cours, nc)); out=[]; idx=0
    for key,tup,c,sc,w,i in rows:
        if c in cs and all(t in ts for t in tup):
            if kind.startswith('low'): w=max(.0001,min(.999,w*(0.25 if kind=='low025' else 0.30)))
            out.append((key,tup,c,sc,w,idx)); idx+=1
    return serialize(out)

def eval_one(mod,text):
    rs,ts,cs=parse(text); t0=time.monotonic(); res=mod.solve(text); dt=time.monotonic()-t0
    cost=mod._solution_expected_cost(res,rs,set(ts)); cov=mod._solution_covered_count(res,rs)
    return cost,cov,dt,len(res),Counter(len(x[1]) for x in res)

def main():
    paths=[Path(p) for p in sys.argv[1:]]
    mods=[(str(p),load(p)) for p in paths]
    cases=[]
    for kind in ['normal','low025','low030','scarce']:
        for seed in range(3): cases.append((kind,seed,make_case(kind,1000+seed+17*len(kind))))
    for name,mod in mods:
        print('\nSOLVER',name, flush=True)
        vals=[]
        for kind,seed,text in cases:
            try:
                cost,cov,dt,groups,kd=eval_one(mod,text)
                vals.append(cost)
                print(f' {kind}{seed}: cost={cost:8.2f} cov={cov:2d} time={dt:5.2f}s groups={groups:2d} k={dict(kd)}', flush=True)
            except Exception as e:
                print(f' {kind}{seed}: ERROR {e!r}', flush=True)
        print(' mean',statistics.mean(vals) if vals else 'NA', flush=True)
if __name__=='__main__': main()
