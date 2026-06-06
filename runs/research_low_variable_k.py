#!/usr/bin/env python3
import sys,time,importlib.util,itertools,collections
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('base',ROOT/'solver.py'); base=importlib.util.module_from_spec(spec); spec.loader.exec_module(base)

def parse_text(path):
    text=Path(path).read_text(); lines=text.strip().splitlines(); start=1 if lines and lines[0].startswith('task') else 0
    rows=[]; tasks=set(); cour=set()
    for i,ln in enumerate(lines[start:]):
        p=ln.split('\t');
        if len(p)<4: continue
        k,c,sc,w=p[:4]; ts=tuple(k.split(',')); rows.append((k,ts,c,float(sc),float(w),i)); tasks.update(ts); cour.add(c)
    return text,rows,sorted(tasks),sorted(cour)

def columns(rows,tasks,top=8,kmax=4,keep=12):
    by={t:[] for t in tasks}
    for r in rows:
        if len(r[1])==1: by[r[1][0]].append(r)
    cols=[]
    for t,rs in by.items():
        pool=[]; seen=set()
        for key in [lambda r:(base._single_expected_cost(r),r[5]), lambda r:(-r[4],r[3]), lambda r:(r[3],-r[4])]:
            for r in sorted(rs,key=key)[:top]:
                if r[2] not in seen: seen.add(r[2]); pool.append(r)
        cand=[]
        for k in range(1,min(kmax,len(pool))+1):
            for comb in itertools.combinations(pool,k):
                cost=base._group_expected_cost(comb,1); cand.append((cost,t,comb))
        cand=sorted(cand,key=lambda x:x[0])[:keep]
        cols.extend(cand)
    return cols

def solve_var(rows,tasks,couriers,top=10,kmax=4,keep=12,beam=20000,sec=8):
    start=time.monotonic(); ci={c:i for i,c in enumerate(couriers)}; ti={t:i for i,t in enumerate(tasks)}
    cols=columns(rows,tasks,top,kmax,keep); items=[]
    for cost,t,comb in cols:
        cm=0
        for r in comb: cm|=1<<ci[r[2]]
        items.append((100-cost,cost,1<<ti[t],cm,t,comb))
    items.sort(reverse=True)
    states={(0,0):(0,())}; full=(1<<len(tasks))-1
    for i,it in enumerate(items):
        if time.monotonic()>start+sec-.05: break
        gain,cost,tm,cm,t,comb=it; add=[]
        for (a,b),(val,path) in list(states.items()):
            if a&tm or b&cm: continue
            nk=(a|tm,b|cm); nv=val+gain; old=states.get(nk)
            if old is None or nv>old[0]: add.append((nk,(nv,path+(i,))))
        for k,v in add: states[k]=v
        if len(states)>beam*2:
            states=dict(sorted(states.items(),key=lambda kv:(kv[0][0].bit_count(),kv[1][0]),reverse=True)[:beam])
    best=max(states.items(),key=lambda kv:(kv[0][0].bit_count(),kv[1][0]))
    out=[]
    for i in best[1][1]:
        comb=items[i][5]; rr=sorted(comb,key=lambda r:(r[3],-r[4],r[5])); out.append((rr[0][0],[r[2] for r in rr]))
    return out,len(items),len(states),time.monotonic()-start

def eval_file(path):
    text,rows,tasks,cour=parse_text(path); baseout=base.solve(text); basecost=base._solution_expected_cost(baseout,rows,set(tasks)); print('base',basecost,base._solution_covered_count(baseout,rows),collections.Counter(len(cs) for _,cs in baseout))
    for p in [(8,3,10,12000),(10,3,14,20000),(10,4,14,25000),(12,4,18,30000)]:
        out,n,s,dt=solve_var(rows,tasks,cour,*p,sec=8); print('p',p,'cost',base._solution_expected_cost(out,rows,set(tasks)),'cov',base._solution_covered_count(out,rows),'groups',len(out),'k',collections.Counter(len(cs) for _,cs in out),'cols',n,'states',s,'time',dt)
if __name__=='__main__': eval_file(sys.argv[1])
