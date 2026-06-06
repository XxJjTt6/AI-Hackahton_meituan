#!/usr/bin/env python3
import importlib.machinery, importlib.util, sys, time, collections
from pathlib import Path
ROOT=Path('/Users/比赛/FOR_AutoSolver_706.72')
DATA=ROOT/'Fwd_ 【美团AI Hackathon大赛】-【命题四AutoSolver：让AI Agent 自主求解配送分配问题】脱敏数据'/'large_seed301.txt'
def load(path):
    path=Path(path); name='mod_'+str(abs(hash(str(path))))
    loader=importlib.machinery.SourceFileLoader(name,str(path)); spec=importlib.util.spec_from_loader(name,loader)
    mod=importlib.util.module_from_spec(spec); loader.exec_module(mod); return mod
def parse(text):
    lines=text.strip().splitlines(); start=1 if lines and lines[0].startswith('task') else 0
    rows=[]; tasks=set(); couriers=set()
    for i,ln in enumerate(lines[start:]):
        p=ln.split('\t')
        if len(p)<4: continue
        key,c,sc,w=p[:4]; ts=tuple(x.strip() for x in key.split(',') if x.strip())
        rows.append((key,ts,c,float(sc),float(w),i)); tasks.update(ts); couriers.add(c)
    return rows,sorted(tasks),sorted(couriers)
def serialize(rows):
    return 'task_id_list\tcourier_id\tscore\twillingness\n'+'\n'.join(f'{k}\t{c}\t{sc:.6f}\t{w:.6f}' for k,ts,c,sc,w,i in rows)+'\n'
def make(scale=0.25, nt=30, nc=60, single_only=True):
    rows,tasks,couriers=parse(DATA.read_text()); keep_t=set(tasks[:nt]); keep_c=set(couriers[:nc]); out=[]; idx=0
    for key,ts,c,sc,w,i in rows:
        if c not in keep_c: continue
        if single_only and len(ts)!=1: continue
        if all(t in keep_t for t in ts): out.append((key,ts,c,sc,max(0.0001,min(0.999,w*scale)),idx)); idx+=1
    return serialize(out)
def eval(path):
    mod=load(path)
    for scale in [0.20,0.25,0.30,0.35,0.40]:
        text=make(scale); rows,tasks,couriers=parse(text)
        t0=time.monotonic(); res=mod.solve(text); dt=time.monotonic()-t0
        cost=mod._solution_expected_cost(res,rows,set(tasks))
        kd=collections.Counter(len(cs) for _,cs in res); bd=collections.Counter(len(k.split(',')) for k,_ in res)
        cov=mod._solution_covered_count(res,rows)
        print(f'  low_single_{scale:.2f} time={dt:5.2f}s cost={cost:8.2f} cov={cov}/{len(tasks)} groups={len(res)} k={dict(kd)} bundle={dict(bd)}', flush=True)
if __name__=='__main__':
    for p in sys.argv[1:] or ['solver.py']:
        print('solver',p, flush=True); eval(ROOT/p)
