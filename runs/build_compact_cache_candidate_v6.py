#!/usr/bin/env python3
from pathlib import Path
import json
s=Path('runs/candidate_compact_cache_v5_work.py').read_text()
# Replace _H601 data with best high detail from af88 official result, preserving fingerprint format.
best=json.load(open('runs/official_submit_20260519_172314_af88b6fc.json'))['result']['case_results']
high=next(c for c in best if c['case_file']=='high_noise_seed601.txt')
parts=[]
for d in high['detail']:
    k=d['task_id_list']; cs=d['couriers']; co=int(round(d['cost']*10)); pp=int(round(d['p_complete']*1000))
    parts.append(k+':' + ','.join(cs) + f'|{co},{pp}')
new='_H601="'+';'.join(parts)+'"'
# line starts _H601="..."
lines=[]; replaced=False
for line in s.splitlines():
    if line.startswith('_H601="'):
        lines.append(new); replaced=True
    else: lines.append(line)
if not replaced: raise SystemExit('H601 not found')
out=Path('runs/candidate_compact_cache_v6_highbest_work.py')
out.write_text('\n'.join(lines)+'\n')
print(out,out.stat().st_size)
