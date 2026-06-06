import json,itertools
cr=next(x for x in json.load(open('runs/official_submit_20260519_171310_41db4b34.json'))['result']['case_results'] if x['case_file']=='scarce_couriers_seed401.txt')
rows=[(d['task_id_list'],float(d['cost'])) for d in cr['detail']]
base=cr['total_score']
print('base',base)
for k,c in sorted(rows,key=lambda x:-x[1])[:8]:
    new=base-c+100*len(k.split(','))
    print('drop',k,'cost',c,'newscore',round(new,4),'delta',round(new-base,4))
