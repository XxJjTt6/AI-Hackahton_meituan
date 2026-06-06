#!/usr/bin/env python3
import importlib.util, sys, time
from pathlib import Path
ROOT=Path('/Users/比赛/FOR_AutoSolver_706.72')
def load(path,name):
 spec=importlib.util.spec_from_file_location(name,ROOT/path); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m
base=load(Path(sys.argv[1]),'base'); cand=load(Path(sys.argv[2]),'cand')
DATA=ROOT/'Fwd_ 【美团AI Hackathon大赛】-【命题四AutoSolver：让AI Agent 自主求解配送分配问题】脱敏数据'/'large_seed301.txt'
text=DATA.read_text()
rows=[]; tasks=set()
for i,ln in enumerate(text.strip().splitlines()[1:]):
 p=ln.split('\t'); k,c,sc,w=p[:4]; ts=tuple(k.split(',')); rows.append((k,ts,c,float(sc),float(w),i)); tasks.update(ts)
for name,mod in [('base',base),('cand',cand)]:
 t=time.monotonic(); out=mod.solve(text); dt=time.monotonic()-t
 print(name,'own',mod._solution_expected_cost(out,rows,tasks),'base_score',base._solution_expected_cost(out,rows,tasks),'cov',base._solution_covered_count(out,rows),'time',dt,'groups',len(out))
