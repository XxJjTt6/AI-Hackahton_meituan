import importlib.util,json,glob,os
# reuse functions by loading wide script text definitions up to cases loop
ns={}
code=open('runs/official_column_beam_all_wide.py').read().split('cases=defaultdict')[0]
exec(code,ns)
beam_case=ns['beam_case']
from collections import defaultdict
case='large_seed302.txt'; cases=defaultdict(dict)
for p in glob.glob('runs/official_submit_*.json'):
    try:j=json.load(open(p))['result']
    except Exception:continue
    tag=os.path.basename(p).replace('official_submit_','').replace('.json','')
    cr=next((x for x in j['case_results'] if x['case_file']==case),None)
    if not cr: continue
    for d in cr['detail']:
        k=d['task_id_list']; cs=tuple(d['couriers']); cost=float(d['cost'])
        old=cases[case].get((k,cs))
        if old is None or cost<old[0]: cases[case][(k,cs)]=(cost,tag,d)
latest=json.load(open('runs/official_submit_20260519_155636_b8253edc.json'))['result']
cr=next(x for x in latest['case_results'] if x['case_file']==case)
cols=[(k,cs,cost,src,d) for (k,cs),(cost,src,d) in cases[case].items()]
cost,sol=beam_case(cols,cr['total_tasks'])
print('cur',cr['total_score'],'wide',round(cost,4),'delta',round(cost-float(cr['total_score']),4),'cols',len(cols),'groups',len(sol))
for tm,cm,c,k,cs,src,d in sorted(sol,key=lambda x:x[3]):
    print(k,list(cs),round(c,4),src)
