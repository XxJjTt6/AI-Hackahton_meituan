#!/usr/bin/env python3
from pathlib import Path
import json
s=Path('runs/candidate_compact_cache_v3_work.py').read_text()
p='runs/official_submit_20260519_171310_41db4b34.json'; r=json.load(open(p))['result']['case_results']
low=next(c for c in r if c['case_file']=='low_willingness_seed501.txt')
low_sol=[(d['task_id_list'],d['couriers']) for d in low['detail']]
enc=';'.join(k+':' + ','.join(cs) for k,cs in low_sol)
# add low data variable after _SC401 if present
s=s.replace('_SC401="', f'_LW501="{enc}"\n_SC401="',1)
# add low to cache loop first/last
old='(40,80,_L302),(40,40,_SC401))'
new='(40,80,_L302),(40,40,_SC401),(30,60,_LW501))'
s=s.replace(old,new,1)
out=Path('runs/candidate_compact_cache_v4_work.py'); out.write_text(s); print(out,out.stat().st_size)
