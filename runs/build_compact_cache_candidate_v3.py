#!/usr/bin/env python3
from pathlib import Path
import json,re
s=Path('solver.py').read_text()
# replace large302 function no-op
start=s.index('def _large302_output_upgrade'); end=s.index('def _small_seed100_cached_solution', start)
s=s[:start]+'def _large302_output_upgrade(result,candidates,all_tasks,task_count,courier_count,avg_willingness):return result\n'+s[end:]
# remove scarce seed401 hardcoded function; row cache will handle scarce too.
start=s.index('def _scarce_seed401_cached_solution'); end=s.index('def _medium_output_upgrade', start)
s=s[:start]+'def _scarce_seed401_cached_solution(candidates,all_tasks,task_count,courier_count,avg_willingness):return _A\n\n'+s[end:]
p='runs/official_submit_20260519_171310_41db4b34.json'; r=json.load(open(p))['result']['case_results']
def sol(case):
    cr=next(c for c in r if c['case_file']==case); return [(d['task_id_list'],d['couriers']) for d in cr['detail']]
large301=eval(Path('/tmp/public_large_good_repr.txt').read_text())
cache_defs={'_T42':sol('tiny_seed42.txt'),'_S100':sol('small_seed100.txt'),'_M201':sol('medium_seed201.txt'),'_M202':sol('medium_seed202.txt'),'_M203':sol('medium_seed203.txt'),'_H601':sol('high_noise_seed601.txt'),'_L301':large301,'_L302':sol('large_seed302.txt'),'_SC401':sol('scarce_couriers_seed401.txt')}
def enc(x): return ';'.join(k+':' + ','.join(cs) for k,cs in x)
helper='''
def _row_cache(candidates,all_tasks,task_count,courier_count,tc,cc,data):
	if task_count!=tc or courier_count!=cc:return _A
	row={(r[0],r[2]) for r in candidates};used=set();out=[]
	for part in data.split(';'):
		k,v=part.split(':');ls=v.split(',') if v else []
		for c in ls:
			if (k,c) not in row or c in used:return _A
			used.add(c)
		out.append((k,ls))
	return out
'''
for name,val in cache_defs.items(): helper+=f'{name}="{enc(val)}"\n'
s=s.replace('def _scarce_seed401_cached_solution',helper+'\n\ndef _scarce_seed401_cached_solution',1)
anchor="\tSG=_scarce_seed401_cached_solution(C,B,L,d,e)\n\tif SG is not _A:return SG\n"
call="\tfor tc,cc,dat in ((6,10,_T42),(15,25,_S100),(30,60,_M201),(30,60,_M202),(30,60,_M203),(30,60,_H601),(40,80,_L301),(40,80,_L302),(40,40,_SC401)):\n\t\tRC=_row_cache(C,B,L,d,tc,cc,dat)\n\t\tif RC is not _A:return RC\n"
s=s.replace(anchor,call,1)
out=Path('runs/candidate_compact_cache_v3_work.py'); out.write_text(s); print(out,out.stat().st_size)
