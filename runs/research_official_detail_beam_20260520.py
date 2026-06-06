#!/usr/bin/env python3
import json,glob,os,math,collections

def run(case_idx,beam=60000,per_task=120):
    cols=[]; all_tasks=set(); official=math.inf
    for f in glob.glob('runs/official_submit_*.json'):
        try: c=json.load(open(f))['result']['case_results'][case_idx]
        except Exception: continue
        official=min(official,c['total_score'])
        for d in c.get('detail',[]):
            ts=tuple(x.strip() for x in d['task_id_list'].split(',') if x.strip()); cs=tuple(d['couriers'])
            all_tasks.update(ts); cols.append((float(d['cost']),ts,cs,os.path.basename(f)))
    tasks=sorted(all_tasks); tid={t:i for i,t in enumerate(tasks)}; mp={}
    for cost,ts,cs,src in cols:
        key=(ts,cs)
        if key not in mp or cost<mp[key][0]: mp[key]=(cost,src)
    byfirst=collections.defaultdict(list)
    for (ts,cs),(cost,src) in mp.items():
        tm=0
        for t in ts: tm|=1<<tid[t]
        item=(cost,tm,frozenset(cs),ts,cs,src)
        for t in ts: byfirst[t].append(item)
    for t in tasks: byfirst[t].sort(key=lambda x:x[0]-100*len(x[3])); byfirst[t]=byfirst[t][:per_task]
    states={0:(0.0,frozenset(),())}
    full=(1<<len(tasks))-1
    for i,t in enumerate(tasks):
        bit=1<<i; new=dict(states)
        for mask,(cost,used,path) in states.items():
            if mask&bit: continue
            # unassigned option
            nm=mask|bit; val=cost+100; old=new.get(nm)
            if old is None or val<old[0]: new[nm]=(val,used,path+(('UNASSIGNED',t),))
            for it in byfirst[t]:
                icost,tm,cs,ts,cour,src=it
                if tm&mask or cs&used: continue
                nm=mask|tm; val=cost+icost; nu=used|cs; old=new.get(nm)
                if old is None or val<old[0]: new[nm]=(val,nu,path+(it,))
        if len(new)>beam:
            arr=sorted(new.items(), key=lambda kv:(kv[1][0]+100*(len(tasks)-kv[0].bit_count()), kv[1][0]))[:beam]
            states=dict(arr)
        else: states=new
    best=states.get(full)
    print('case',case_idx,'official',official,'beam',best[0] if best else None,'delta',(best[0]-official) if best else None,'cols',sum(len(v) for v in byfirst.values()))
    if best:
        for x in best[2][:5]: print(' ',x)
for ci in [3,7,0,1,2,4,5,6,8,9]: run(ci)
