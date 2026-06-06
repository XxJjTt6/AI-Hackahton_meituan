#!/usr/bin/env python3
# Try local 2-task pair swap for low single proxy after solver output.
from pathlib import Path
import importlib.util, itertools, collections, time
ROOT=Path('/Users/比赛/FOR_AutoSolver_706.72')
spec=importlib.util.spec_from_file_location('s',ROOT/'solver.py'); s=importlib.util.module_from_spec(spec); spec.loader.exec_module(s)
# reuse low_single text maker from previous script quickly
DATA=ROOT/'Fwd_ 【美团AI Hackathon大赛】-【命题四AutoSolver：让AI Agent 自主求解配送分配问题】脱敏数据'/'large_seed301.txt'
rows=[]; tasks=[]; cours=[]
for i,ln in enumerate(DATA.read_text().strip().splitlines()[1:]):
 p=ln.split('\t'); key,c,sc,w=p[:4]; ts=tuple(key.split(',')); rows.append((key,ts,c,float(sc),float(w),i));
tasks=sorted({t for _,ts,_,_,_,_ in rows for t in ts})[:30]; cours=sorted({c for _,_,c,_,_,_ in rows})[:60]
sel=[]; idx=0
for key,ts,c,sc,w,i in rows:
 if c in cours and len(ts)==1 and ts[0] in tasks: sel.append((key,ts,c,sc,max(.0001,w*.25),idx)); idx+=1
text='task_id_list\tcourier_id\tscore\twillingness\n'+'\n'.join(f'{k}\t{c}\t{sc}\t{w}' for k,ts,c,sc,w,i in sel)+'\n'
res=s.solve(text); base=s._solution_expected_cost(res,sel,set(tasks)); print('base',base,collections.Counter(len(cs) for _,cs in res))
row={(r[0],r[2]):r for r in sel}; bytask={t:[r for r in sel if r[1][0]==t] for t in tasks}
best=res; bestc=base
# Re-optimize courier assignment for two tasks preserving total rider counts on those tasks.
for (i,(t1,c1)),(j,(t2,c2)) in itertools.combinations(list(enumerate(res)),2):
 if ',' in t1 or ',' in t2: continue
 k1,k2=len(c1),len(c2); pool=[]
 for c in c1+c2:
  if (t1,c) in row: pool.append(row[(t1,c)])
  if (t2,c) in row: pool.append(row[(t2,c)])
 # also allow top alternatives unused globally
 used={c for k,cs in res for c in cs}-set(c1)-set(c2)
 for t in [t1,t2]:
  pool += [r for r in sorted(bytask[t],key=lambda r:s._single_expected_cost(r))[:8] if r[2] not in used]
 for a in itertools.combinations([r for r in pool if r[1][0]==t1], k1):
  cs1=[r[2] for r in a]
  if len(set(cs1))<k1: continue
  for b in itertools.combinations([r for r in pool if r[1][0]==t2 and r[2] not in cs1], k2):
   cs2=[r[2] for r in b]
   nr=list(res); nr[i]=(t1,cs1); nr[j]=(t2,cs2)
   c=s._solution_expected_cost(nr,sel,set(tasks))
   if c<bestc-1e-9: bestc=c; best=nr
print('best',bestc,'delta',bestc-base,collections.Counter(len(cs) for _,cs in best))
