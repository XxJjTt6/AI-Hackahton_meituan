# Test exact formulas against official detail rows.
import json,glob,math,collections
rows=[]
for p in glob.glob('runs/official_submit_*.json'):
    try:j=json.load(open(p))['result']
    except Exception:continue
    for cr in j['case_results']:
        for d in cr['detail']:
            rows.append((cr['case_file'],len(d['task_id_list'].split(',')),len(d['couriers']),float(d['p_complete']),float(d['expected_score']),float(d['cost'])))
forms={
'expected_plus_fail100':lambda t,k,p,e:e+(1-p)*100*t,
'exp_over_p':lambda t,k,p,e:e/max(p,1e-9),
'exp_plus_fail80':lambda t,k,p,e:e+(1-p)*80*t,
'0.85_exp_0.85_fail100':lambda t,k,p,e:.85*e+.85*(1-p)*100*t,
}
for name,fn in forms.items():
    by=collections.defaultdict(list)
    for case,t,k,p,e,c in rows:
        by[case].append(abs(fn(t,k,p,e)-c))
    print('\n',name)
    for case in ['low_willingness_seed501.txt','scarce_couriers_seed401.txt','large_seed302.txt','medium_seed202.txt']:
        arr=by[case]; print(case,round(sum(arr)/len(arr),3))
