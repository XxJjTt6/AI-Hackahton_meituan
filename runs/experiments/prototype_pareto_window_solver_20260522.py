#!/usr/bin/env python3
from __future__ import annotations
import importlib.util,pathlib,itertools,time,sys,json
ROOT=pathlib.Path(__file__).resolve().parents[2]
SOLVER=ROOT/'runs/baselines/official_best_7046558e_robust_cache.py'
spec=importlib.util.spec_from_file_location('s',SOLVER); s=importlib.util.module_from_spec(spec); spec.loader.exec_module(s)
orig=s._search_column_window

def pareto_rows(rows, task_count, limit):
    seed=[]; seen=set()
    orders=[
        lambda c:(s._group_expected_cost([c],task_count),-c[4],c[5]),
        lambda c:(-c[4],c[3],c[5]),
        lambda c:(c[3]/max(c[4],.01),c[5]),
        lambda c:(c[3],-c[4],c[5]),
    ]
    for order in orders:
        for r in sorted(rows,key=order)[:max(3,limit//2)]:
            if r[2] not in seen: seen.add(r[2]); seed.append(r)
    # true Pareto: lower score and higher willingness among unique couriers
    best_by_c={}
    for r in rows:
        old=best_by_c.get(r[2])
        if old is None or (r[3],-r[4],r[5])<(old[3],-old[4],old[5]): best_by_c[r[2]]=r
    vals=list(best_by_c.values())
    front=[]
    for r in vals:
        dominated=False
        for q in vals:
            if q is r: continue
            if q[3]<=r[3]+1e-12 and q[4]>=r[4]-1e-12 and (q[3]<r[3]-1e-12 or q[4]>r[4]+1e-12):
                dominated=True; break
        if not dominated: front.append(r)
    for r in sorted(front,key=lambda c:(s._group_expected_cost([c],task_count),-c[4],c[5]))[:limit]:
        if r[2] not in seen: seen.add(r[2]); seed.append(r)
    return seed[:max(limit, min(len(seed), limit+4))]

def patched(candidates,all_tasks,deadline,top_riders_per_task_key,max_k,option_limit):
    O=deadline; F=s._canonical_candidates(candidates); P=sorted({B for A in F for B in A[1]}); Q={B:A for(A,B)in enumerate(P)}; b={B:A for(A,B)in enumerate(sorted({A[2]for A in F}))}; R={}
    for G in F:
        if all(A in Q for A in G[1]): R.setdefault(G[0],[]).append(G)
    H=[]
    for B in R.values():
        if time.monotonic()>O-.05: break
        D=len(B[0][1]); B=pareto_rows(B,D,top_riders_per_task_key)
        if not B: continue
        S=0
        for c in B[0][1]: S|=1<<Q[c]
        for d in range(1,min(max_k,len(B))+1):
            for K in itertools.combinations(B,d):
                L=0; bad=False
                for G in K:
                    U=1<<b[G[2]]
                    if L&U: bad=True; break
                    L|=U
                if bad: continue
                V=s._group_expected_cost(K,D); W=V-1e2*D
                if W<-1e-9: H.append((W,V,S,L,K))
    if not H: return []
    D=len(P); M=(1<<D)-1; I=[[] for _ in range(D)]
    for A in H:
        e=A[2]
        for X in range(D):
            if e>>X&1: I[X].append(A)
    E=[]; C=0.0; Y=0; Z=0
    for A in sorted(H,key=lambda c:(c[0]/max(1,s._popcount(c[2])),c[0])):
        if A[2]&Y or A[3]&Z: continue
        Y|=A[2]; Z|=A[3]; E.append(A); C+=A[0]
    if C>0: E=[]; C=0.0
    for f in I: f.sort(key=lambda c:(c[0],len(c[4]),c[4][0][0],tuple(A[2] for A in c[4])))
    g=[min(0.0,min((A[0] for A in A),default=0.0)) for A in I]; J=[]
    def lb(mask,cur):
        A=M&~mask; B=cur
        while A:
            Cc=A&-A; idx=Cc.bit_length()-1; B+=g[idx]; A^=Cc
        return B
    def choose(mask,cmask):
        A=M&~mask; bi=None; bl=[]
        while A:
            F=A&-A; idx=F.bit_length()-1; opts=[A for A in I[idx] if not A[2]&mask and not A[3]&cmask]
            if bi is None or len(opts)<len(bl):
                bi=idx; bl=opts
                if not opts: break
            A^=F
        return bi,bl
    def dfs(mask,cmask,cur):
        nonlocal E,C
        if time.monotonic()>O-.02: return
        if lb(mask,cur)>=C-1e-9: return
        if mask==M:
            if cur<C-1e-9: C=cur; E=list(J)
            return
        idx,opts=choose(mask,cmask)
        if idx is None:
            if cur<C-1e-9: C=cur; E=list(J)
            return
        # slightly wider effective option limit for pareto since rows are diverse
        for opt in opts[:max(option_limit, option_limit+20)]:
            J.append(opt); dfs(mask|opt[2],cmask|opt[3],cur+opt[0]); J.pop()
        dfs(mask|1<<idx,cmask,cur)
    dfs(0,0,0.0)
    out=[]
    for A in sorted(E,key=lambda c:(min(A[5] for A in c[4]),c[4][0][0],tuple(A[2] for A in c[4]))):
        B=sorted(A[4],key=lambda c:(c[3],-c[4],c[5])); out.append((B[0][0],[A[2] for A in B]))
    return out

def parse(text):
    rows=[]; T=set(); lines=text.strip().splitlines(); st=1 if lines and lines[0].startswith('task') else 0
    for i,l in enumerate(lines[st:]):
        p=l.split('\t'); ts=tuple(x.strip() for x in p[0].split(',') if x.strip()); rows.append((p[0],ts,p[1],float(p[2]),float(p[3]),i)); T.update(ts)
    return rows,T

def run(path):
    text=pathlib.Path(path).read_text(); C,T=parse(text)
    s._search_column_window=orig; base=s.solve(text); bc=s._solution_expected_cost(base,C,T)
    s._search_column_window=patched; t=time.monotonic(); cand=s.solve(text); cc=s._solution_expected_cost(cand,C,T)
    print(json.dumps({'case':pathlib.Path(path).name,'base':bc,'pareto':cc,'delta':cc-bc,'groups':len(cand),'time':time.monotonic()-t},ensure_ascii=False))
    if cc<bc-1e-9: print(cand)
for p in sys.argv[1:]: run(p)
