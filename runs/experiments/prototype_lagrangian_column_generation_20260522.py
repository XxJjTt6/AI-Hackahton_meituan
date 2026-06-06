#!/usr/bin/env python3
"""Lagrangian column generation prototype for TSV candidate problems.
Build many compact columns, iteratively prices task rewards / courier penalties, then repairs.
No official submission; tests a genuinely different solver family.
"""
from __future__ import annotations
import importlib.util,pathlib,itertools,random,math,time,sys,json,collections
ROOT=pathlib.Path(__file__).resolve().parents[2]
SOLVER=ROOT/'runs/baselines/official_best_7046558e_robust_cache.py'
spec=importlib.util.spec_from_file_location('s',SOLVER); s=importlib.util.module_from_spec(spec); spec.loader.exec_module(s)

def parse(text):
 rows=[]; T=set(); lines=text.strip().splitlines(); st=1 if lines and lines[0].startswith('task') else 0
 for i,l in enumerate(lines[st:]):
  p=l.split('\t'); ts=tuple(x.strip() for x in p[0].split(',') if x.strip()); rows.append((p[0],ts,p[1],float(p[2]),float(p[3]),i)); T.update(ts)
 return rows,sorted(T)

def build_columns(C,tasks,per_key_rows=10,per_key_cols=16):
 ti={t:i for i,t in enumerate(tasks)}; ci={c:i for i,c in enumerate(sorted({r[2] for r in C}))}
 by=collections.defaultdict(list)
 for r in s._canonical_candidates(C):
  if len(r[1])<=2: by[r[0]].append(r)
 cols=[]
 for key,rows in by.items():
  tc=len(rows[0][1]); tm=0
  for t in rows[0][1]: tm|=1<<ti[t]
  seed=[]; seen=set()
  for order in [lambda r:(s._group_expected_cost([r],tc),-r[4],r[5]),lambda r:(-r[4],r[3],r[5]),lambda r:(r[3]/max(r[4],.01),r[5])]:
   for r in sorted(rows,key=order)[:per_key_rows]:
    if r[2] not in seen: seen.add(r[2]); seed.append(r)
  opts=[]
  for k in range(1,min((4 if tc==1 else 3),len(seed))+1):
   for comb in itertools.combinations(seed,k):
    cm=0
    for r in comb: cm|=1<<ci[r[2]]
    if cm.bit_count()!=len(comb): continue
    cost=s._group_expected_cost(comb,tc)
    if cost<100*tc:
     opts.append((cost,tm,cm,key,tuple(r[2] for r in comb),tuple(comb)))
  # keep diverse by several score orders
  chosen=[]; sig=set()
  orders=[lambda x:x[0], lambda x:x[0]-100*x[1].bit_count(), lambda x:x[0]/max(1,x[1].bit_count()), lambda x:(x[0]/max(1,x[2].bit_count()))]
  for order in orders:
   for col in sorted(opts,key=order)[:per_key_cols//2]:
    sg=(col[1],col[2])
    if sg not in sig: sig.add(sg); chosen.append(col)
  cols.extend(chosen[:per_key_cols])
 return cols,ti,ci

def greedy(cols,n_tasks,n_couriers,lam_t,lam_c,noise=0.0,rng=None):
 order=[]
 for idx,col in enumerate(cols):
  cost,tm,cm=col[:3]
  red=cost-sum(lam_t[i] for i in range(n_tasks) if tm>>i&1)+sum(lam_c[i] for i in range(n_couriers) if cm>>i&1)
  if noise and rng: red+=rng.random()*noise
  order.append((red,idx))
 order.sort()
 usedt=usedc=0; val=0; path=[]
 for red,idx in order:
  cost,tm,cm=cols[idx][:3]
  if usedt&tm or usedc&cm: continue
  # accept if reduced attractive or still covers missing near penalty
  if red>15 and usedt.bit_count()>n_tasks*0.8: continue
  usedt|=tm; usedc|=cm; val+=cost; path.append(idx)
  if usedt.bit_count()==n_tasks: break
 return val+100*(n_tasks-usedt.bit_count()),usedt,usedc,path

def solve_lagr(C,tasks,inc,seconds=8.0):
 base=s._solution_expected_cost(inc,C,set(tasks)); cols,ti,ci=build_columns(C,tasks)
 # add incumbent exact columns
 lut={(r[0],r[2]):r for r in C}
 for key,cs in inc:
  rr=[lut.get((key,c)) for c in cs]; rr=[r for r in rr if r]
  if rr:
   tm=cm=0
   for t in rr[0][1]: tm|=1<<ti[t]
   for r in rr: cm|=1<<ci[r[2]]
   cols.append((s._group_expected_cost(rr,len(rr[0][1])),tm,cm,key,tuple(r[2] for r in rr),tuple(rr)))
 n=len(tasks); m=len(ci); rng=random.Random(522); lam_t=[95.0]*n; lam_c=[0.0]*m; best=(base,None)
 deadline=time.monotonic()+seconds
 for it in range(500):
  if time.monotonic()>deadline: break
  obj,ut,uc,path=greedy(cols,n,m,lam_t,lam_c,noise=0.05,rng=rng)
  if obj<best[0]-1e-9: best=(obj,path)
  step=12.0/(1+it/35)
  for i in range(n): lam_t[i]+= step*(1 if not (ut>>i)&1 else -0.08)
  for j in range(m): lam_c[j]=max(0.0, lam_c[j]+step*(0.04 if (uc>>j)&1 else -0.02))
 # deterministic sweeps around learned lambdas
 for reward in [70,80,90,100,110,120,140]:
  if time.monotonic()>deadline: break
  obj,ut,uc,path=greedy(cols,n,m,[reward]*n,[0]*m)
  if obj<best[0]-1e-9: best=(obj,path)
 if best[1] is None: return inc,base,len(cols)
 sol=[(cols[i][3],list(cols[i][4])) for i in best[1]]
 # polish with existing exact repair for fairness
 if time.monotonic()<deadline-.2:
  sol=s._reassign_mixed_solution(sol,C,set(tasks),min(deadline,time.monotonic()+.2))
 score=s._solution_expected_cost(sol,C,set(tasks))
 if score<base-1e-9: return sol,score,len(cols)
 return inc,base,len(cols)

def run(path):
 text=pathlib.Path(path).read_text(); C,T=parse(text); inc=s.solve(text); base=s._solution_expected_cost(inc,C,set(T)); t=time.monotonic(); sol,score,ncols=solve_lagr(C,T,inc,seconds=8.2)
 print(json.dumps({'case':pathlib.Path(path).name,'base':base,'lagr':score,'delta':score-base,'cols':ncols,'groups':len(sol),'time':time.monotonic()-t},ensure_ascii=False))
 if score<base-1e-9: print(sol)
if __name__=='__main__':
 for p in sys.argv[1:]: run(p)
