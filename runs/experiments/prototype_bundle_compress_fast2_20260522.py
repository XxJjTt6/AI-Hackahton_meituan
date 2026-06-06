#!/usr/bin/env python3
from __future__ import annotations
import importlib.util,pathlib,itertools,time,sys,json,collections
ROOT=pathlib.Path(__file__).resolve().parents[2]
SOLVER=ROOT/'runs/baselines/official_best_7046558e_robust_cache.py'
spec=importlib.util.spec_from_file_location('s',SOLVER); s=importlib.util.module_from_spec(spec); spec.loader.exec_module(s)

def parse(text):
 rows=[]; T=set(); lines=text.strip().splitlines(); st=1 if lines and lines[0].startswith('task') else 0
 for i,l in enumerate(lines[st:]):
  p=l.split('\t'); ts=tuple(x.strip() for x in p[0].split(',') if x.strip()); rows.append((p[0],ts,p[1],float(p[2]),float(p[3]),i)); T.update(ts)
 return rows,T

def sel(sol,C):
 lut={(r[0],r[2]):r for r in C}; d={}
 for k,cs in sol:
  rr=[lut.get((k,c)) for c in cs]; rr=[r for r in rr if r]
  if rr: d[k]=rr
 return d

def best_reinvest(new,free,bykey,marg,removed_keys):
 free=list(free)
 opts=[]
 for c in free:
  L=[None]
  for key in list(new.keys()):
   if key in removed_keys: continue
   for r in bykey.get(key,[]):
    if r[2]==c and tuple(r[1])==tuple(new[key][0][1]): L.append((key,r)); break
  for z,key,r in marg.get(c,[])[:5]:
   if key in new and key not in removed_keys: L.append((key,r))
  # de-dup
  seen=set(); LL=[]
  for x in L:
   sg=None if x is None else (x[0],x[1][2])
   if sg in seen: continue
   seen.add(sg); LL.append(x)
  opts.append(LL[:6])
 best=None; bestv=1e99
 for choice in itertools.product(*opts):
  N={k:list(v) for k,v in new.items()}; ok=True
  for x,c in zip(choice,free):
   if x is None: continue
   key,r=x
   if any(a[2]==c for a in N[key]): ok=False; break
   N[key].append(r)
  if not ok: continue
  # local delta only over changed keys for speed
  v=0.0; changed={x[0] for x in choice if x is not None}
  for k in changed: v+=s._group_expected_cost(N[k],len(N[k][0][1]))
  if v<bestv: bestv=v; best=N
 return best or new

def fast_once(sol,C,T,sec=1.0,focus=22):
 dead=time.monotonic()+sec; S0=sel(sol,C); base=s._solution_expected_cost(sol,C,T); best=(base,sol,None)
 bykey=collections.defaultdict(list)
 for r in s._canonical_candidates(C): bykey[r[0]].append(r)
 U={r[2]for v in S0.values()for r in v}; M={}
 for k,g in S0.items():
  q=s._group_expected_cost(g,len(g[0][1])); h={r[2]for r in g}
  for r in bykey.get(k,[]):
   if r[2]in h:continue
   z=s._group_expected_cost(g+[r],len(g[0][1]))-q
   if z<-.01:M.setdefault(r[2],[]).append((z,k,r))
 for c in M:M[c].sort()
 W=sorted([(s._group_expected_cost(v,1),k,v)for k,v in S0.items()if len(v[0][1])==1],reverse=True)[:focus]
 for i in range(len(W)):
  if time.monotonic()>dead-.03:break
  _,ka,ga=W[i];ta=ga[0][1][0]
  for _,kb,gb in W[i+1:]:
   if time.monotonic()>dead-.03:break
   tb=gb[0][1][0];P=bykey.get(ta+','+tb)or bykey.get(tb+','+ta)or[]
   if not P:continue
   O=U-{r[2]for r in ga+gb};P=sorted([r for r in P if r[2]not in O],key=lambda r:(s._group_expected_cost([r],2),-r[4],r[5]))[:5]
   for n in(1,2):
    for comb in itertools.combinations(P,n):
     if len({r[2]for r in comb})!=len(comb):continue
     N={k:list(v)for k,v in S0.items()if k not in(ka,kb)};N[comb[0][0]]=list(comb);free={r[2]for r in ga+gb}-{r[2]for r in comb}
     N=best_reinvest(N,free,bykey,M,{ka,kb})
     cand=[(k,[r[2]for r in v])for k,v in N.items()];v=s._solution_expected_cost(cand,C,T)
     if v<best[0]-1e-9:best=(v,cand,(ka,kb,comb[0][0],[r[2]for r in comb]))
 return best

def repair(sol,C,T,total=2.5):
 end=time.monotonic()+total;cur=sol;best=s._solution_expected_cost(sol,C,T);info=[]
 while time.monotonic()<end-.05:
  sc,cand,why=fast_once(cur,C,T,min(.9,end-time.monotonic()))
  if sc<best-1e-9:best=sc;cur=cand;info.append(why)
  else:break
 return cur,best,info

def run(path):
 text=pathlib.Path(path).read_text();C,T=parse(text);b=s.solve(text);bc=s._solution_expected_cost(b,C,T)
 for sec in [.5,1.0,1.5,2.5,4.0]:
  t=time.monotonic();sol,sc,info=repair(b,C,T,sec);print(json.dumps({'case':pathlib.Path(path).name,'sec':sec,'base':bc,'score':sc,'delta':sc-bc,'groups':len(sol),'time':time.monotonic()-t,'info':info},ensure_ascii=False))
if __name__=='__main__':
 for p in sys.argv[1:]:run(p)
