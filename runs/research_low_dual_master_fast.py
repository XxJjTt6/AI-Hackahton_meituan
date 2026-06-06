#!/usr/bin/env python3
import sys,time,importlib.util,itertools,collections,math,random
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('base',ROOT/'solver.py'); base=importlib.util.module_from_spec(spec); spec.loader.exec_module(base)
sys.path.insert(0,str(ROOT/'runs'))
import proxy_eval

def parse(path):
    text=Path(path).read_text(); return text,*proxy_eval.parse(text)

def gen_task_cols(rows,tasks,top=8,kmax=4,keep=12):
    by={t:[] for t in tasks}
    for r in rows:
        if len(r[1])==1: by[r[1][0]].append(r)
    task_cols={}
    for t,rs in by.items():
        pool=[]; seen=set()
        orders=[lambda r:(base._single_expected_cost(r),r[5]),lambda r:(-r[4],r[3]),lambda r:(r[3],-r[4]),lambda r:(r[3]/max(r[4],1e-6),r[5])]
        for key in orders:
            for r in sorted(rs,key=key)[:top]:
                if r[2] not in seen:seen.add(r[2]);pool.append(r)
        pool=pool[:top]
        cols=[]
        for k in range(1,min(kmax,len(pool))+1):
            for comb in itertools.combinations(pool,k):
                cost=base._group_expected_cost(comb,1); cols.append((cost,tuple(sorted(r[2] for r in comb)),comb))
        cols=sorted(cols,key=lambda x:(x[0],len(x[1])))[:keep]
        task_cols[t]=cols
    return task_cols

def greedy_dual(task_cols,couriers,lmbd,order):
    used=set(); out=[]; total=0
    for t in order:
        best=None; bv=1e9
        for cost,cs,comb in task_cols[t]:
            if any(c in used for c in cs): continue
            v=cost+sum(lmbd.get(c,0) for c in cs)
            if v<bv: bv=v; best=(cost,cs,comb)
        if best:
            cost,cs,comb=best; used.update(cs); total+=cost; rr=sorted(comb,key=lambda r:(r[3],-r[4],r[5])); out.append((t,[r[2] for r in rr]))
    return out,total+100*(len(task_cols)-len(out))

def improve(out,rows,tasks,task_cols,deadline):
    # local destroy/repair by worst 4-8 tasks with exact assignment over their columns
    rowmap={(r[0],r[2]):r for r in rows}; best=out; bestc=base._solution_expected_cost(best,rows,set(tasks)); rng=random.Random(7)
    while time.monotonic()<deadline:
        selected={k:cs for k,cs in best}; costs=[]
        for k,cs in selected.items():
            rr=[rowmap[(k,c)] for c in cs if (k,c) in rowmap]; costs.append((base._group_expected_cost(rr,1),k))
        costs.sort(reverse=True); seeds=[k for _,k in costs[:10]]
        if not seeds: break
        win=set(rng.sample(seeds,min(len(seeds),rng.choice([4,5,6,7]))))
        used={c for k,cs in selected.items() if k not in win for c in cs}
        cols=[]; ti={t:i for i,t in enumerate(sorted(win))}; ci={c:i for i,c in enumerate(sorted({c for t in win for _,cs,_ in task_cols[t] for c in cs if c not in used}))}
        for t in win:
            for cost,cs,comb in task_cols[t]:
                if any(c in used for c in cs): continue
                if any(c not in ci for c in cs): continue
                cm=sum(1<<ci[c] for c in cs); cols.append((100-cost,cost,1<<ti[t],cm,t,comb))
        states={(0,0):(0,())}
        for i,it in enumerate(sorted(cols,reverse=True)):
            g,cost,tm,cm,t,comb=it; add=[]
            for (a,b),(val,path) in list(states.items()):
                if a&tm or b&cm: continue
                nk=(a|tm,b|cm); nv=val+g; old=states.get(nk)
                if old is None or nv>old[0]: add.append((nk,(nv,path+(i,))))
            for k,v in add: states[k]=v
        if not states: continue
        cols=sorted(cols,reverse=True); key,(val,path)=max(states.items(),key=lambda kv:kv[1][0])
        cand=[(k,list(cs)) for k,cs in selected.items() if k not in win]
        for i in path:
            comb=cols[i][5]; rr=sorted(comb,key=lambda r:(r[3],-r[4],r[5])); cand.append((rr[0][0],[r[2] for r in rr]))
        cc=base._solution_expected_cost(cand,rows,set(tasks))
        if cc<bestc-1e-9: best,bestc=cand,cc
    return best

def solve(path):
    text,rows,tasks,couriers=parse(path); task_cols=gen_task_cols(rows,tasks)
    baseout=base.solve(text); basecost=base._solution_expected_cost(baseout,rows,set(tasks)); print('base',basecost,collections.Counter(len(cs) for _,cs in baseout))
    best=baseout; bestc=basecost; start=time.monotonic()
    # dual penalties: encourage scarce couriers by penalizing popular globally good riders
    freq=collections.Counter(c for cols in task_cols.values() for _,cs,_ in cols[:8] for c in cs)
    scenarios=[]
    for alpha in [0,0.5,1.5]:
        lmbd={c:alpha*freq[c] for c in couriers}
        scenarios.append(lmbd)
    orders=[sorted(tasks), sorted(tasks,key=lambda t:len(task_cols[t])), sorted(tasks,key=lambda t:task_cols[t][0][0] if task_cols[t] else 999, reverse=True)]
    for lmbd in scenarios:
        for order in orders:
            out,_=greedy_dual(task_cols,couriers,lmbd,order)
            out=improve(out,rows,tasks,task_cols,start+3.5)
            c=base._solution_expected_cost(out,rows,set(tasks))
            print('cand',c,collections.Counter(len(cs) for _,cs in out))
            if c<bestc: best,bestc=out,c
    print('BEST',bestc,collections.Counter(len(cs) for _,cs in best))
if __name__=='__main__': solve(sys.argv[1])
