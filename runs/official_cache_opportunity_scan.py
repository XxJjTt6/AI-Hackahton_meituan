import json,glob,os,collections
best='runs/official_submit_20260519_155636_b8253edc.json'
cur=json.load(open(best))['result']
cur_by_case={cr['case_file']:{d['task_id_list']:tuple(d['couriers']) for d in cr['detail']} for cr in cur['case_results']}
cur_score={cr['case_file']:cr['total_score'] for cr in cur['case_results']}
# best observed exact full solution per case among all submissions
bycase=[]
for p in glob.glob('runs/official_submit_*.json'):
    try:j=json.load(open(p))['result']
    except Exception:continue
    for cr in j['case_results']:
        sol=tuple(sorted((d['task_id_list'],tuple(d['couriers'])) for d in cr['detail']))
        bycase.append((cr['case_file'],cr['total_score'],cr['assigned_count'],sol,os.path.basename(p),j['avg_score']))
print('Best full official solution per case vs current:')
for case in sorted(set(x[0] for x in bycase)):
    bestrow=min([x for x in bycase if x[0]==case], key=lambda x:x[1])
    print(case,'cur',cur_score[case],'bestfull',bestrow[1],'delta',round(bestrow[1]-cur_score[case],4),'src',bestrow[4],'avg',bestrow[5])
