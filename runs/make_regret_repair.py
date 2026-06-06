from pathlib import Path
base=Path('solver.py').read_text()
helper=r'''
def _regret_insert_window_solution(result,candidates,all_tasks,deadline,max_remove=4):
	row={(r[0],r[2]):r for r in candidates};sel=_result_to_selected(result,row)
	if not sel:return result
	items=[]
	for k,rs in sel.items():
		if rs: items.append((_group_expected_cost(rs,len(rs[0][1]))/max(1,len(rs[0][1])),k,rs[0][1]))
	items=sorted(items,reverse=_B)[:max_remove]
	remove={k for _,k,_ in items};partial={k:v for k,v in sel.items() if k not in remove}
	used={r[2] for rs in partial.values() for r in rs};covered={t for rs in partial.values() for t in rs[0][1]}
	missing=sorted(set(all_tasks)-covered)
	bytask={t:[] for t in missing}
	for r in candidates:
		if r[2] in used:continue
		if len(r[1])!=1:continue
		t=r[1][0]
		if t in bytask:bytask[t].append(r)
	for t in bytask:bytask[t]=sorted(bytask[t],key=lambda r:_group_expected_cost([r],1))[:12]
	cur={t:[] for t in missing};cost={t:1e2 for t in missing}
	while missing and time.monotonic()<deadline-.05:
		best=_A;best_key=_A
		for t in list(missing):
			opts=[]
			for r in bytask.get(t,[]):
				if r[2] in used:continue
				new=_group_expected_cost(cur[t],1,extra=r);gain=cost[t]-new
				if gain>1e-12:opts.append((new,gain,r))
			if not opts:continue
			opts.sort(key=lambda x:x[0])
			reg=(opts[1][0]-opts[0][0]) if len(opts)>1 else 50.
			key=(reg,opts[0][1],-opts[0][0])
			if best_key is _A or key>best_key:best_key=key;best=(t,opts[0])
		if best is _A:break
		t,(new,gain,r)=best;cur[t].append(r);cost[t]=new;used.add(r[2])
		# keep adding to same task only while beneficial is handled by loop; remove when at least one rider and marginal small
		if cur[t] and (len(cur[t])>=3 or all(rr[2] in used for rr in bytask.get(t,[]))):
			missing.remove(t)
		elif cur[t] and cost[t]<55:
			missing.remove(t)
	trial=_format_selected(partial)+[(t,[r[2] for r in rs]) for t,rs in cur.items() if rs]
	return trial if _solution_expected_cost(trial,candidates,all_tasks)<_solution_expected_cost(result,candidates,all_tasks)-1e-09 else result
'''
s=base.replace('def _scarce_seed401_cached_solution', helper+'\ndef _scarce_seed401_cached_solution',1)
marker="\tif 9<=L<=35 and not G and not F and time.monotonic()<A-.95:D=_normal_worst_related_repair_solution(D,C,B,min(A,time.monotonic()+.75))\n"
insert="\tif 9<=L<=35 and not G and not F and time.monotonic()<A-.55:D=_regret_insert_window_solution(D,C,B,min(A,time.monotonic()+.45),max_remove=4)\n"
s=s.replace(marker,marker+insert,1)
Path('runs/nonscarce_regret_insert.py').write_text(s)
print('runs/nonscarce_regret_insert.py')
