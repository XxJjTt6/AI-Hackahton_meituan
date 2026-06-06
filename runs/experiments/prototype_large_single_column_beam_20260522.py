#!/usr/bin/env python3
import importlib.util, pathlib, itertools, time, heapq, math
ROOT=pathlib.Path(__file__).resolve().parents[2]
SOLVER=ROOT/'runs/baselines/official_best_7046558e_robust_cache.py'
DATA=ROOT/'Fwd_ 【美团AI Hackathon大赛】-【命题四AutoSolver：让AI Agent 自主求解配送分配问题】脱敏数据/large_seed301.txt'
spec=importlib.util.spec_from_file_location('s',SOLVER); s=importlib.util.module_from_spec(spec); spec.loader.exec_module(s)
text=DATA.read_text(); out=s.solve(text)
rows=[]; by_task={}; tasks=set(); couriers=set(); ridx={}
for i,ln in enumerate(text.strip().splitlines()[1:]):
    p=ln.split('\t'); tl=tuple(x.strip() for x in p[0].split(',') if x.strip())
    r=(p[0],tl,p[1],float(p[2]),float(p[3]),i); rows.append(r)
    if len(tl)==1: by_task.setdefault(tl[0],[]).append(r)
    tasks.update(tl); couriers.add(p[1])
for i,c in enumerate(sorted(couriers)): ridx[c]=i
base=s._solution_expected_cost(out,rows,tasks)
print('base',base,'groups',len(out), flush=True)
# current columns to force availability
curcols={}
lut={(r[0],r[2]):r for r in rows}
for k,cs in out:
    rr=[lut[(k,c)] for c in cs if (k,c) in lut]
    if rr and len(rr[0][1])==1:
        t=rr[0][1][0]; mask=sum(1<<ridx[r[2]] for r in rr); curcols[t]=(s._group_expected_cost(rr,1),mask,k,tuple(c for c in cs),rr)

def make_cols(t, topn=12, keep=60):
    rs=sorted(by_task[t], key=lambda r:(s._single_expected_cost(r), -r[4], r[3]))[:topn]
    cols=[]
    for k in range(1,5):
        for comb in itertools.combinations(rs,k):
            mask=0; ok=True
            for r in comb:
                bit=1<<ridx[r[2]]
                if mask&bit: ok=False; break
                mask|=bit
            if not ok: continue
            cost=s._group_expected_cost(list(comb),1)
            # reject clearly awful but keep singles
            cols.append((cost,mask,comb[0][0],tuple(r[2] for r in comb),comb))
    if t in curcols: cols.append(curcols[t])
    # de-dup mask keep best
    best={}
    for c in cols:
        old=best.get(c[1])
        if old is None or c[0]<old[0]: best[c[1]]=c
    cols=sorted(best.values(), key=lambda x:x[0])[:keep]
    return cols
cols={t:make_cols(t) for t in sorted(tasks)}
mins={t:cols[t][0][0] for t in cols}
print('cols lens',min(map(len,cols.values())),max(map(len,cols.values())),sum(map(len,cols.values())), flush=True)
# order hard tasks by regret and current position
order=sorted(cols)
# incumbent prefix state protects feasibility
cur_by_task=curcols
cur_prefix=[]
cmask=0; ccost=0.0; csol=[]
for t in order:
    cur_prefix.append((ccost,cmask,list(csol)))
    cc=cur_by_task[t]
    ccost += cc[0]; cmask |= cc[1]; csol.append(cc)
# but lower bound suffix
suf=[0]*(len(order)+1)
for i in range(len(order)-1,-1,-1): suf[i]=suf[i+1]+mins[order[i]]
# beam states cost, mask, solution list
beam=[(0.0,0,[])]
BEAM=5000
for i,t in enumerate(order):
    nb=[]; seen={}
    for cost,mask,sol in beam:
        for cc in cols[t]:
            c,m=cc[0],cc[1]
            if mask&m: continue
            nm=mask|m; nc=cost+c
            old=seen.get(nm)
            if old is None or nc<old[0]:
                seen[nm]=(nc,nm,sol+[cc])
    arr=list(seen.values())
    # score by actual partial cost + optimistic suffix + small used count penalty
    if len(arr)>BEAM:
        arr=heapq.nsmallest(BEAM, arr, key=lambda x:x[0]+suf[i+1])
    # add baseline prefix after choosing this task
    bp=(cur_prefix[i][0]+cur_by_task[t][0], cur_prefix[i][1]|cur_by_task[t][1], cur_prefix[i][2]+[cur_by_task[t]])
    if all(x[1]!=bp[1] for x in arr): arr.append(bp)
    beam=arr
    print(i+1,t,'beam',len(beam),'best_lb',min(x[0] for x in beam)+suf[i+1], flush=True)
    if not beam: break
best=min(beam,key=lambda x:x[0])
sol=[(c[2],list(c[3])) for c in best[2]]
score=s._solution_expected_cost(sol,rows,tasks)
print('beam score',score,'delta',score-base,'groups',len(sol),'couriers',sum(len(c) for _,c in sol))
for g in sorted(sol): print(g)
