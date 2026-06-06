#!/usr/bin/env python3
import importlib.util, random, time, sys, statistics
from pathlib import Path
ROOT=Path('/Users/比赛/FOR_AutoSolver_706.72')
DATA=ROOT/'Fwd_ 【美团AI Hackathon大赛】-【命题四AutoSolver：让AI Agent 自主求解配送分配问题】脱敏数据'/'large_seed301.txt'
def load(p,name):
 spec=importlib.util.spec_from_file_location(name,ROOT/p); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m
base=load(Path('solver.py'),'base')
def parse(text):
 rows=[]; tasks=set(); cours=set()
 for i,ln in enumerate(text.strip().splitlines()[1:]):
  p=ln.split('\t'); k,c,sc,w=p[:4]; ts=tuple(k.split(',')); rows.append((k,ts,c,float(sc),float(w),i)); tasks.update(ts); cours.add(c)
 return rows,sorted(tasks),sorted(cours)
rows,tasks,cours=parse(DATA.read_text())
def ser(sel): return 'task_id_list\tcourier_id\tscore\twillingness\n'+'\n'.join(f'{k}\t{c}\t{sc:.6f}\t{w:.6f}' for k,ts,c,sc,w,i in sel)+'\n'
def make(kind,seed):
 rng=random.Random(seed); nt=30; nc=60; ts=set(rng.sample(tasks,nt)); cs=set(rng.sample(cours,nc)); out=[]; idx=0
 for k,tup,c,sc,w,i in rows:
  if c in cs and all(t in ts for t in tup):
   scale=.25 if kind=='low025' else .30
   out.append((k,tup,c,sc,max(.0001,min(.999,w*scale)),idx)); idx+=1
 return ser(out)
def ev(mod,text):
 rs,ts,cs=parse(text); t=time.monotonic(); out=mod.solve(text); dt=time.monotonic()-t
 return mod._solution_expected_cost(out,rs,set(ts)),dt,len(out)
def main():
 cand=load(Path(sys.argv[1]),'cand'); vals=[]
 for kind in ['low025','low030']:
  for seed in range(6):
   text=make(kind,2000+seed+31*len(kind)); b=ev(base,text); c=ev(cand,text); vals.append(c[0]-b[0])
   print(f'{kind}{seed} base={b[0]:.2f} cand={c[0]:.2f} delta={c[0]-b[0]:.2f} time={b[1]:.2f}->{c[1]:.2f} groups={c[2]}',flush=True)
 print('mean_delta',statistics.mean(vals),'worst_delta',max(vals),'best_delta',min(vals))
if __name__=='__main__': main()
