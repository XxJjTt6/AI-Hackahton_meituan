#!/usr/bin/env python3
import json,glob,collections,hashlib
for f in sorted(glob.glob('runs/official_submit_*.json')):
    try: data=json.load(open(f))
    except Exception: continue
    res=data.get('result',{})
    avg=res.get('avg_score')
    sha=data.get('sha256','')[:8]
    rows=res.get('case_results',[])
    print('\n',f.split('/')[-1],sha,'avg',avg)
    for cr in rows:
        name=cr.get('case_file','')
        if 'low_willingness' not in name and 'scarce_couriers' not in name: continue
        detail=cr.get('detail',[]) or []
        lens=collections.Counter()
        cov=set(); sig=[]
        for d in detail:
            key=d.get('task_id_list') or d.get('task_key') or d.get('task_ids') or d.get('task') or ''
            cs=d.get('courier_id_list') or d.get('couriers') or d.get('courier_ids') or d.get('courier_id') or []
            if isinstance(cs,str): cs=[cs]
            ts=[x for x in str(key).split(',') if x]
            lens[len(cs)]+=1; cov.update(ts); sig.append(str(key)+':' + ','.join(map(str,cs)))
        scores=[d.get('expected_score') for d in detail if isinstance(d.get('expected_score'),(int,float))]
        top=sorted(scores, reverse=True)[:5]
        print(' ',name,'score',cr.get('total_score'),'n',len(detail),'cov',len(cov),'k',dict(sorted(lens.items())),'top',top,'sig',hashlib.sha256('\n'.join(sig).encode()).hexdigest()[:10])
