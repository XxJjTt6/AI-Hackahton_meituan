#!/usr/bin/env python3
import importlib.util,itertools,time,random
from pathlib import Path
ROOT=Path('/Users/比赛/FOR_AutoSolver_706.72')
DATA=ROOT/'Fwd_ 【美团AI Hackathon大赛】-【命题四AutoSolver：让AI Agent 自主求解配送分配问题】脱敏数据'/'large_seed301.txt'
spec=importlib.util.spec_from_file_location('s',ROOT/'solver.py');s=importlib.util.module_from_spec(spec);spec.loader.exec_module(s)
text=DATA.read_text(); rows=[]; tasks=set()
for i,ln in enumerate(text.strip().splitlines()[1:]):
 p=ln.split('\t'); k,c,sc,w=p[:4]; tup=tuple(k.split(',')); rows.append((k,tup,c,float(sc),float(w),i)); tasks.update(tup)
out=s.solve(text); row={(r[0],r[2]):r for r in rows}; sel=s._result_to_selected(out,row)
base=s._solution_expected_cost(out,rows,tasks); print('base',base,'groups',len(out))
keys=list(sel); bykey={}
for r in rows: bykey.setdefault(r[0],[]).append(r)
# For each pair/triple of selected task groups, rebuild only those task groups using _repair_task_window with larger budget.
best=out; bestc=base; t_end=time.monotonic()+120; tried=0
items=s._selected_repair_groups(sel); items=sorted(items,reverse=True)
windows=[]
for _,_,_,ts,_ in items[:16]: windows.append(set(ts))
for a in range(min(12,len(items))):
 for b in range(a+1,min(16,len(items))): windows.append(set(items[a][3])|set(items[b][3]))
for a in range(min(8,len(items))):
 for b in range(a+1,min(10,len(items))):
  for c in range(b+1,min(12,len(items))): windows.append(set(items[a][3])|set(items[b][3])|set(items[c][3]))
seen=set()
for W in windows:
 if time.monotonic()>t_end: break
 if len(W)>12: continue
 key=tuple(sorted(W))
 if key in seen: continue
 seen.add(key); tried+=1
 cur=s._result_to_selected(best,row)
 cand=s._repair_task_window(cur,rows,tasks,W,min(t_end,time.monotonic()+0.28),top_riders_per_task_key=14,max_k=5,option_limit=140)
 if cand:
  if time.monotonic()<t_end-.05: cand=s._reassign_mixed_solution(cand,rows,tasks,min(t_end,time.monotonic()+.05))
  cc=s._solution_expected_cost(cand,rows,tasks)
  if cc<bestc-1e-9:
   print('improve',bestc,'->',cc,'delta',cc-bestc,'W',key,'groups',len(cand),flush=True)
   best,bestc=cand,cc
print('done tried',tried,'best',bestc,'delta',bestc-base)
