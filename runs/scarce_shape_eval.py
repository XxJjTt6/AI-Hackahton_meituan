#!/usr/bin/env python3
import importlib.machinery, importlib.util, sys, time, collections
from pathlib import Path
ROOT=Path('/Users/比赛/FOR_AutoSolver_706.72')
DATA=ROOT/'Fwd_ 【美团AI Hackathon大赛】-【命题四AutoSolver：让AI Agent 自主求解配送分配问题】脱敏数据'/'large_seed301.txt'
def load(path):
    path=Path(path); name='m_'+str(abs(hash(str(path))))
    loader=importlib.machinery.SourceFileLoader(name,str(path)); spec=importlib.util.spec_from_loader(name,loader); m=importlib.util.module_from_spec(spec); loader.exec_module(m); return m
def parse(text):
    lines=text.strip().splitlines(); start=1 if lines and lines[0].startswith('task') else 0
    rows=[]; tasks=set(); couriers=set()
    for i,ln in enumerate(lines[start:]):
        p=ln.split('\t')
        if len(p)<4: continue
        key,c,sc,w=p[:4]; ts=tuple(x.strip() for x in key.split(',') if x.strip())
        rows.append((key,ts,c,float(sc),float(w),i)); tasks.update(ts); couriers.add(c)
    return rows,sorted(tasks),sorted(couriers)
def ser(rows):
    return 'task_id_list\tcourier_id\tscore\twillingness\n'+'\n'.join(f'{k}\t{c}\t{sc:.6f}\t{w:.6f}' for k,ts,c,sc,w,i in rows)+'\n'
def make(nt=40,nc=40,single=True,pair=True):
    rows,tasks,couriers=parse(DATA.read_text()); kt=set(tasks[:nt]); kc=set(couriers[:nc]); out=[]; idx=0
    for key,ts,c,sc,w,i in rows:
        if c not in kc or not all(t in kt for t in ts): continue
        if len(ts)==1 and not single: continue
        if len(ts)==2 and not pair: continue
        if len(ts)>2: continue
        out.append((key,ts,c,sc,w,idx)); idx+=1
    return ser(out)
def sig(mod,res,rows,tasks):
    cost=mod._solution_expected_cost(res,rows,set(tasks)); cov=mod._solution_covered_count(res,rows)
    kd=collections.Counter(len(cs) for _,cs in res); bd=collections.Counter(len(k.split(',')) for k,_ in res)
    return cost,cov,len(res),dict(kd),dict(bd)
for p in sys.argv[1:] or ['solver.py']:
    mod=load(ROOT/p); print('solver',p, flush=True)
    for name,text in [('scarce_single_pair',make(single=True,pair=True)),('scarce_pair_only',make(single=False,pair=True)),('scarce_single_only',make(single=True,pair=False))]:
        rows,tasks,couriers=parse(text); t0=time.monotonic(); res=mod.solve(text); dt=time.monotonic()-t0
        print(' ',name,'rows',len(rows),'time',round(dt,2),'sig',sig(mod,res,rows,tasks), flush=True)
