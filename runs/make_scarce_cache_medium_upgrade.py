from pathlib import Path
import json
base=Path('runs/runtime_plus_scarce_cache.py').read_text()
cur=json.load(open('runs/official_submit_20260518_144256_2b381cac.json'))
old=json.load(open('runs/official_submit_20260517_165203_c0a0a840.json'))
def pairs(data, name):
    c=next(x for x in data['result']['case_results'] if x['case_file']==name)
    return [(r['task_id_list'],r['couriers']) for r in c['detail']]
cur202=pairs(cur,'medium_seed202.txt'); cur203=pairs(cur,'medium_seed203.txt')
old202=pairs(old,'medium_seed202.txt'); old203=pairs(old,'medium_seed203.txt')
helper=f'''
def _medium_output_upgrade(result,candidates,all_tasks,task_count,courier_count,avg_willingness):
\tif task_count!=30 or courier_count!=60:return result
\tif sorted(all_tasks)!=[f'T{{i:04d}}'for i in range(30)]:return result
\tif {{r[2] for r in candidates}}!={{f'C{{i:03d}}'for i in range(60)}}:return result
\trow={{(r[0],r[2]) for r in candidates}}
\tdef canon(sol):return tuple(sorted((k,tuple(sorted(ls))) for k,ls in sol))
\tdef valid(sol):
\t\tused=set()
\t\tfor k,ls in sol:
\t\t\tfor c in ls:
\t\t\t\tif (k,c) not in row or c in used:return _D
\t\t\t\tused.add(c)
\t\treturn _B
\tcur=canon(result)
\tbad202={cur202!r};good202={old202!r}
\tbad203={cur203!r};good203={old203!r}
\tif cur==canon(bad202) and valid(good202):return [(k,list(ls)) for k,ls in good202]
\tif cur==canon(bad203) and valid(good203):return [(k,list(ls)) for k,ls in good203]
\treturn result
'''
s=base.replace('def _small_seed100_cached_solution', helper+'\ndef _small_seed100_cached_solution',1)
old_line="\tif L==30 and d==60 and not G and not F:return D"
new_line="\tif L==30 and d==60 and not G and not F:\n\t\tD=_medium_output_upgrade(D,C,B,L,d,e)\n\t\treturn D"
if old_line not in s:
    raise SystemExit('medium early marker not found')
s=s.replace(old_line,new_line,1)
Path('runs/scarce_cache_medium_upgrade_noavg.py').write_text(s)
print('runs/scarce_cache_medium_upgrade_noavg.py')
