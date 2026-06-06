#!/usr/bin/env python3
# LNS over low pair assignment: start from solver output; repeatedly free worst tasks and solve exact pair options within window.
import sys,itertools,random,time,hashlib
from pathlib import Path
sys.path.insert(0,'.'); sys.path.insert(0,'runs')
import solver, proxy_eval
text=proxy_eval.make_low(.25); rows,tasks,couriers=proxy_eval.parse(text); tasks=set(tasks)
base=solver.solve(text); lut={(r[0],r[2]):r for r in rows}
def cost(sol): return solver._solution_expected_cost(sol,rows,tasks)
print('base',round(cost(base),6),{k:sum(len(cs)==k for _,cs in base) for k in range(1,5)})
# keep only single-task rows; windows can choose k=1..3 for each freed task with no duplicate courier.
by={t:[] for t in tasks}
for r in rows:
    if len(r[1])==1: by[r[1][0]].append(r)
for t in tasks: by[t]=sorted(by[t],key=lambda r:(solver._single_expected_cost(r),r[3],-r[4],r[5]))[:16]
cur={k:[lut[(k,c)] for c in cs if (k,c) in lut] for k,cs in base if ',' not in k}
best={k:list(v) for k,v in cur.items()}; bestc=solver._selected_cost(best,tasks)
rng=random.Random(50119); deadline=time.monotonic()+20
iters=0
while time.monotonic()<deadline:
    iters+=1
    # choose worst + related by shared good couriers
    vals=sorted(((solver._group_expected_cost(v,1),k) for k,v in cur.items()), reverse=True)
    seeds=[k for _,k in vals[:8]]; seed=rng.choice(seeds)
    win={seed}
    while len(win)<6:
        # add random among worst not already selected
        win.add(rng.choice([k for _,k in vals[:18] if k not in win]))
    outside={r[2] for k,v in cur.items() if k not in win for r in v}
    opts=[]
    ok=True
    for t in sorted(win):
        arr=[]
        rs=[r for r in by[t] if r[2] not in outside]
        for m in (1,2,3):
            for comb in itertools.combinations(rs,m):
                cs=[r[2] for r in comb]
                if len(cs)!=len(set(cs)): continue
                arr.append((solver._group_expected_cost(comb,1),t,comb))
        arr=sorted(arr,key=lambda x:x[0])[:40]
        if not arr: ok=False; break
        opts.append(arr)
    if not ok: continue
    local_best=[sum(solver._group_expected_cost(cur[t],1) for t in win), None]
    order=sorted(range(len(opts)), key=lambda i: len(opts[i])); stack=[]
    mins=[opts[i][0][0] for i in order]; suf=[0]*(len(order)+1)
    for i in range(len(order)-1,-1,-1): suf[i]=suf[i+1]+mins[i]
    def dfs(pos,used,cc):
        if cc+suf[pos]>=local_best[0]-1e-9: return
        if pos==len(order): local_best[0]=cc; local_best[1]=list(stack); return
        for c,t,comb in opts[order[pos]]:
            cs={r[2] for r in comb}
            if cs&used: continue
            stack.append((t,comb)); dfs(pos+1,used|cs,cc+c); stack.pop()
    dfs(0,set(),0.0)
    if local_best[1]:
        for t,comb in local_best[1]: cur[t]=list(comb)
        cc=solver._selected_cost(cur,tasks)
        if cc<bestc-1e-9:
            bestc=cc; best={k:list(v) for k,v in cur.items()}; print('improve',iters,round(bestc,6),flush=True)
print('final',round(bestc,6),'iters',iters,{k:sum(len(v)==k for v in best.values()) for k in range(1,5)})
