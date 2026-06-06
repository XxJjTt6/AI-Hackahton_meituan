#!/usr/bin/env python3
import json, math, statistics
p='runs/official_submit_20260519_171310_41db4b34.json'
r=json.load(open(p))['result']['case_results']
for case in ['low_willingness_seed501.txt','scarce_couriers_seed401.txt']:
    cr=next(c for c in r if c['case_file']==case)
    print('\nCASE',case,'score',cr['total_score'])
    vals=[]
    for d in cr['detail']:
        k=len(d['couriers']); nt=len(d['task_id_list'].split(',')); pcomp=d['p_complete']; cost=d['cost']; exp=d['expected_score']
        # equal-w approximation per courier willingness
        w=1-(1-pcomp)**(1/max(1,k))
        # judge cost relation approx: expected cost = p*avg_score + (1-p)*100*nt? solve implied success cost
        succ=(cost-(1-pcomp)*100*nt)/pcomp if pcomp>0 else None
        vals.append((cost,nt,k,pcomp,w,exp,succ,d['task_id_list'],d['couriers']))
    for name,idx in [('cost',0),('p',3),('w_eq',4),('succ_implied',6)]:
        arr=[x[idx] for x in vals if x[idx] is not None]
        print(name,'mean',round(statistics.mean(arr),4),'min',round(min(arr),4),'max',round(max(arr),4))
    print('worst marginal groups:')
    for x in sorted(vals, reverse=True)[:8]: print(x[7],x[8],'cost',x[0],'p',x[3],'w_eq',round(x[4],3),'succ_implied',round(x[6],2))
