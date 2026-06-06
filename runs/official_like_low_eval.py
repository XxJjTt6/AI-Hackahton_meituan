#!/usr/bin/env python3
import importlib.util, random, time, sys, statistics
from pathlib import Path
ROOT=Path('/Users/比赛/FOR_AutoSolver_706.72'); DATA=ROOT/'Fwd_ 【美团AI Hackathon大赛】-【命题四AutoSolver：让AI Agent 自主求解配送分配问题】脱敏数据'/'large_seed301.txt'
def load(p,n): spec=importlib.util.spec_from_file_location(n,ROOT/p); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m
base=load(Path('solver.py'),'base'); cand=load(Path(sys.argv[1]),'cand')
def parse(text):
 rows=[]; tasks=set(); cours=set()
 for i,ln in enumerate(text.strip().splitlines()[1:]):
  p=ln.split('\t'); k,c,sc,w=p[:4]; ts=tuple(k.split(',')); rows.append((k,ts,c,float(sc),float(w),i)); tasks.update(ts); cours.add(c)
 return rows,sorted(tasks),sorted(cours)
rows,tasks,cours=parse(DATA.read_text())
def make(seed,scale=.28):
 rng=random.Random(seed); ts=set(rng.sample(tasks,30)); cs=set(rng.sample(cours,60)); out=[]; idx=0
 for k,tup,c,sc,w,i in rows:
  if len(tup)==1 and c in cs and tup[0] in ts:
   w=max(.0001,min(.999,w*scale)); out.append((k,tup,c,sc,w,idx)); idx+=1
 return 'task_id_list\tcourier_id\tscore\twillingness\n'+'\n'.join(f'{k}\t{c}\t{sc:.6f}\t{w:.6f}' for k,tup,c,sc,w,i in out)+'\n'
def ev(mod,text):
 rs,ts,cs=parse(text); t=time.monotonic(); out=mod.solve(text); dt=time.monotonic()-t
 return base._solution_expected_cost(out,rs,set(ts)), dt, len(out), {k:sum(1 for _,v in out if len(v)==k) for k in range(1,7)}
vals=[]
for scale in [.25,.28,.30,.33]:
 for seed in range(5):
  text=make(3000+seed,scale); b=ev(base,text); c=ev(cand,text); vals.append(c[0]-b[0]); print('scale',scale,'seed',seed,'delta',c[0]-b[0],'base',b,'cand',c,flush=True)
print('mean_delta',statistics.mean(vals))
