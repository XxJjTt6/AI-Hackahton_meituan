#!/usr/bin/env python3
import sys,time,importlib.util,itertools,hashlib,collections
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('base',ROOT/'solver.py'); base=importlib.util.module_from_spec(spec); spec.loader.exec_module(base)
sys.path.insert(0,str(ROOT/'runs'))
import proxy_eval

def parse(text): return proxy_eval.parse(text)
def masks(rows,tasks):
    tl=sorted(tasks); ti={t:i for i,t in enumerate(tl)}; cl=sorted({r[2] for r in rows}); ci={c:i for i,c in enumerate(cl)}; return tl,ti,cl,ci

def gen_columns(rows,tasks,top=8,kmax=3,limit_per_key=10):
    tl,ti,cl,ci=masks(rows,tasks); by={}
    for r in rows: by.setdefault(r[0],[]).append(r)
    cols=[]
    for key,rs in by.items():
        task_tuple=rs[0][1]; tm=0
        for t in task_tuple: tm|=1<<ti[t]
        # unique best per courier for this key
        best={}
        for r in rs:
            old=best.get(r[2])
            if old is None or base._group_expected_cost([r],len(task_tuple))<base._group_expected_cost([old],len(task_tuple)): best[r[2]]=r
        rs=sorted(best.values(), key=lambda r:(base._group_expected_cost([r],len(task_tuple)),-r[4],r[5]))[:top]
        cand=[]
        for k in range(1,min(kmax,len(rs))+1):
            for comb in itertools.combinations(rs,k):
                cm=0
                for r in comb: cm|=1<<ci[r[2]]
                cost=base._group_expected_cost(comb,len(task_tuple)); gain=100*len(task_tuple)-cost
                if gain>1e-9: cand.append((gain,cost,tm,cm,comb))
        cand=sorted(cand,key=lambda x:(-x[0]/max(1,len(x[4])),-x[0],x[1]))[:limit_per_key]
        cols.extend(cand)
    return cols,tl,cl

def pack(cols,tasks,beam=6000,deadline=None,coverage_weight=0):
    # states key=(taskmask,courmask), value=(gain,path)
    states={(0,0):(0,())}; best=(0,())
    cols=sorted(cols,key=lambda c:(base._popcount(c[2]),c[0]/max(1,base._popcount(c[3])),c[0]),reverse=True)
    for i,c in enumerate(cols):
        if deadline and time.monotonic()>deadline: break
        g,cost,tm,cm,rows=c; add=[]
        for (tmask,cmask),(val,path) in states.items():
            if tmask&tm or cmask&cm: continue
            nv=val+g; key=(tmask|tm,cmask|cm)
            old=states.get(key)
            if old is None or nv>old[0]+1e-9: add.append((key,(nv,path+(i,))))
            if nv+coverage_weight*base._popcount(tmask|tm)>best[0]+coverage_weight*base._popcount(key[0]): best=(nv,path+(i,))
        for k,v in add: states[k]=v
        if len(states)>beam*2:
            items=sorted(states.items(), key=lambda kv:(kv[1][0]+coverage_weight*base._popcount(kv[0][0]), base._popcount(kv[0][0])), reverse=True)[:beam]
            states=dict(items)
    # choose min actual cost including penalties
    best_key,best_val=max(states.items(), key=lambda kv:(kv[1][0]+100*base._popcount(kv[0][0]), base._popcount(kv[0][0])))
    return [cols[i] for i in best_val[1]]

def solve_unified(text,top=8,kmax=3,limit=10,beam=8000,sec=7.5):
    rows,tasks,couriers=parse(text); T=set(tasks); start=time.monotonic(); cols,tl,cl=gen_columns(rows,tasks,top,kmax,limit)
    chosen=pack(cols,tasks,beam,start+sec,coverage_weight=100)
    out=[]
    for g,cost,tm,cm,comb in chosen:
        rr=sorted(comb,key=lambda r:(r[3],-r[4],r[5])); out.append((rr[0][0],[r[2] for r in rr]))
    return sorted(out,key=lambda x:x[0]),rows,T

def eval_case(name,text):
    bmod=base; bout=bmod.solve(text); rows,tasks,couriers=parse(text); T=set(tasks)
    bcost=bmod._solution_expected_cost(bout,rows,T); bcov=bmod._solution_covered_count(bout,rows)
    for params in [(6,2,8,5000),(8,3,8,8000),(10,3,12,10000),(10,4,10,12000)]:
        t=time.monotonic(); out,rows,T=solve_unified(text,*params,sec=8.0); dt=time.monotonic()-t
        cost=base._solution_expected_cost(out,rows,T); cov=base._solution_covered_count(out,rows); kd=collections.Counter(len(cs) for _,cs in out)
        print(name,'base',round(bcost,2),bcov,'params',params,'cost',round(cost,2),'cov',cov,'groups',len(out),'k',dict(kd),'time',round(dt,2))

def main():
    DATA=proxy_eval.DATA.read_text()
    cases=[('large',DATA),('low025',proxy_eval.make_low(.25)),('low030',proxy_eval.make_low(.30)),('scarce40',proxy_eval.make_scarce())]
    for name,text in cases: eval_case(name,text)
if __name__=='__main__': main()
