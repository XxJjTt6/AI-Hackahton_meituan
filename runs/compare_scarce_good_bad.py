import json
files=['runs/official_submit_20260519_171310_41db4b34.json','runs/official_submit_20260519_172314_af88b6fc.json']
sol=[]
for p in files:
    cr=next(x for x in json.load(open(p))['result']['case_results'] if x['case_file']=='scarce_couriers_seed401.txt')
    d={x['task_id_list']:tuple(x['couriers']) for x in cr['detail']}
    sol.append(d)
keys=sorted(set(sol[0])|set(sol[1]))
for k in keys:
    if sol[0].get(k)!=sol[1].get(k): print(k,'good',sol[0].get(k),'bad',sol[1].get(k))
