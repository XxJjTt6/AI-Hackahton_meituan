#!/usr/bin/env python3
# Generate local low strategies with business view: K=2 all, selective K=3 for high marginal value + reject worst.
from pathlib import Path
import importlib.util, collections, time, itertools
ROOT=Path('/Users/比赛/FOR_AutoSolver_706.72')
DATA=ROOT/'Fwd_ 【美团AI Hackathon大赛】-【命题四AutoSolver：让AI Agent 自主求解配送分配问题】脱敏数据'/'large_seed301.txt'
spec=importlib.util.spec_from_file_location('s',ROOT/'solver.py'); s=importlib.util.module_from_spec(spec); spec.loader.exec_module(s)
def parse(text):
 rows=[]; tasks=set(); cour=set()
 for i,ln in enumerate(text.strip().splitlines()[1:]):
  p=ln.split('\t'); key,c,sc,w=p[:4]; ts=tuple(key.split(',')); rows.append((key,ts,c,float(sc),float(w),i)); tasks.update(ts); cour.add(c)
 return rows,sorted(tasks),sorted(cour)
rows,tasks,cour=parse(DATA.read_text()); keep_t=set(tasks[:30]); keep_c=set(cour[:60])
base=[]; idx=0
for key,ts,c,sc,w,i in rows:
 if c in keep_c and len(ts)==1 and ts[0] in keep_t:
  base.append((key,ts,c,sc,max(.0001,w*.25),idx)); idx+=1
by={t:[] for t in sorted(keep_t)}
for r in base: by[r[1][0]].append(r)
def result_cost(res): return s._solution_expected_cost(res,base,keep_t)
def topw(k=2):
 used=set(); res=[]
 for t in sorted(keep_t):
  opts=[r for r in by[t] if r[2] not in used]
  opts=sorted(opts,key=lambda r:(-r[4],r[3]))[:k]
  for r in opts: used.add(r[2])
  if opts: res.append((t,[r[2] for r in opts]))
 return res
# Greedy marginal allocation: first give everyone 1 best, then allocate remaining riders to highest marginal cost drop.
used=set(); sel={}
for t in sorted(keep_t):
 opts=sorted(by[t],key=lambda r:s._single_expected_cost(r))
 for r in opts:
  if r[2] not in used: sel[t]=[r]; used.add(r[2]); break
while len(used)<60:
 best=None; bd=0
 for t,rs in sel.items():
  old=s._group_expected_cost(rs,1)
  for r in by[t]:
   if r[2] in used: continue
   new=s._group_expected_cost(rs,1,extra=r); delta=old-new
   if delta>bd: bd=delta; best=(t,r)
 if not best: break
 t,r=best; sel[t].append(r); used.add(r[2])
greedy=[(t,[r[2] for r in sorted(rs,key=lambda x:(x[3],-x[4]))]) for t,rs in sorted(sel.items())]
for name,res in [('solver',s.solve('task_id_list\tcourier_id\tscore\twillingness\n'+'\n'.join(f'{k}\t{c}\t{sc}\t{w}' for k,ts,c,sc,w,i in base)+'\n')),('topw2',topw(2)),('topw3',topw(3)),('marginal',greedy)]:
 print(name,'cost',result_cost(res),'groups',len(res),'k',collections.Counter(len(cs) for _,cs in res),'cov',s._solution_covered_count(res,base))
