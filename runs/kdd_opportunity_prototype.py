# Offline prototype: estimate courier opportunity cost from best alternative rows and rescore groups.
import json,glob,collections,math
# Use official details to estimate per-courier shadow: high cost contribution when courier used in good rows.
latest=json.load(open('runs/official_submit_20260519_171310_41db4b34.json'))['result']
for case in ['low_willingness_seed501.txt','scarce_couriers_seed401.txt']:
    cr=next(x for x in latest['case_results'] if x['case_file']==case)
    shadows=collections.defaultdict(list)
    for d in cr['detail']:
        per=float(d['cost'])/max(1,len(d['couriers']))
        for c in d['couriers']: shadows[c].append(per)
    vals={c:sum(v)/len(v) for c,v in shadows.items()}
    print('\nCASE',case,'shadow range',round(min(vals.values()),2),round(max(vals.values()),2))
    print('highest opportunity couriers', sorted(vals.items(), key=lambda x:-x[1])[:8])
    print('lowest opportunity couriers', sorted(vals.items(), key=lambda x:x[1])[:8])
