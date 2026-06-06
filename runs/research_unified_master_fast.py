#!/usr/bin/env python3
import sys,time,importlib.util,itertools,collections,heapq
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('base',ROOT/'solver.py'); base=importlib.util.module_from_spec(spec); spec.loader.exec_module(base)
sys.path.insert(0,str(ROOT/'runs'))
import proxy_eval

def best_combos(rs,task_count,top_riders=8,kmax=4,keep=8):
    # choose diverse riders by several single-row metrics
    pool=[]; seen=set()
    orders=[lambda r:(base._group_expected_cost([r],task_count),-r[4],r[5]), lambda r:(-r[4],r[3],r[5]), lambda r:(r[3],-r[4],r[5])]
    for key in orders:
        for r in sorted(rs,key=key)[:top_riders]:
            if r[2] not in seen: seen.add(r[2]); pool.append(r)
    pool=pool[:top_riders]
    cand=[]
    for k in range(1,min(kmax,len(pool))+1):
        for comb in itertools.combinations(pool,k):
            cost=base._group_expected_cost(comb,task_count); gain=100*task_count-cost
            if gain>0: cand.append((gain,cost,comb))
    return sorted(cand,key=lambda x:(-x[0],x[1],len(x[2])))[:keep]

def solve_master(text,top_riders=7,kmax=3,keep=6,beam=5000,sec=7.0):
    rows,tasks,couriers=proxy_eval.parse(text); T=set(tasks); ti={t:i for i,t in enumerate(sorted(T))}; ci={c:i for i,c in enumerate(sorted(couriers))}
    by={}
    for r in rows: by.setdefault(r[0],[]).append(r)
    cols=[]; start=time.monotonic()
    for key,rs in by.items():
        if time.monotonic()>start+sec*.35: break
        ts=rs[0][1]; tm=sum(1<<ti[t] for t in ts); tc=len(ts)
        for gain,cost,comb in best_combos(rs,tc,top_riders,kmax,keep):
            cm=0
            for r in comb: cm|=1<<ci[r[2]]
            cols.append((gain,cost,tm,cm,comb))
    cols.sort(key=lambda c:(base._popcount(c[2]),c[0],c[0]/max(1,base._popcount(c[3]))),reverse=True)
    states={(0,0):(0,())}; deadline=start+sec
    for i,c in enumerate(cols):
        if time.monotonic()>deadline-.05: break
        g,cost,tm,cm,comb=c; adds=[]
        for key,(val,path) in states.items():
            a,b=key
            if a&tm or b&cm: continue
            nk=(a|tm,b|cm); nv=val+g; old=states.get(nk)
            if old is None or nv>old[0]: adds.append((nk,(nv,path+(i,))))
        for k,v in adds: states[k]=v
        if len(states)>beam*2:
            states=dict(sorted(states.items(),key=lambda kv:(base._popcount(kv[0][0]),kv[1][0]),reverse=True)[:beam])
    # actual objective = 100*uncovered + chosen costs == 100*|T|-gain, so max gain
    key,(val,path)=max(states.items(),key=lambda kv:kv[1][0])
    out=[]
    for i in path:
        comb=cols[i][4]; rr=sorted(comb,key=lambda r:(r[3],-r[4],r[5])); out.append((rr[0][0],[r[2] for r in rr]))
    return out,rows,T,time.monotonic()-start,len(cols),len(states)

def run_case(name,text):
    rows,tasks,couriers=proxy_eval.parse(text); bout=base.solve(text); bcost=base._solution_expected_cost(bout,rows,set(tasks)); bcov=base._solution_covered_count(bout,rows)
    for params in [(6,2,5,3000),(7,3,6,5000),(8,3,8,8000),(8,4,8,8000)]:
        out,rows,T,dt,nc,ns=solve_master(text,*params,sec=8.0); cost=base._solution_expected_cost(out,rows,T); cov=base._solution_covered_count(out,rows)
        print(name,'base',round(bcost,2),bcov,'p',params,'cost',round(cost,2),'cov',cov,'groups',len(out),'cols',nc,'states',ns,'time',round(dt,2), 'k',dict(collections.Counter(len(cs) for _,cs in out)), flush=True)

def main():
    cases=[('large',proxy_eval.DATA.read_text()),('low025',proxy_eval.make_low(.25)),('low030',proxy_eval.make_low(.30)),('scarce40',proxy_eval.make_scarce())]
    for c in cases: run_case(*c)
if __name__=='__main__': main()
