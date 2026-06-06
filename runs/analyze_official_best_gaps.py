import json
p='runs/official_submit_20260519_155636_b8253edc.json'
j=json.load(open(p))['result']
for case in ['low_willingness_seed501.txt','scarce_couriers_seed401.txt']:
    cr=next(x for x in j['case_results'] if x['case_file']==case)
    used=set(); covered=set()
    print('\nCASE',case,'score',cr['total_score'],'assigned',cr['assigned_count'],'unassigned',cr['unassigned_count'],'time',cr['elapsed_ms'])
    for d in sorted(cr['detail'], key=lambda d: -float(d['cost'])):
        tasks=d['task_id_list'].split(',')
        covered.update(tasks); used.update(d['couriers'])
        print(d['task_id_list'], d['couriers'], 'cost',d['cost'],'p',d['p_complete'],'exp',d['expected_score'])
    all_tasks={f'T{i:04d}' for i in range(cr['total_tasks'])}
    all_c={f'C{i:03d}' for i in range(cr['total_couriers'])}
    print('missing tasks', sorted(all_tasks-covered))
    print('unused couriers', sorted(all_c-used))
