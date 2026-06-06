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

def fast_once(sol,C,T,sec=1.0,focus=22):
 dead=time.monotonic()+sec; S0=sel(sol,C); base=s._solution_expected_cost(sol,C,T); best=(base,sol,None)
 bykey=collections.defaultdict(list); row_by_ck={}
 for r in s._canonical_candidates(C): bykey[r[0]].append(r); row_by_ck[(r[0],r[2])]=r
 singles=[(s._group_expected_cost(v,1),k,v) for k,v in S0.items() if len(v[0][1])==1]
 singles.sort(reverse=True); singles=singles[:focus]
 used_all={r[2] for v in S0.values() for r in v}
 # marginal insertion lookup for current groups: courier -> sorted (delta,key,row)
 marg=collections.defaultdict(list)
 for key,g in S0.items():
  before=s._group_expected_cost(g,len(g[0][1]))
  have={r[2] for r in g}
  for r in bykey.get(key,[]):
   if r[2] in have: continue
   after=s._group_expected_cost(g+[r],len(g[0][1])); d=after-before
   if d<-.01: marg[r[2]].append((d,key,r))
 for c in marg: marg[c].sort()
 for ia in range(len(singles)):
  if time.monotonic()>dead-.02: break
  _,ka,ga=singles[ia]; ta=ga[0][1][0]
  for _,kb,gb in singles[ia+1:]:
   if time.monotonic()>dead-.02: break
   tb=gb[0][1][0]; rows=bykey.get(ta+','+tb) or bykey.get(tb+','+ta)
   if not rows: continue
   outside=used_all-{r[2] for r in ga+gb}
   br=sorted([r for r in rows if r[2] not in outside],key=lambda r:(s._group_expected_cost([r],2),-r[4],r[5]))[:4]
   for k in (1,2):
    for comb in itertools.combinations(br,k):
     cs={r[2] for r in comb}
     if len(cs)!=len(comb): continue
     new={x:list(y) for x,y in S0.items() if x not in (ka,kb)}; new[comb[0][0]]=list(comb)
     free=({r[2] for r in ga+gb}-cs)
     occupied={r[2] for v in new.values() for r in v}
     # freed couriers may be best added back to the new bundle or to other existing groups.
     new_bundle_key=comb[0][0]
     for c in sorted(free):
      choices=[]
      for r in bykey.get(new_bundle_key,[]):
       if r[2]==c: choices.append((0,new_bundle_key,r))
      choices += marg.get(c,[])[:12]
      for d,key,r in choices:
       if key not in new or key in (ka,kb): continue
       if c in occupied: break
       g=new[key]
       if tuple(g[0][1])!=tuple(r[1]): continue
       before=s._group_expected_cost(g,len(g[0][1])); after=s._group_expected_cost(g+[r],len(g[0][1]))
       if after<before-1e-9: new[key].append(r); occupied.add(c); break
     cand=[(k,[r[2] for r in v]) for k,v in new.items()]
     sc=s._solution_expected_cost(cand,C,T)
     if sc<best[0]-1e-9: best=(sc,cand,(ka,kb,comb[0][0],list(cs)))
 return best

def repair(sol,C,T,total=2.5):
 end=time.monotonic()+total; cur=sol; base=s._solution_expected_cost(sol,C,T); best=base; info=[]
 while time.monotonic()<end-.05:
  sc,cand,why=fast_once(cur,C,T,min(0.8,end-time.monotonic()))
  if sc<best-1e-9:
   best=sc; cur=cand; info.append(why)
  else: break
 return cur,best,info

def run(path):
 text=pathlib.Path(path).read_text(); C,T=parse(text); b=s.solve(text); bc=s._solution_expected_cost(b,C,T)
 for sec in [.4,.8,1.2,2.0,3.0]:
  t=time.monotonic(); sol,sc,info=repair(b,C,T,sec)
  print(json.dumps({'case':pathlib.Path(path).name,'sec':sec,'base':bc,'score':sc,'delta':sc-bc,'groups':len(sol),'time':time.monotonic()-t,'info':info},ensure_ascii=False))
if __name__=='__main__':
 for p in sys.argv[1:]: run(p)
