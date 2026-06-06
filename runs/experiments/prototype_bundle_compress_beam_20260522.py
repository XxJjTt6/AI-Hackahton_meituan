#!/usr/bin/env python3
from __future__ import annotations
import importlib.util,pathlib,itertools,time,sys,json,collections,heapq
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

def partial_cost(N,keys):
 return sum(s._group_expected_cost(N[k],len(N[k][0][1])) for k in keys if k in N and N[k])

def reinvest_beam(new,free,bykey,marg,removed,base_changed,beamw=24,per_c=10):
 # states: (delta_partial, N, changed_keys, occupied)
 states=[(base_changed,{k:list(v) for k,v in new.items()},set(),{r[2] for v in new.values() for r in v})]
 for c in sorted(free):
  cand=[None]
  # include all compatible current groups with this courier; score by exact marginal later
  for k,g in new.items():
   if k in removed: continue
   for r in bykey.get(k,[]):
    if r[2]==c and tuple(r[1])==tuple(g[0][1]): cand.append((k,r)); break
  for z,k,r in marg.get(c,[])[:per_c]:
   if k in new and k not in removed: cand.append((k,r))
  # de-dup but keep enough diversity
  seen=set(); cc=[]
  for x in cand:
   sg=None if x is None else (x[0],x[1][2])
   if sg in seen: continue
   seen.add(sg); cc.append(x)
  nxt=[]
  for _,N,chg,occ in states:
   for x in cc[:per_c+1]:
    if x is None:
     nxt.append((partial_cost(N,chg),N,chg,occ)); continue
    k,r=x
    if r[2] in occ or k not in N: continue
    if tuple(N[k][0][1])!=tuple(r[1]): continue
    old=s._group_expected_cost(N[k],len(N[k][0][1]))
    g=list(N[k])+[r]
    newc=s._group_expected_cost(g,len(g[0][1]))
    # allow non-improving insertion only if it may be needed? no, redundancy should reduce expected cost
    if newc>=old-1e-9: continue
    NN={a:list(b) for a,b in N.items()}; NN[k]=g
    nchg=set(chg); nchg.add(k); nocc=set(occ); nocc.add(r[2])
    nxt.append((partial_cost(NN,nchg),NN,nchg,nocc))
  if len(nxt)>beamw:
   nxt=heapq.nsmallest(beamw,nxt,key=lambda x:x[0])
  states=nxt or states
 best=min(states,key=lambda x:x[0])
 return best[1]

def build_indexes(C,S0):
 bykey=collections.defaultdict(list)
 for r in s._canonical_candidates(C): bykey[r[0]].append(r)
 marg=collections.defaultdict(list)
 for k,g in S0.items():
  q=s._group_expected_cost(g,len(g[0][1])); h={r[2] for r in g}
  for r in bykey.get(k,[]):
   if r[2] in h: continue
   z=s._group_expected_cost(g+[r],len(g[0][1]))-q
   if z<-.01: marg[r[2]].append((z,k,r))
 for c in marg: marg[c].sort()
 return bykey,marg

def compress_once(sol,C,T,sec=1.0,focus=24):
 dead=time.monotonic()+sec; S0=sel(sol,C); base=s._solution_expected_cost(sol,C,T); best=(base,sol,None)
 bykey,marg=build_indexes(C,S0)
 used={r[2] for v in S0.values() for r in v}
 singles=sorted([(s._group_expected_cost(v,1),k,v) for k,v in S0.items() if len(v[0][1])==1],reverse=True)[:focus]
 evals=0
 for i in range(len(singles)):
  if time.monotonic()>dead-.04: break
  _,ka,ga=singles[i]; ta=ga[0][1][0]
  for _,kb,gb in singles[i+1:]:
   if time.monotonic()>dead-.04: break
   tb=gb[0][1][0]; rows=bykey.get(ta+','+tb) or bykey.get(tb+','+ta) or []
   if not rows: continue
   outside=used-{r[2] for r in ga+gb}
   rows=sorted([r for r in rows if r[2] not in outside],key=lambda r:(s._group_expected_cost([r],2),-r[4],r[5]))[:6]
   for k in (1,2):
    for comb in itertools.combinations(rows,k):
     if time.monotonic()>dead-.035: break
     if len({r[2] for r in comb})!=len(comb): continue
     N={a:list(b) for a,b in S0.items() if a not in (ka,kb)}; N[comb[0][0]]=list(comb)
     changed={comb[0][0]}
     base_changed=s._group_expected_cost(N[comb[0][0]],2)
     free={r[2] for r in ga+gb}-{r[2] for r in comb}
     N=reinvest_beam(N,free,bykey,marg,{ka,kb},base_changed,beamw=18,per_c=8)
     cand=[(a,[r[2] for r in b]) for a,b in N.items()]
     sc=s._solution_expected_cost(cand,C,T); evals+=1
     if sc<best[0]-1e-9: best=(sc,cand,(ka,kb,comb[0][0],[r[2] for r in comb],evals))
 return best

def repair(sol,C,T,total=3.0):
 end=time.monotonic()+total; cur=sol; best=s._solution_expected_cost(sol,C,T); info=[]
 while time.monotonic()<end-.05:
  sc,cand,why=compress_once(cur,C,T,min(1.25,end-time.monotonic()))
  if sc<best-1e-9:
   cur=cand; best=sc; info.append(why)
  else: break
 return cur,best,info

def run(path):
 text=pathlib.Path(path).read_text(); C,T=parse(text); b=s.solve(text); bc=s._solution_expected_cost(b,C,T)
 for sec in [.8,1.5,2.5,4.0,8.0]:
  t=time.monotonic(); sol,sc,info=repair(b,C,T,sec)
  print(json.dumps({'case':pathlib.Path(path).name,'sec':sec,'base':bc,'score':sc,'delta':sc-bc,'groups':len(sol),'time':time.monotonic()-t,'info':info},ensure_ascii=False),flush=True)
if __name__=='__main__':
 for p in sys.argv[1:]: run(p)
