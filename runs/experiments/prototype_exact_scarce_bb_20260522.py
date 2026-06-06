#!/usr/bin/env python3
"""Exact-ish branch-and-bound for scarce single-courier set packing.

This is a new algorithm direction: treat scarce as prize-collecting set packing with
one row per courier group, not local repack. It branches on uncovered tasks and uses
upper/lower bounds in saved-cost space.
"""
from __future__ import annotations
import importlib.util,pathlib,time,sys,json,collections
ROOT=pathlib.Path(__file__).resolve().parents[2]
SOLVER=ROOT/'runs/baselines/official_best_7046558e_robust_cache.py'
spec=importlib.util.spec_from_file_location('s',SOLVER); s=importlib.util.module_from_spec(spec); spec.loader.exec_module(s)

def parse(text):
    rows=[]; tasks=set(); lines=text.strip().splitlines(); st=1 if lines and lines[0].startswith('task') else 0
    for i,l in enumerate(lines[st:]):
        p=l.split('\t')
        if len(p)<4: continue
        ts=tuple(x.strip() for x in p[0].split(',') if x.strip())
        r=(p[0],ts,p[1],float(p[2]),float(p[3]),i); rows.append(r); tasks.update(ts)
    return rows,sorted(tasks)

def build_columns(C,tasks,top_per_key=4):
    ti={t:i for i,t in enumerate(tasks)}; ci={c:i for i,c in enumerate(sorted({r[2] for r in C}))}
    by=collections.defaultdict(list)
    for r in s._canonical_candidates(C):
        if len(r[1])<=2: by[r[0]].append(r)
    cols=[]
    for key,rs in by.items():
        task_mask=0
        for t in rs[0][1]: task_mask|=1<<ti[t]
        tc=len(rs[0][1])
        # one courier column; exact over input rows, but prune dominated rows per key/courier/key order
        best_by_c={}
        for r in rs:
            old=best_by_c.get(r[2])
            if old is None or s._group_expected_cost([r],tc)<s._group_expected_cost([old],tc)-1e-12:
                best_by_c[r[2]]=r
        rows=sorted(best_by_c.values(),key=lambda r:(s._group_expected_cost([r],tc),-r[4],r[5]))[:top_per_key]
        for r in rows:
            cost=s._group_expected_cost([r],tc); gain=100*tc-cost
            if gain>1e-9:
                cols.append((gain,cost,task_mask,1<<ci[r[2]],r[0],r[2],r))
    # Add all very good singles/bundles even outside top_per_key by absolute gain
    extra=[]
    for key,rs in by.items():
        tc=len(rs[0][1]); task_mask=0
        for t in rs[0][1]: task_mask|=1<<ti[t]
        for r in rs:
            cost=s._group_expected_cost([r],tc); gain=100*tc-cost
            if gain>70 or (tc==2 and gain>115): extra.append((gain,cost,task_mask,1<<ci[r[2]],r[0],r[2],r))
    sig={(c[2],c[3],c[4]) for c in cols}
    for c in sorted(extra,reverse=True)[:500]:
        sg=(c[2],c[3],c[4])
        if sg not in sig: sig.add(sg); cols.append(c)
    return cols,ti,ci

def greedy_inc(cols,n):
    usedt=usedc=0; gain=0; path=[]
    for i,c in sorted(enumerate(cols),key=lambda x:(x[1][0]/max(1,x[1][2].bit_count()),x[1][0]),reverse=True):
        if usedt&c[2] or usedc&c[3]: continue
        usedt|=c[2]; usedc|=c[3]; gain+=c[0]; path.append(i)
    return gain,usedt,usedc,path

def solve_bb(C,tasks,inc=None,seconds=8.0,top_per_key=5,max_cols=1500):
    cols,ti,ci=build_columns(C,tasks,top_per_key=top_per_key)
    if inc:
        lut={(r[0],r[2]):r for r in C}
        for key,cs in inc:
            for courier in cs:
                r=lut.get((key,courier))
                if not r or len(r[1])>2 or r[2] not in ci: continue
                tm=0
                for t in r[1]: tm|=1<<ti[t]
                cost=s._group_expected_cost([r],len(r[1])); gain=100*len(r[1])-cost
                if gain>1e-9: cols.append((gain,cost,tm,1<<ci[r[2]],r[0],r[2],r))
    # keep best diverse columns
    
    # prune but force incumbent signatures to survive when present
    incsig=set()
    if inc:
        for key,cs in inc:
            for courier in cs: incsig.add((key,courier))
    forced=[c for c in cols if (c[4],c[5]) in incsig]
    rest=[c for c in cols if (c[4],c[5]) not in incsig]
    rest=sorted(rest,key=lambda c:(c[0]/max(1,c[2].bit_count()),c[0],-c[1]),reverse=True)[:max(0,max_cols-len(forced))]
    cols=forced+rest
    n=len(tasks); full=(1<<n)-1
    by_task=[[] for _ in range(n)]
    for idx,c in enumerate(cols):
        m=c[2]
        while m:
            b=m&-m; by_task[b.bit_length()-1].append(idx); m^=b
    for lst in by_task: lst.sort(key=lambda i:cols[i][0],reverse=True)
    # optimistic per-task saved bound (overcounts multi-task columns intentionally)
    best_task=[max([cols[i][0]/cols[i][2].bit_count() for i in by_task[t]] or [0.0]) for t in range(n)]
    suffix_cache={}
    def optimistic(mask):
        return sum(best_task[i] for i in range(n) if not (mask>>i)&1)
    best_gain,bm,bc,bpath=greedy_inc(cols,n)
    best_path=list(bpath); nodes=0; deadline=time.monotonic()+seconds
    # choose next task: uncovered with fewest compatible candidates
    def dfs(mask,cmask,gain,path):
        nonlocal best_gain,best_path,nodes
        nodes+=1
        if time.monotonic()>deadline: return
        if gain+optimistic(mask)<=best_gain+1e-9: return
        if gain>best_gain+1e-9:
            best_gain=gain; best_path=list(path)
        if mask==full: return
        best_t=None; opts=None
        rem=full&~mask
        m=rem
        while m:
            b=m&-m; t=b.bit_length()-1
            cand=[i for i in by_task[t] if not (cols[i][2]&mask) and not (cols[i][3]&cmask)]
            if opts is None or len(cand)<len(opts): best_t=t; opts=cand
            if opts is not None and len(opts)<=1: break
            m^=b
        if best_t is None: return
        # branch include promising compatible columns, then skip task (pay penalty)
        for i in opts[:40]:
            c=cols[i]
            dfs(mask|c[2], cmask|c[3], gain+c[0], path+[i])
        dfs(mask | (1<<best_t), cmask, gain, path)
    dfs(0,0,0.0,[])
    sol=[(cols[i][4],[cols[i][5]]) for i in best_path]
    return sol,cols,nodes,best_gain

def run(path):
    text=pathlib.Path(path).read_text(); C,T=parse(text); base=s.solve(text); bc=s._solution_expected_cost(base,C,set(T))
    t=time.monotonic(); sol,cols,nodes,gain=solve_bb(C,T,base,seconds=8.4); sc=s._solution_expected_cost(sol,C,set(T))
    if sc>=bc-1e-9:
        sol=base; sc=bc
    print(json.dumps({'case':pathlib.Path(path).name,'base':bc,'bb':sc,'delta':sc-bc,'covered':len({x for k,_ in sol for x in k.split(',')}),'groups':len(sol),'cols':len(cols),'nodes':nodes,'time':time.monotonic()-t},ensure_ascii=False))
    if sc<bc-1e-9: print(sol)
if __name__=='__main__':
    for p in sys.argv[1:]: run(p)
