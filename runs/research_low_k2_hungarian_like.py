#!/usr/bin/env python3
# Exact-ish low K=2: generate pair columns per task, solve set packing by Lagrangian rider prices + repair.
import sys,time,importlib.util,itertools,collections,random
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('base',ROOT/'solver.py'); base=importlib.util.module_from_spec(spec); spec.loader.exec_module(base)

def parse(path):
 text=Path(path).read_text(); lines=text.strip().splitlines(); start=1 if lines and lines[0].startswith('task') else 0
 rows=[]; tasks=set(); cour=set()
 for i,ln in enumerate(lines[start:]):
  p=ln.split('\t');
  if len(p)<4: continue
  k,c,sc,w=p[:4]; ts=tuple(k.split(',')); rows.append((k,ts,c,float(sc),float(w),i)); tasks.update(ts); cour.add(c)
 return text,rows,sorted(tasks),sorted(cour)

def build_pairs(rows,tasks,top=18,keep=80):
 by={t:[] for t in tasks}
 for r in rows:
  if len(r[1])==1: by[r[1][0]].append(r)
 pairs={}
 for t,rs in by.items():
  pool=[]; seen=set()
  for key in [lambda r:(base._single_expected_cost(r),r[5]),lambda r:(-r[4],r[3]),lambda r:(r[3],-r[4]),lambda r:(r[3]/max(r[4],1e-6),r[5])]:
   for r in sorted(rs,key=key)[:top]:
    if r[2] not in seen: seen.add(r[2]); pool.append(r)
  cand=[]
  for a,b in itertools.combinations(pool,2):
   cost=base._group_expected_cost((a,b),1); cand.append((cost,(a[2],b[2]),(a,b)))
  pairs[t]=sorted(cand,key=lambda x:x[0])[:keep]
 return pairs

def lagrangian(pairs,tasks,couriers,rounds=80):
 price={c:0.0 for c in couriers}; best=None; bestc=1e9
 for it in range(rounds):
  chosen=[]; count=collections.Counter()
  for t in tasks:
   cost,cs,comb=min(pairs[t],key=lambda x:x[0]+price[x[1][0]]+price[x[1][1]])
   chosen.append((t,cost,cs,comb)); count.update(cs)
  # repair duplicate riders greedily by replacing most expensive conflicts
  used=set(); out=[]; ok=True
  for t,cost,cs,comb in sorted(chosen,key=lambda x:x[1],reverse=True):
   pick=None
   for cand in pairs[t]:
    if cand[1][0] not in used and cand[1][1] not in used:
     pick=cand; break
   if not pick: ok=False; break
   cost,cs,comb=pick; used.update(cs); rr=sorted(comb,key=lambda r:(r[3],-r[4],r[5])); out.append((t,[r[2] for r in rr]))
  if ok:
   # cost evaluated outside by caller
   yield out,it
  step=2.0/(1+it*.05)
  for c,n in count.items(): price[c]+=step*(n-1)

def eval(path):
 text,rows,tasks,cour=parse(path); baseout=base.solve(text); basec=base._solution_expected_cost(baseout,rows,set(tasks)); print('base',basec,collections.Counter(len(cs) for _,cs in baseout))
 pairs=build_pairs(rows,tasks); best=baseout; bestc=basec
 for out,it in lagrangian(pairs,tasks,cour,120):
  c=base._solution_expected_cost(out,rows,set(tasks))
  if c<bestc: best,bestc=out,c; print('improve',it,bestc)
 print('best',bestc,collections.Counter(len(cs) for _,cs in best))
if __name__=='__main__': eval(sys.argv[1])
