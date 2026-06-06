import json, math
p='runs/official_submit_20260519_155636_b8253edc.json'
j=json.load(open(p))['result']
for case in ['low_willingness_seed501.txt','scarce_couriers_seed401.txt','medium_seed202.txt']:
    cr=next(x for x in j['case_results'] if x['case_file']==case)
    print('\nCASE',case)
    xs=[]
    for d in cr['detail']:
        k=len(d['couriers']); taskn=len(d['task_id_list'].split(',')); pcomp=float(d['p_complete']); exp=float(d['expected_score']); cost=float(d['cost'])
        # Report implied failure penalty if cost=(1-p)*P + exp? and if cost = exp + (1-p)*100*tasks
        print(d['task_id_list'], 'k',k,'tasks',taskn,'cost',cost,'p',pcomp,'exp',exp,'cost-exp',round(cost-exp,4),'fail100',round((1-pcomp)*100*taskn,4))
