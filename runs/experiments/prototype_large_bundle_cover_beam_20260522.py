#!/usr/bin/env python3
import importlib.util, pathlib, itertools, time, heapq, collections
ROOT=pathlib.Path(__file__).resolve().parents[2]
SOLVER=ROOT/'runs/baselines/official_best_7046558e_robust_cache.py'
DATA=ROOT/'Fwd_ 【美团AI Hackathon大赛】-【命题四AutoSolver：让AI Agent 自主求解配送分配问题】脱敏数据/large_seed301.txt'
spec=importlib.util.spec_from_file_location('s',SOLVER); s=importlib.util.module_from_spec(spec); spec.loader.exec_module(s)
text=DATA.read_text(); base_out=s.solve(text)
rows=[]; by_key=collections.defaultdict(list); tasks=set(); couriers=set()
for i,ln in enumerate(text.strip().splitlines()[1:]):
    p=ln.split('\t'); tl=tuple(x.strip() for x in p[0].split(',') if x.strip())
    r=(p[0],tl,p[1],float(p[2]),float(p[3]),i); rows.append(r); by_key[p[0]].append(r); tasks.update(tl); couriers.add(p[1])
tasks=sorted(tasks); tidx={t:i for i,t in enumerate(tasks)}; cidx={c:i for i,c in enumerate(sorted(couriers))}
full=(1<<len(tasks))-1
base=s._solution_expected_cost(base_out,rows,set(tasks))
print('base',base,'groups',len(base_out), flush=True)
# generate columns for each input key: choose up to 4 couriers, keep best few
def keymask(tl):
    m=0
    for t in tl: m|=1<<tidx[t]
    return m
cols_by_task=collections.defaultdict(list); allcols=[]
for key,rs0 in by_key.items():
    tl=rs0[0][1]; k=len(tl)
    # top rows by single row group cost and willingness; bundles are noisy, keep wider
    rs=sorted(rs0,key=lambda r:(s._group_expected_cost([r],k), -r[4], r[3], r[5]))[:10 if k==1 else 8]
    raw=[]
    for q in range(1, min(4,len(rs))+1):
        for comb in itertools.combinations(rs,q):
            cm=0
            for r in comb: cm |= 1<<cidx[r[2]]
            cost=s._group_expected_cost(list(comb),k)
            # dominance: one column only useful if better than abandoning covered tasks
            if cost < 100*k-1e-9:
                raw.append((cost,keymask(tl),cm,key,tuple(r[2] for r in comb),comb))
    # include base output exact group
    for bk,bcs in base_out:
        if bk==key:
            lut={(r[0],r[2]):r for r in rows}
            comb=tuple(lut[(bk,c)] for c in bcs if (bk,c) in lut)
            if comb:
                cm=0
                for r in comb: cm|=1<<cidx[r[2]]
                raw.append((s._group_expected_cost(list(comb),k),keymask(tl),cm,key,tuple(r[2] for r in comb),comb))
    best={}
    for col in raw:
        old=best.get(col[2])
        if old is None or col[0]<old[0]: best[col[2]]=col
    keep=18 if k==1 else 10
    for col in sorted(best.values(),key=lambda x:x[0])[:keep]:
        allcols.append(col)
        for t in tl: cols_by_task[t].append(col)
for t in tasks: cols_by_task[t].sort(key=lambda x:(x[0]/(x[1].bit_count()), x[0]))
min_single={}
for t in tasks:
    singles=[c for c in cols_by_task[t] if c[1]==(1<<tidx[t])]
    min_single[t]=min(c[0] for c in singles)
print('columns',len(allcols),'bylen',collections.Counter(c[1].bit_count() for c in allcols), flush=True)
# baseline state path for feasibility
base_cols=[]
for key,bcs in base_out:
    m=0; cm=0; comb=[]; lut={(r[0],r[2]):r for r in rows}
    for c in bcs:
        r=lut[(key,c)]; comb.append(r); cm|=1<<cidx[c]
    base_cols.append((s._group_expected_cost(comb,len(comb[0][1])),keymask(comb[0][1]),cm,key,tuple(bcs),tuple(comb)))
# Beam: choose first uncovered task with fewest compatible cols in static list.
beam=[(0.0,0,0,[])]
BEAM=30000
for step in range(40):
    nb={}
    for cost,tmask,cmask,sol in beam:
        if tmask==full:
            old=nb.get((tmask,cmask));
            if old is None or cost<old[0]: nb[(tmask,cmask)]=(cost,tmask,cmask,sol)
            continue
        uncovered=[t for t in tasks if not (tmask>>tidx[t])&1]
        # dynamic choose uncovered with least feasible first 60 columns
        bestt=None; bestlist=None
        for t in uncovered[:]:
            feasible=[]
            for col in cols_by_task[t][:80]:
                if col[1]&tmask: continue
                if col[2]&cmask: continue
                feasible.append(col)
                if len(feasible)>=35: break
            if bestlist is None or len(feasible)<len(bestlist): bestt=t; bestlist=feasible
            if bestlist is not None and len(bestlist)<=1: break
        for col in bestlist or []:
            nc=cost+col[0]; nt=tmask|col[1]; nm=cmask|col[2]
            key=(nt,nm)
            old=nb.get(key)
            if old is None or nc<old[0]: nb[key]=(nc,nt,nm,sol+[col])
    arr=list(nb.values())
    if not arr: print('dead',step); break
    # lower bound uncovered min singles ignoring conflicts
    def rank(st):
        cost,tmask,cmask,sol=st
        lb=cost+sum(min_single[t] for t in tasks if not (tmask>>tidx[t])&1)
        return lb, cost
    if len(arr)>BEAM: arr=heapq.nsmallest(BEAM,arr,key=rank)
    # keep baseline as fallback
    beam=arr
    best_complete=[x for x in beam if x[1]==full]
    print('step',step+1,'beam',len(beam),'bestlb',rank(min(beam,key=rank))[0],'complete',min([x[0] for x in best_complete], default=None), flush=True)
    if best_complete and step>20:
        # continue some steps due states complete carried
        pass
best=min([x for x in beam if x[1]==full], key=lambda x:x[0], default=None)
if not best:
    print('no complete'); raise SystemExit
sol=[(c[3],list(c[4])) for c in best[3]]
score=s._solution_expected_cost(sol,rows,set(tasks))
print('best',score,'delta',score-base,'groups',len(sol),'bundles',sum(1 for k,cs in sol if len(k.split(','))>1),'couriers',sum(len(cs) for k,cs in sol), flush=True)
for g in sorted(sol): print(g)
