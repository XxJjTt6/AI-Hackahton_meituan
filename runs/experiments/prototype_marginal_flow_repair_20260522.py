#!/usr/bin/env python3
"""Global marginal-flow repair prototype.

Different angle from cache/repack: keep task grouping fixed, but solve courier reassignment
as a global min-cost flow over marginal insertion costs, then evaluate exactly.
This tests whether current solutions are stuck because courier allocation, not grouping, is local.
"""
from __future__ import annotations
import importlib.util, pathlib, time, collections, sys, itertools, json
ROOT=pathlib.Path(__file__).resolve().parents[2]
SOLVER=ROOT/'runs/baselines/official_best_7046558e_robust_cache.py'
spec=importlib.util.spec_from_file_location('s',SOLVER); s=importlib.util.module_from_spec(spec); spec.loader.exec_module(s)

def parse(text):
    lines=text.strip().splitlines(); st=1 if lines and lines[0].startswith('task') else 0
    C=[]; T=set()
    for i,l in enumerate(lines[st:]):
        p=l.split('\t')
        if len(p)<4: continue
        ts=tuple(x.strip() for x in p[0].split(',') if x.strip())
        r=(p[0],ts,p[1],float(p[2]),float(p[3]),i); C.append(r); T.update(ts)
    return C,T

def selected_rows(sol,C):
    lut={(r[0],r[2]):r for r in C}; out={}
    for key,cs in sol:
        rr=[lut.get((key,c)) for c in cs]
        rr=[r for r in rr if r]
        if rr: out[key]=rr
    return out

def repair(sol,C,T,top_per_group=26, max_passes=5):
    by_key_courier={(r[0],r[2]):r for r in C}
    by_group=selected_rows(sol,C)
    # preserve current groups/task keys and group cardinalities; this avoids risky regrouping.
    groups=[]
    used0=set()
    for key,cs in sol:
        rows=[by_key_courier.get((key,c)) for c in cs]
        rows=[r for r in rows if r]
        if not rows: continue
        groups.append([key, rows[0][1], len(rows), list(rows)])
        used0.update(r[2] for r in rows)
    all_couriers=sorted({r[2] for r in C})
    # candidate rows per existing group key only
    cand_by_key=collections.defaultdict(list)
    for r in C:
        cand_by_key[r[0]].append(r)
    for _pass in range(max_passes):
        source=0; gbase=1; cbase=gbase+len(groups); sink=cbase+len(all_couriers)
        mf=s._MinCostFlow(sink+1)
        edge_meta={}
        scale=100000
        # group slots: each selected group demands its current number of couriers.
        for gi,(key,ts,k,cur) in enumerate(groups):
            mf.add_edge(source,gbase+gi,k,0)
            cur_cost=s._group_expected_cost(cur,len(ts))
            pool=[]; seen=set()
            # mix current rows + best marginal rows + high willingness rows
            rows=cand_by_key.get(key,[])
            for order in [lambda r:(s._group_expected_cost([r],len(ts)), -r[4], r[5]), lambda r:(-r[4], r[3], r[5]), lambda r:(r[3]/max(r[4],.01), r[5])]:
                for r in sorted(rows,key=order)[:top_per_group]:
                    if r[2] not in seen: seen.add(r[2]); pool.append(r)
            for r in cur:
                if r[2] not in seen: seen.add(r[2]); pool.append(r)
            # marginal cost is exact delta inserting this row into current group-minus-same-courier rows.
            for r in pool:
                base=[x for x in cur if x[2]!=r[2]]
                before=s._group_expected_cost(base,len(ts)) if base else 100*len(ts)
                after=s._group_expected_cost(base+[r],len(ts))
                marg=after-before
                ci=all_couriers.index(r[2])
                eidx=len(mf.graph[gbase+gi])
                mf.add_edge(gbase+gi,cbase+ci,1,int(round(marg*scale)))
                edge_meta[(gbase+gi,eidx)]=(gi,r)
        for ci,c in enumerate(all_couriers):
            mf.add_edge(cbase+ci,sink,1,0)
        need=sum(g[2] for g in groups)
        if mf.min_cost_flow(source,sink,need)<need:
            break
        new_groups=[[key,ts,k,[]] for key,ts,k,cur in groups]
        for (u,eidx),(gi,r) in edge_meta.items():
            if mf.graph[u][eidx][1]==0:
                new_groups[gi][3].append(r)
        # only accept exact objective improvement
        new_sol=[]
        ok=True
        for key,ts,k,rows in new_groups:
            if len(rows)!=k:
                ok=False; break
            new_sol.append((key,[r[2] for r in rows]))
        if not ok: break
        old=s._solution_expected_cost([(g[0],[r[2] for r in g[3]]) for g in groups],C,T)
        new=s._solution_expected_cost(new_sol,C,T)
        if new<old-1e-9:
            groups=new_groups
        else:
            break
    return [(key,[r[2] for r in rows]) for key,ts,k,rows in groups]

def run(path):
    text=pathlib.Path(path).read_text(); C,T=parse(text); base=s.solve(text); bc=s._solution_expected_cost(base,C,T)
    t=time.monotonic(); cand=repair(base,C,T); cc=s._solution_expected_cost(cand,C,T)
    print(json.dumps({'case':pathlib.Path(path).name,'base':bc,'cand':cc,'delta':cc-bc,'groups':len(cand),'couriers':sum(len(x[1]) for x in cand),'time':time.monotonic()-t},ensure_ascii=False))
    if cc<bc-1e-9: print(cand)
if __name__=='__main__':
    for p in sys.argv[1:]: run(p)
