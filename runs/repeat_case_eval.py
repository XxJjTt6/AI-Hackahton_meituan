#!/usr/bin/env python3
import importlib.util, random, time, sys, statistics
from pathlib import Path
ROOT=Path('/Users/比赛/FOR_AutoSolver_706.72')
DATA=ROOT/'Fwd_ 【美团AI Hackathon大赛】-【命题四AutoSolver：让AI Agent 自主求解配送分配问题】脱敏数据'/'large_seed301.txt'
def load(path,name):
 spec=importlib.util.spec_from_file_location(name,ROOT/path); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m
base=load(Path('solver.py'),'base')
def parse(text):
 rows=[]; tasks=set(); cours=set()
 for i,ln in enumerate(text.strip().splitlines()[1:]):
  p=ln.split('\t'); k,c,sc,w=p[:4]; ts=tuple(k.split(',')); rows.append((k,ts,c,float(sc),float(w),i)); tasks.update(ts); cours.add(c)
 return rows,sorted(tasks),sorted(cours)
rows,tasks,cours=parse(DATA.read_text())
def serialize(sel): return 'task_id_list\tcourier_id\tscore\twillingness\n'+'\n'.join(f'{k}\t{c}\t{sc:.6f}\t{w:.6f}' for k,ts,c,sc,w,i in sel)+'\n'
def make_case(kind,seed):
 rng=random.Random(seed); nt=30 if kind in ('normal','low025','low030') else 40; nc=60 if nt==30 else 40
 ts=set(rng.sample(tasks,nt)); cs=set(rng.sample(cours,nc)); out=[]; idx=0
 for k,tup,c,sc,w,i in rows:
  if c in cs and all(t in ts for t in tup):
   if kind=='low025': w=max(.0001,min(.999,w*.25))
   if kind=='low030': w=max(.0001,min(.999,w*.30))
   out.append((k,tup,c,sc,w,idx)); idx+=1
 return serialize(out)
def eval_mod(mod,text):
 rs,ts,cs=parse(text); t=time.monotonic(); out=mod.solve(text); dt=time.monotonic()-t
 return base._solution_expected_cost(out,rs,set(ts)), dt, len(out), {k:sum(1 for _,c in out if len(c)==k) for k in range(1,8)}
kind=sys.argv[2]; seed=int(sys.argv[3]); reps=int(sys.argv[4]) if len(sys.argv)>4 else 5
cand=load(Path(sys.argv[1]),'cand')
text=DATA.read_text() if kind=='public_large' else make_case(kind,1000+seed+17*len(kind))
for r in range(reps):
 b=eval_mod(base,text); c=eval_mod(cand,text)
 print(r,'base',b,'cand',c,'delta',c[0]-b[0],flush=True)
