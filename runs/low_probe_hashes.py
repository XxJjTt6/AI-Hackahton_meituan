#!/usr/bin/env python3
# Print compact fingerprints of current solver outputs on synthetic low cases for future cache/sanity comparisons.
import importlib.util, random, hashlib
from pathlib import Path
ROOT=Path('/Users/比赛/FOR_AutoSolver_706.72')
DATA=ROOT/'Fwd_ 【美团AI Hackathon大赛】-【命题四AutoSolver：让AI Agent 自主求解配送分配问题】脱敏数据'/'large_seed301.txt'
spec=importlib.util.spec_from_file_location('s',ROOT/'solver.py');s=importlib.util.module_from_spec(spec);spec.loader.exec_module(s)
rows=[];tasks=set();cours=set()
for i,ln in enumerate(DATA.read_text().strip().splitlines()[1:]):
 p=ln.split('\t'); k,c,sc,w=p[:4]; tup=tuple(k.split(',')); rows.append((k,tup,c,float(sc),float(w),i)); tasks.update(tup); cours.add(c)
def make(kind,seed):
 rng=random.Random(seed); nt=30 if kind in ('normal','low025','low030') else 40; nc=60 if nt==30 else 40; ts=set(rng.sample(sorted(tasks),nt)); cs=set(rng.sample(sorted(cours),nc)); out=[]
 for k,t,c,sc,w,i in rows:
  if c in cs and all(x in ts for x in t):
   if kind=='low025': w=max(.0001,min(.999,w*.25))
   if kind=='low030': w=max(.0001,min(.999,w*.30))
   out.append((k,t,c,sc,w,i))
 return 'task_id_list\tcourier_id\tscore\twillingness\n'+'\n'.join(f'{k}\t{c}\t{sc:.6f}\t{w:.6f}' for k,t,c,sc,w,i in out)+'\n'
for kind in ['low025','low030']:
 for seed in range(3):
  text=make(kind,1000+seed+17*len(kind)); out=s.solve(text); h=hashlib.sha1(repr(out).encode()).hexdigest()[:12]
  rs=[]; T=set()
  for i,ln in enumerate(text.strip().splitlines()[1:]):
   p=ln.split('\t'); tup=tuple(p[0].split(',')); rs.append((p[0],tup,p[1],float(p[2]),float(p[3]),i)); T.update(tup)
  print(kind,seed,h,s._solution_expected_cost(out,rs,T),len(out),{k:sum(1 for _,cs in out if len(cs)==k) for k in range(1,8)})
