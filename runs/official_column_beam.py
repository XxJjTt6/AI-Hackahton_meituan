import json, glob, os
from collections import defaultdict

def tasks_of(k): return tuple(k.split(','))

def beam_case(cols, total_tasks=None):
    present=sorted({t for k,_,_,_,_ in cols for t in tasks_of(k)})
    if total_tasks and present and all(t.startswith('T') and t[1:].isdigit() for t in present):
        tasks=[f'T{i:04d}' for i in range(total_tasks)]
    else:
        tasks=present
    task_index={t:i for i,t in enumerate(tasks)}
    couriers=sorted({c for _,cs,_,_,_ in cols for c in cs})
    courier_index={c:i for i,c in enumerate(couriers)}
    cols=list(cols)+[(t, (), 100.0, 'dummy', None) for t in tasks]
    by_first=defaultdict(list)
    for k,cs,cost,src,detail in cols:
        tm=0
        for t in tasks_of(k): tm |= 1<<task_index[t]
        cm=0
        for c in cs: cm |= 1<<courier_index[c]
        first=(tm&-tm).bit_length()-1
        by_first[first].append((tm,cm,cost,k,cs,src,detail))
    for v in by_first.values():
        v.sort(key=lambda x:(x[2], -x[0].bit_count(), len(x[4])))
        del v[25:]
    full=(1<<len(tasks))-1
    states={(0,0):(0.0,())}
    width=1800 if len(tasks)<=40 else 1000
    for _ in range(len(tasks)):
        nxt={}
        for (mask,cmask),(cost,sol) in states.items():
            if mask==full:
                old=nxt.get((mask,cmask))
                if old is None or cost<old[0]: nxt[(mask,cmask)]=(cost,sol)
                continue
            rem=full^mask; first=(rem&-rem).bit_length()-1
            for it in by_first.get(first,[]):
                tm,cm,c,k,cs,src,d=it
                if tm&mask or cm&cmask: continue
                key=(mask|tm, cmask|cm); val=(cost+c, sol+(it,))
                old=nxt.get(key)
                if old is None or val[0]<old[0]: nxt[key]=val
        if len(nxt)>width:
            states=dict(sorted(nxt.items(), key=lambda kv:(kv[1][0], -kv[0][0].bit_count()))[:width])
        else:
            states=nxt
    return min((v for (m,_),v in states.items() if m==full), key=lambda x:x[0], default=(float('inf'),()))

cases=defaultdict(dict)
for p in glob.glob('runs/official_submit_*.json'):
    try: j=json.load(open(p))['result']
    except Exception: continue
    if float(j.get('avg_score',9999))>706.7153:
        continue
    tag=os.path.basename(p).replace('official_submit_','').replace('.json','')
    for cr in j.get('case_results',[]):
        for d in cr.get('detail',[]):
            k=d['task_id_list']; cs=tuple(d['couriers']); cost=float(d['cost'])
            old=cases[cr['case_file']].get((k,cs))
            if old is None or cost<old[0]: cases[cr['case_file']][(k,cs)]=(cost,tag,d)

best_file=min(glob.glob('runs/official_submit_*.json'), key=lambda p: json.load(open(p))['result'].get('avg_score', 9999))
latest=json.load(open(best_file))['result']
print('[baseline]', best_file, latest.get('avg_score'))
cur_scores={cr['case_file']:float(cr['total_score']) for cr in latest['case_results']}
for case in sorted(cases):
    cols=[(k,cs,cost,src,d) for (k,cs),(cost,src,d) in cases[case].items()]
    total_tasks=next(cr.get('total_tasks') for cr in latest['case_results'] if cr['case_file']==case)
    cost, sol=beam_case(cols,total_tasks)
    delta=cost-cur_scores[case]
    print('\nCASE',case,'cur',round(cur_scores[case],4),'beam',round(cost,4),'delta',round(delta,4),'cols',len(cols))
    if delta < -1e-6:
        for tm,cm,c,k,cs,src,d in sorted(sol, key=lambda x:x[3]):
            if cs: print(' ',k, list(cs), round(c,4), src)
