#!/usr/bin/env python3
import importlib.util, random, time, sys, statistics
from pathlib import Path
from collections import Counter
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
 return base._solution_expected_cost(out,rs,set(ts)), base._solution_covered_count(out,rs), dt, len(out), Counter(len(x[1]) for x in out)
def main():
 cand=load(Path(sys.argv[1]),'cand')
 cases=[('public_large',DATA.read_text())]
 for kind in ['normal','low025','low030','scarce']:
  for seed in range(3): cases.append((f'{kind}{seed}',make_case(kind,1000+seed+17*len(kind))))
 bvals=[]; cvals=[]
 for name,text in cases:
  b=eval_mod(base,text); c=eval_mod(cand,text); bvals.append(b[0]); cvals.append(c[0])
  print(f'{name:12s} base={b[0]:9.2f} cand={c[0]:9.2f} delta={c[0]-b[0]:8.2f} cov {b[1]:2d}->{c[1]:2d} time {b[2]:5.2f}->{c[2]:5.2f} k={dict(c[4])}', flush=True)
 print('MEAN base',statistics.mean(bvals),'cand',statistics.mean(cvals),'delta',statistics.mean(cvals)-statistics.mean(bvals))
if __name__=='__main__': main()
