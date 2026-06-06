import json,glob,os,collections
case='scarce_couriers_seed401.txt'
cols=collections.defaultdict(dict)
for p in glob.glob('runs/official_submit_*.json'):
    try:j=json.load(open(p))['result']
    except Exception:continue
    cr=next((x for x in j['case_results'] if x['case_file']==case),None)
    if not cr: continue
    tag=os.path.basename(p)
    for d in cr['detail']:
        k=d['task_id_list']; cs=tuple(d['couriers']); cost=float(d['cost'])
        old=cols[k].get(cs)
        if old is None or cost<old[0]: cols[k][cs]=(cost,tag)
# beam over all observed scarce columns + dummy penalties
all_tasks=[f'T{i:04d}' for i in range(40)]; ti={t:i for i,t in enumerate(all_tasks)}; ci={f'C{i:03d}':i for i in range(40)}
items=[]
for k,mp in cols.items():
    tm=0
    for t in k.split(','): tm|=1<<ti[t]
    for cs,(cost,tag) in mp.items():
        cm=0
        for c in cs: cm|=1<<ci[c]
        items.append((tm,cm,cost,k,cs,tag))
for t in all_tasks: items.append((1<<ti[t],0,100.0,t,(), 'dummy'))
by=collections.defaultdict(list)
for it in items: by[(it[0]&-it[0]).bit_length()-1].append(it)
for v in by.values(): v.sort(key=lambda x:(x[2],-x[0].bit_count())); del v[60:]
full=(1<<40)-1; states={(0,0):(0.0,())}; width=20000
for step in range(40):
    nxt={}
    for (m,cm),(cost,sol) in states.items():
        if m==full:
            old=nxt.get((m,cm));
            if old is None or cost<old[0]: nxt[(m,cm)]=(cost,sol)
            continue
        first=((full^m)&-(full^m)).bit_length()-1
        for it in by[first]:
            tm,cmm,c,k,cs,tag=it
            if tm&m or cmm&cm: continue
            key=(m|tm,cm|cmm); val=(cost+c,sol+(it,))
            old=nxt.get(key)
            if old is None or val[0]<old[0]: nxt[key]=val
    states=dict(sorted(nxt.items(), key=lambda kv:(kv[1][0], -kv[0][0].bit_count()))[:width]) if len(nxt)>width else nxt
best=min((v for (m,_),v in states.items() if m==full), key=lambda x:x[0])
cur=json.load(open('runs/official_submit_20260519_155636_b8253edc.json'))['result']
cr=next(x for x in cur['case_results'] if x['case_file']==case)
print('cur',cr['total_score'],'beam',round(best[0],4),'delta',round(best[0]-float(cr['total_score']),4),'items',len(items),'states',len(states))
for tm,cm,c,k,cs,tag in sorted(best[1], key=lambda x:x[3]):
    if cs: print(k,list(cs),round(c,4),tag)
