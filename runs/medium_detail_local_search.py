import json, itertools
from pathlib import Path
# Analyze official detail group expected_score/cost only; without full row probabilities this is limited.
d=json.load(open('runs/official_submit_20260518_170527_8ee7a12d.json'))
for name in ['medium_seed202.txt','medium_seed203.txt','medium_seed201.txt']:
    c=next(x for x in d['result']['case_results'] if x['case_file']==name)
    rows=c['detail']
    print('\n',name,'score',c['total_score'])
    worst=sorted(rows,key=lambda r:r['expected_score']/max(1,len(r['task_id_list'].split(','))),reverse=True)[:8]
    for r in worst:
        print(r['task_id_list'], r['couriers'], 'exp', r['expected_score'], 'p', r['p_complete'], 'cost', r['cost'])
