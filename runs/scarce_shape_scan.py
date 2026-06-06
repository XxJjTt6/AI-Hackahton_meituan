import json,glob,collections,os
case='scarce_couriers_seed401.txt'
rows=[]
for p in glob.glob('runs/official_submit_*.json'):
    try:j=json.load(open(p))['result']
    except Exception:continue
    cr=next((x for x in j['case_results'] if x['case_file']==case),None)
    if not cr: continue
    shape=tuple(sorted(collections.Counter((len(d['task_id_list'].split(',')),len(d['couriers'])) for d in cr['detail']).items()))
    covered=set()
    for d in cr['detail']: covered.update(d['task_id_list'].split(','))
    rows.append((cr['total_score'],cr['assigned_count'],tuple(sorted(set(f'T{i:04d}' for i in range(40))-covered)),shape,os.path.basename(p),j['avg_score']))
for r in sorted(rows)[:30]: print(r[0],r[1],r[2],r[4],r[5],r[3])
