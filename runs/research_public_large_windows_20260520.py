#!/usr/bin/env python3
import importlib.util,pathlib,itertools,collections,time,random
ROOT=pathlib.Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('solver_mod',ROOT/'solver.py')
s=importlib.util.module_from_spec(spec); spec.loader.exec_module(s)
P=ROOT/'Fwd_ 【美团AI Hackathon大赛】-【命题四AutoSolver：让AI Agent 自主求解配送分配问题】脱敏数据/large_seed301.txt'
text=P.read_text(); lines=text.strip().splitlines(); C=[]; B=set()
for i,line in enumerate(lines[1:]):
    tk,c,score,w=line.split('\t')[:4]; ts=tuple(tk.split(',')); C.append((tk,ts,c,float(score),float(w),i)); B.update(ts)
row={(r[0],r[2]):r for r in C}; base=s.solve(text); sel=s._result_to_selected(base,row)
print('base',s._solution_expected_cost(base,C,B),collections.Counter(len(v) for v in sel.values()),flush=True)
by={t:[] for t in B}
for r in s._canonical_candidates(C):
    if len(r[1])==1: by[r[1][0]].append(r)
opts={}
for t,rows in by.items():
    seed={r[2]:r for r in sorted(rows,key=lambda r:(s._single_expected_cost(r),r[3],-r[4],r[5]))[:22]}
    for r in sorted(rows,key=lambda r:(-r[4],r[3],r[5]))[:10]: seed.setdefault(r[2],r)
    rows=list(seed.values()); cur=[]
    for k in (1,2,3,4):
        for comb in itertools.combinations(rows,k):
            cs=tuple(r[2] for r in comb)
            if len(cs)!=len(set(cs)): continue
            cost=s._group_expected_cost(comb,1)
            if cost<45: cur.append((cost,cs,tuple(comb)))
    cur.sort(key=lambda x:(x[0],len(x[1]))); opts[t]=cur[:120]
print('opts',sum(map(len,opts.values())),min(map(len,opts.values())),max(map(len,opts.values())),flush=True)
best={t:tuple(v) for t,v in sel.items()}; best_cost=sum(s._group_expected_cost(v,1) for v in best.values())
tasks=sorted(best); rng=random.Random(301); deadline=time.monotonic()+55; improved=0; checked=[0]
for round_no in range(5):
    wins=list(itertools.combinations(tasks,2))+list(itertools.combinations(tasks,3))
    for _ in range(500): wins.append(tuple(rng.sample(tasks,4)))
    rng.shuffle(wins); any_imp=False
    for W in wins:
        if time.monotonic()>deadline: break
        W=set(W); outside={r[2] for t,rs in best.items() if t not in W for r in rs}
        old=sum(s._group_expected_cost(best[t],1) for t in W)
        local=[]
        for t in W:
            cand=[o for o in opts[t] if not (set(o[1])&outside)]
            if not cand: break
            local.append((t,cand[:80]))
        if len(local)!=len(W): continue
        local.sort(key=lambda x:len(x[1])); cur=[]; used=set(); loc_best=[None]; loc_cost=[old]
        def dfs(i,cost):
            checked[0]+=1
            if cost>=loc_cost[0]-1e-10: return
            if i==len(local): loc_best[0]=list(cur); loc_cost[0]=cost; return
            t,cands=local[i]
            for oc,cs,rows in cands:
                st=set(cs)
                if st&used: continue
                used.update(st); cur.append((t,rows,oc)); dfs(i+1,cost+oc); cur.pop(); used.difference_update(st)
        dfs(0,0.0)
        if loc_best[0] and loc_cost[0]<old-1e-9:
            for t,rows,oc in loc_best[0]: best[t]=rows
            best_cost+=loc_cost[0]-old; improved+=1; any_imp=True
            print('improve',improved,'round',round_no,'win',len(W),'delta',loc_cost[0]-old,'cost',best_cost,collections.Counter(len(v) for v in best.values()),flush=True)
    if not any_imp or time.monotonic()>deadline: break
out=[(t,[r[2] for r in sorted(rows,key=lambda r:(r[3],-r[4],r[5]))]) for t,rows in sorted(best.items())]
print('final',s._solution_expected_cost(out,C,B),'delta',s._solution_expected_cost(out,C,B)-s._solution_expected_cost(base,C,B),'improved',improved,'checked',checked[0],'k',collections.Counter(len(x[1]) for x in out))
if improved:
    for x in out: print(x)
