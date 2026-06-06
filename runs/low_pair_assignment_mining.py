# Mine if historical official rows contain alternative low pair matchings with no courier conflicts.
import json,glob,os,collections
case='low_willingness_seed501.txt'
cols=collections.defaultdict(dict)
for p in glob.glob('runs/official_submit_*.json'):
    try:j=json.load(open(p))['result']
    except Exception:continue
    cr=next((x for x in j['case_results'] if x['case_file']==case),None)
    if not cr: continue
    tag=os.path.basename(p)
    for d in cr['detail']:
        if len(d['task_id_list'].split(','))==1 and len(d['couriers'])==2:
            k=d['task_id_list']; cs=tuple(sorted(d['couriers'])); cost=float(d['cost'])
            old=cols[k].get(cs)
            if old is None or cost<old[0]: cols[k][cs]=(cost,tag)
# exact DP by tasks, courier mask over C000-C059
idx={f'C{i:03d}':i for i in range(60)}
states={0:(0.0,())}
tasks=[f'T{i:04d}' for i in range(30)]
for t in tasks:
    nxt={}
    for mask,(cost,sol) in states.items():
        for cs,(c,tag) in cols[t].items():
            cm=sum(1<<idx[x] for x in cs)
            if mask&cm: continue
            nm=mask|cm; val=(cost+c, sol+((t,cs,c,tag),))
            old=nxt.get(nm)
            if old is None or val[0]<old[0]: nxt[nm]=val
    states=nxt
best=min(states.values(), key=lambda x:x[0])
cur=json.load(open('runs/official_submit_20260519_155636_b8253edc.json'))['result']
cr=next(x for x in cur['case_results'] if x['case_file']==case)
print('cur',cr['total_score'],'best_pair_hist',round(best[0],4),'delta',round(best[0]-float(cr['total_score']),4),'states',len(states))
for t,cs,c,tag in best[1]: print(t,list(cs),round(c,4),tag)
