#!/usr/bin/env python3
import json,glob,os,itertools,math

def solve_case(case_idx):
    cols=[]; all_tasks=set(); best_current=math.inf
    for f in glob.glob('runs/official_submit_*.json'):
        try: data=json.load(open(f)); c=data['result']['case_results'][case_idx]
        except Exception: continue
        best_current=min(best_current,c['total_score'])
        for d in c.get('detail',[]):
            tasks=tuple(x.strip() for x in d['task_id_list'].split(',') if x.strip())
            cour=tuple(d['couriers'])
            all_tasks.update(tasks)
            cols.append((float(d['cost']),tasks,cour,os.path.basename(f)))
    tasks=sorted(all_tasks); tid={t:i for i,t in enumerate(tasks)}
    # unique best by (tasks,couriers)
    mp={}
    for cost,ts,cs,src in cols:
        key=(ts,cs)
        if key not in mp or cost<mp[key][0]: mp[key]=(cost,src)
    items=[]
    for (ts,cs),(cost,src) in mp.items():
        tm=0
        for t in ts: tm|=1<<tid[t]
        items.append((cost,tm,set(cs),ts,cs,src))
    items.sort(key=lambda x:x[0]-100*len(x[3]))
    best=[best_current,None]
    # DFS branch and bound over tasks; penalty 100 per uncovered task.
    bytask=[[] for _ in tasks]
    for item in items:
        for t in item[3]: bytask[tid[t]].append(item)
    for b in bytask: b.sort(key=lambda x:x[0]-100*len(x[3]))
    chosen=[]
    full=(1<<len(tasks))-1
    def lower(mask,cost):
        # admissible: no negative extra beyond current; just current cost + 0 for remaining, weak but safe
        return cost
    seen={}
    def dfs(mask,used,cost):
        total_lb=cost+100*(len(tasks)-mask.bit_count())*0
        if total_lb>=best[0]: return
        key=(mask,tuple(sorted(used)))
        if seen.get(key,math.inf)<=cost+1e-9: return
        seen[key]=cost
        if mask==full:
            if cost<best[0]: best[0]=cost; best[1]=list(chosen); print('case',case_idx,'best',best[0],flush=True)
            return
        # choose uncovered task with fewest feasible columns
        rem=[i for i,t in enumerate(tasks) if not (mask>>i)&1]
        pick=min(rem,key=lambda i:sum(1 for it in bytask[i] if not (it[1]&mask) and not (it[2]&used)))
        # option: leave this task uncovered, but only once via masking it and adding 100
        chosen.append(('UNASSIGNED',tasks[pick])); dfs(mask| (1<<pick),used,cost+100); chosen.pop()
        count=0
        for it in bytask[pick]:
            if it[1]&mask or it[2]&used: continue
            chosen.append(it); dfs(mask|it[1], used|it[2], cost+it[0]); chosen.pop()
            count+=1
            if count>80: break
    dfs(0,set(),0.0)
    print('case',case_idx,'observed cols',len(items),'official_best',best_current,'repacked',best[0],'delta',best[0]-best_current)
    if best[1]:
        for it in best[1][:10]: print(' ',it)
for i in [3,7,0,1,2,4,5,6,8,9]: solve_case(i)
