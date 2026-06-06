# Wider all-column beam for non-bottleneck cases; offline only.
import json, glob, os
from collections import defaultdict

def tasks_of(k): return tuple(k.split(','))
def beam_case(cols,total_tasks):
    present=sorted({t for k,_,_,_,_ in cols for t in tasks_of(k)})
    tasks=[f'T{i:04d}' for i in range(total_tasks)] if present and all(t.startswith('T') and t[1:].isdigit() for t in present) else present
    ti={t:i for i,t in enumerate(tasks)}; ci={c:i for i,c in enumerate(sorted({c for _,cs,_,_,_ in cols for c in cs}))}
    cols=list(cols)+[(t,(),100.0,'dummy',None) for t in tasks]
    by=defaultdict(list)
    for k,cs,cost,src,d in cols:
        tm=0
        ok=True
        for t in tasks_of(k):
            if t not in ti: ok=False; break
            tm|=1<<ti[t]
        if not ok: continue
        cm=0
        for c in cs: cm|=1<<ci[c]
        by[(tm&-tm).bit_length()-1].append((tm,cm,cost,k,cs,src,d))
    for v in by.values():
        v.sort(key=lambda x:(x[2], -x[0].bit_count(), len(x[4])))
        del v[90:]
    full=(1<<len(tasks))-1; states={(0,0):(0.0,())}; width=25000 if len(tasks)<=40 else 6000
    for _ in range(len(tasks)):
        nxt={}
        for (mask,cmask),(cost,sol) in states.items():
            if mask==full:
                old=nxt.get((mask,cmask))
                if old is None or cost<old[0]: nxt[(mask,cmask)]=(cost,sol)
                continue
            first=((full^mask)&-(full^mask)).bit_length()-1
            for it in by.get(first,[]):
                tm,cm,c,k,cs,src,d=it
                if tm&mask or cm&cmask: continue
                key=(mask|tm,cmask|cm); val=(cost+c,sol+(it,))
                old=nxt.get(key)
                if old is None or val[0]<old[0]: nxt[key]=val
        states=dict(sorted(nxt.items(), key=lambda kv:(kv[1][0], -kv[0][0].bit_count()))[:width]) if len(nxt)>width else nxt
    return min((v for (m,_),v in states.items() if m==full), key=lambda x:x[0], default=(float('inf'),()))

cases=defaultdict(dict)
for p in glob.glob('runs/official_submit_*.json'):
    try:j=json.load(open(p))['result']
    except Exception:continue
    tag=os.path.basename(p).replace('official_submit_','').replace('.json','')
    for cr in j['case_results']:
        for d in cr['detail']:
            k=d['task_id_list']; cs=tuple(d['couriers']); cost=float(d['cost'])
            old=cases[cr['case_file']].get((k,cs))
            if old is None or cost<old[0]: cases[cr['case_file']][(k,cs)]=(cost,tag,d)
best_file=min(glob.glob('runs/official_submit_*.json'), key=lambda p: json.load(open(p))['result'].get('avg_score',9999))
latest=json.load(open(best_file))['result']; print('[baseline-wide]',best_file,latest['avg_score'])
for cr in sorted(latest['case_results'], key=lambda x:x['case_file']):
    case=cr['case_file']; cols=[(k,cs,cost,src,d) for (k,cs),(cost,src,d) in cases[case].items()]
    cost,sol=beam_case(cols,cr['total_tasks'])
    print('CASE',case,'cur',cr['total_score'],'wide',round(cost,4),'delta',round(cost-float(cr['total_score']),4),'cols',len(cols))
