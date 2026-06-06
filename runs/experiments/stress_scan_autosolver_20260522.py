#!/usr/bin/env python3
from __future__ import annotations
import importlib.util,pathlib,random,statistics,json,collections,math,time
ROOT=pathlib.Path(__file__).resolve().parents[2]
BASE=ROOT/'runs/baselines/official_best_7046558e_robust_cache.py'
spec=importlib.util.spec_from_file_location('s',BASE); s=importlib.util.module_from_spec(spec); spec.loader.exec_module(s)
DATA=ROOT/'Fwd_ 【美团AI Hackathon大赛】-【命题四AutoSolver：让AI Agent 自主求解配送分配问题】脱敏数据/large_seed301.txt'

def parse(text):
 rows=[]; tasks=set(); couriers=set(); lines=text.strip().splitlines(); st=1 if lines and lines[0].startswith('task') else 0
 for i,l in enumerate(lines[st:]):
  p=l.split('\t'); ts=tuple(x.strip() for x in p[0].split(',') if x.strip()); r=[p[0],ts,p[1],float(p[2]),float(p[3]),i]; rows.append(r); tasks.update(ts); couriers.add(p[1])
 return rows,sorted(tasks),sorted(couriers)

def serialize(rows):
 out=['task_id_list\tcourier_id\ttotal_score\twillingness']
 for k,ts,c,sc,w,i in rows: out.append(f'{k}\t{c}\t{sc:.6f}\t{w:.6f}')
 return '\n'.join(out)+'\n'

def subset_variant(rows,tasks,couriers,nt,nc,wscale=1.0,score_scale=1.0,bundle_scale=1.0,seed=0,keep_bundles=True):
 rng=random.Random(seed); T=set(tasks[:nt]); C=set(couriers[:nc]); out=[]; idx=0
 for k,ts,c,sc,w,i in rows:
  if c not in C or not set(ts)<=T: continue
  if len(ts)>1 and not keep_bundles: continue
  sc2=sc*(bundle_scale if len(ts)>1 else score_scale)
  w2=max(.0001,min(.9999,w*wscale))
  out.append([k,ts,c,sc2,w2,idx]); idx+=1
 return serialize(out)

def metrics(text):
 C,T=parse(text)[:2]; t=time.monotonic(); out=s.solve(text); dt=time.monotonic()-t; sc=s._solution_expected_cost(out,C,set(T)); cov=set(); used=set(); lens=collections.Counter(); ks=collections.Counter()
 lut={(r[0],r[2]):r for r in C}
 valid=True
 for k,cs in out:
  rr=[lut.get((k,c)) for c in cs]
  rr=[r for r in rr if r]
  if not rr: valid=False; continue
  if any(c in used for c in cs): valid=False
  used.update(cs); cov.update(rr[0][1]); lens[len(rr[0][1])]+=1; ks[len(cs)]+=1
 return {'score':sc,'time':dt,'covered':len(cov),'tasks':len(T),'groups':len(out),'task_lens':dict(lens),'k_lens':dict(ks),'valid':valid}

def simple_baselines(text):
 C,T=parse(text)[:2]
 bytask=collections.defaultdict(list)
 for r in C:
  if len(r[1])==1: bytask[r[1][0]].append(r)
 # K2 top willingness with courier conflicts greedy by task difficulty
 used=set(); out=[]
 order=sorted(T,key=lambda t:max([r[4] for r in bytask[t]] or [0]))
 for t in order:
  cand=[r for r in sorted(bytask[t],key=lambda r:(-r[4],r[3])) if r[2] not in used][:2]
  if cand:
   used.update(r[2] for r in cand); out.append((cand[0][0],[r[2] for r in cand]))
 return s._solution_expected_cost(out,C,set(T)),len(out)

def main():
 rows,tasks,couriers=parse(DATA.read_text())
 cases=[]
 for nt,nc in [(30,60),(30,45),(40,40),(35,45)]:
  for ws in [.22,.3,.7,1.0]:
   for bs in [.55,1.0]:
    if nc>len(couriers) or nt>len(tasks): continue
    text=subset_variant(rows,tasks,couriers,nt,nc,wscale=ws,score_scale=.82 if ws<.5 else 1.0,bundle_scale=bs,seed=nt*100+nc)
    m=metrics(text); k2,k2n=simple_baselines(text); print('done',nt,nc,ws,bs,m['score'],m['time'],flush=True)
    m.update({'nt':nt,'nc':nc,'wscale':ws,'bundle_scale':bs,'k2topw':k2,'k2n':k2n,'gap_vs_k2':m['score']-k2})
    cases.append(m)
 cases.sort(key=lambda x:x['gap_vs_k2'],reverse=True)
 print('worst_vs_k2')
 for m in cases[:25]: print(json.dumps(m,ensure_ascii=False))
 print('\nbest_solver_cases')
 for m in sorted(cases,key=lambda x:x['score'])[:10]: print(json.dumps(m,ensure_ascii=False))
 print('\nscarce_like_bad')
 for m in sorted([x for x in cases if x['nc']<=x['nt']+5],key=lambda x:x['score'],reverse=True)[:15]: print(json.dumps(m,ensure_ascii=False))
if __name__=='__main__': main()
