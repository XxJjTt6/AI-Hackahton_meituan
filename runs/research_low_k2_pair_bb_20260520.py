#!/usr/bin/env python3
import argparse, importlib.util, itertools, pathlib, time, math
ROOT=pathlib.Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('solver_mod',ROOT/'solver.py')
s=importlib.util.module_from_spec(spec); spec.loader.exec_module(s)

def parse(text):
    lines=text.strip().splitlines(); off=1 if lines and lines[0].startswith('task') else 0
    C=[]; B=set()
    for idx,line in enumerate(lines[off:]):
        p=line.strip().split('\t')
        if len(p)<4: continue
        tk,cid,cost,prob=p[:4]; tasks=tuple(x.strip() for x in tk.split(',') if x.strip())
        if not tasks or not cid: continue
        try: cost=float(cost); prob=float(prob)
        except: continue
        C.append((tk,tasks,cid,cost,prob,idx)); B.update(tasks)
    return C,B

def k2_bb(C,B,seconds=5,top_singles=24,top_pairs=120):
    deadline=time.monotonic()+seconds
    tasks=sorted(B); couriers=sorted({r[2] for r in C}); cidx={c:i for i,c in enumerate(couriers)}
    by={t:[] for t in tasks}
    for r in s._canonical_candidates([x for x in C if len(x[1])==1]):
        if r[1][0] in by: by[r[1][0]].append(r)
    cols=[]
    for t in tasks:
        rows=sorted(by[t], key=lambda r:(s._single_expected_cost(r), r[3], -r[4], r[5]))[:top_singles]
        opts=[]
        for a,b in itertools.combinations(rows,2):
            if a[2]==b[2]: continue
            cost=s._group_expected_cost([a,b],1)
            mask=(1<<cidx[a[2]])|(1<<cidx[b[2]])
            opts.append((cost,mask,(a,b)))
        opts.sort(key=lambda x:x[0])
        # remove duplicate masks; keep best
        uniq=[]; seen=set()
        for o in opts:
            if o[1] in seen: continue
            seen.add(o[1]); uniq.append(o)
            if len(uniq)>=top_pairs: break
        if not uniq: return []
        cols.append((t,uniq))
    # static lower bound by unconstrained min option
    mincost={t:opts[0][0] for t,opts in cols}
    best=[math.inf,None]
    chosen=[]
    rem_tasks=[t for t,_ in cols]
    def dfs(done, used, cost):
        if time.monotonic()>deadline: return
        if done==len(cols):
            if cost<best[0]: best[0]=cost; best[1]=list(chosen); print('best',best[0],flush=True)
            return
        # cheap admissible lower bound
        lb=cost
        for i in range(done,len(cols)): lb+=mincost[cols[i][0]]
        if lb>=best[0]-1e-9: return
        # dynamic choose remaining task with fewest feasible among next positions
        pick=None; feasible=None; pos=None
        for i in range(done,len(cols)):
            t,opts=cols[i]
            fs=[o for o in opts if not (o[1]&used)]
            if pick is None or len(fs)<len(feasible): pick=t; feasible=fs; pos=i
            if feasible is not None and len(feasible)<=1: break
        if not feasible: return
        cols[done],cols[pos]=cols[pos],cols[done]
        t,opts=cols[done]
        for o in feasible[:80]:
            chosen.append((t,o[2])); dfs(done+1, used|o[1], cost+o[0]); chosen.pop()
        cols[done],cols[pos]=cols[pos],cols[done]
    # greedy incumbent
    used=0; greedy=[]; gcost=0; ok=True
    for t,opts in sorted(cols, key=lambda x:x[1][0][0]):
        found=False
        for o in opts:
            if not (o[1]&used): used|=o[1]; gcost+=o[0]; greedy.append((t,o[2])); found=True; break
        if not found: ok=False; break
    if ok: best[0]=gcost; best[1]=greedy; print('greedy',gcost)
    dfs(0,0,0.0)
    if not best[1]: return []
    return [(t,[a[2],b[2]]) for t,(a,b) in best[1]]

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('input'); ap.add_argument('--seconds',type=float,default=8); args=ap.parse_args()
    text=open(args.input).read(); C,B=parse(text)
    base=s.solve(text); basecost=s._solution_expected_cost(base,C,B)
    print('base',basecost)
    for ts,tp in [(18,60),(24,120),(32,180)]:
        s._GROUP_COST_CACHE={}
        t0=time.monotonic(); r=k2_bb(C,B,args.seconds,ts,tp); dt=time.monotonic()-t0
        if r:
            cost=s._solution_expected_cost(r,C,B); print('bb',ts,tp,'cost',cost,'delta',cost-basecost,'time',dt,'n',len(r))
        else: print('bb',ts,tp,'no result','time',dt)
if __name__=='__main__': main()
