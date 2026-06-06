#!/usr/bin/env python3
import importlib.machinery, importlib.util, re, sys, time
from pathlib import Path
sys.path.insert(0,'runs')
import proxy_eval
ROOT=Path('/Users/比赛/FOR_AutoSolver_706.72')
base=(ROOT/'solver.py').read_text()
variants=[
 ('current','(8,10,12,16,20)','(8,10,12,14,16,18)'),
 ('deep16_only','(8,10,12,16)','(8,10,12,14,16,18)'),
 ('deep20_only','(8,10,12,20)','(8,10,12,14,16,18)'),
 ('late_more','(8,10,12,16,20)','(8,10,12,14,16,18,20)'),
 ('late_alt','(8,10,12,16,20)','(10,12,14,16,18,20)'),
 ('baseline_windows','(8,10,12)','(8,10,12,14)'),
]
texts=[('low025',proxy_eval.make_low(.25)),('low030',proxy_eval.make_low(.30))]

def load(path):
 loader=importlib.machinery.SourceFileLoader('wmod'+str(abs(hash(path))),str(path)); spec=importlib.util.spec_from_loader(loader.name,loader); mod=importlib.util.module_from_spec(spec); loader.exec_module(mod); return mod
for name,deep,late in variants:
 s=base
 s=re.sub(r'for N in\([0-9,]+\):\n\t\tfor O in range\(10\):',f'for N in{deep}:\n\t\tfor O in range(10):',s,count=1)
 s=re.sub(r'F=\([0-9,]+\)\[B%\d+\];K=B%5',f'F={late}[B%{late.count(",")+1}];K=B%5',s,count=1)
 path=ROOT/'runs'/f'win_{name}.py'; path.write_text(s)
 mod=load(path)
 print('variant',name,flush=True)
 total=0
 for cname,text in texts:
  rows,tasks,couriers=proxy_eval.parse(text); T=set(tasks)
  t0=time.monotonic(); res=mod.solve(text); dt=time.monotonic()-t0
  cost=mod._solution_expected_cost(res,rows,T); total+=cost
  kd={}
  for k,cs in res: kd[len(cs)]=kd.get(len(cs),0)+1
  print(f'  {cname} time={dt:.2f} cost={cost:.2f} groups={len(res)} k={kd}',flush=True)
 print(f'  total={total:.2f}',flush=True)
