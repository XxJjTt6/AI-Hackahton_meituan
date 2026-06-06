#!/usr/bin/env python3
import json,glob,os,math,time,argparse

def load_case(ci):
    cols=[]; tasks=set(); couriers=set(); best=math.inf
    for f in glob.glob('runs/official_submit_*.json'):
        try: c=json.load(open(f))['result']['case_results'][ci]
        except Exception: continue
        best=min(best,float(c['total_score']))
        for d in c.get('detail',[]):
            ts=tuple(x.strip() for x in d['task_id_list'].split(',') if x.strip())
            cs=tuple(d['couriers']); cost=float(d['cost'])
            tasks.update(ts); couriers.update(cs); cols.append((cost,ts,cs,os.path.basename(f)))
    tasks=sorted(tasks); tid={t:i for i,t in enumerate(tasks)}; cids=sorted(couriers); cid={c:i for i,c in enumerate(cids)}
    uniq={}
    for cost,ts,cs,src in cols:
        key=(ts,cs)
        if key not in uniq or cost<uniq[key][0]: uniq[key]=(cost,src)
    items=[]
    for (ts,cs),(cost,src) in uniq.items():
        tm=0; cm=0
        for t in ts: tm|=1<<tid[t]
        for c in cs: cm|=1<<cid[c]
        items.append((cost,tm,cm,ts,cs,src))
    bytask=[[] for _ in tasks]
    for item in items:
        for t in item[3]: bytask[tid[t]].append(item)
    for b in bytask: b.sort(key=lambda x:(x[0]/len(x[3]),x[0]))
    return tasks,items,bytask,best

def solve(ci,seconds=30):
    tasks,items,bytask,official=load_case(ci); n=len(tasks); full=(1<<n)-1; deadline=time.monotonic()+seconds
    # min possible cost for lower bound, allowing uncovered penalty 100.
    min_task=[]
    for i in range(n):
        vals=[x[0]/len(x[3]) for x in bytask[i]]+[100.0]
        min_task.append(min(vals))
    suffix_min=[0]*(1<<0)  # unused
    best=[official,None]
    nodes=0
    seen={}
    def lb(mask,cost):
        # optimistic lower bound by summing independent per-uncovered-task minimum contribution.
        rem=0.0
        m=(~mask)&full
        while m:
            bit=m & -m; i=bit.bit_length()-1; rem+=min_task[i]; m^=bit
        return cost+rem
    def dfs(mask,used,cost,path):
        nonlocal nodes
        nodes+=1
        if nodes%200000==0 and time.monotonic()>deadline: return
        if lb(mask,cost)>=best[0]-1e-9: return
        key=(mask,used)
        if cost>=seen.get(key,math.inf)-1e-9: return
        seen[key]=cost
        if mask==full:
            if cost<best[0]-1e-9:
                best[0]=cost; best[1]=list(path); print('IMPROVE case',ci,best[0],best[0]-official,'nodes',nodes,flush=True)
            return
        if time.monotonic()>deadline: return
        # choose uncovered task with fewest feasible options under current used/mask.
        rem_bits=[i for i in range(n) if not (mask>>i)&1]
        pick=None; feasible=None
        for i in rem_bits:
            opts=[x for x in bytask[i] if not (x[1]&mask) and not (x[2]&used)]
            # include unassigned option as fallback
            if pick is None or len(opts)<len(feasible): pick=i; feasible=opts
            if feasible is not None and len(feasible)<=1: break
        # unassigned option costs 100 and covers only this task.
        dfs(mask|(1<<pick),used,cost+100,path+[('UNASSIGNED',tasks[pick])])
        for item in feasible[:120]:
            ic,tm,cm,ts,cs,src=item
            dfs(mask|tm,used|cm,cost+ic,path+[item])
    dfs(0,0,0.0,[])
    print('DONE case',ci,'tasks',n,'unique_cols',len(items),'official',official,'best_visible',best[0],'delta',best[0]-official,'nodes',nodes,'seen',len(seen))
    if best[1]:
        for x in best[1][:20]: print(' ',x)
for ci in [3,7]: solve(ci,seconds=25)
