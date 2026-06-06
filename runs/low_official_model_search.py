# Offline: reconstruct low candidate rows from official detail pool and test whether case-specific calibrated cost suggests non-current combos.
import json,glob,collections,itertools,os
coef=[0.42853,0.78455,11.32012,-1.08366,2.8843]
def pred(d):
    t=len(d['task_id_list'].split(',')); k=len(d['couriers']); pc=float(d['p_complete']); exp=float(d['expected_score'])
    x=[exp,(1-pc)*100*t,t,k,1.0]
    return sum(a*b for a,b in zip(coef,x))
case='low_willingness_seed501.txt'
cols=collections.defaultdict(dict)
latest=json.load(open('runs/official_submit_20260519_155636_b8253edc.json'))['result']
cur=next(x for x in latest['case_results'] if x['case_file']==case)
cur_sol={d['task_id_list']:tuple(d['couriers']) for d in cur['detail']}
for p in glob.glob('runs/official_submit_*.json'):
    try: j=json.load(open(p))['result']
    except Exception: continue
    cr=next((x for x in j['case_results'] if x['case_file']==case),None)
    if not cr: continue
    tag=os.path.basename(p)
    for d in cr['detail']:
        key=(d['task_id_list'],tuple(d['couriers']))
        old=cols[d['task_id_list']].get(tuple(d['couriers']))
        if old is None or pred(d)<old[0]: cols[d['task_id_list']][tuple(d['couriers'])]=(pred(d),float(d['cost']),tag,d)
print('task best by calibrated model vs current')
total_delta=0
for t in sorted(cols):
    curcs=cur_sol.get(t); curitem=cols[t].get(curcs)
    best=min(cols[t].items(), key=lambda kv: kv[1][0])
    if curitem and best[0]!=curcs:
        delta=best[1][0]-curitem[0]
        total_delta+=delta
        print(t,'cur',list(curcs),round(curitem[0],3), 'best',list(best[0]),round(best[1][0],3),'official_cost',best[1][1],'src',best[1][2],'delta',round(delta,3))
print('sum independent calibrated delta',round(total_delta,3))
