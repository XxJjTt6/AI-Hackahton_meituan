from pathlib import Path
base=Path('solver.py').read_text()
func=r'''
def _scarce_pair_replace_for_uncovered(result,candidates,all_tasks,deadline):
	D=deadline;C=candidates;B=all_tasks;R={(a[0],a[2]):a for a in C};S=_result_to_selected(result,R)
	if not S:return result
	covered={t for rows in S.values() if rows for t in rows[0][1]};missing=set(B)-covered
	if not missing:return result
	used={r[2] for rows in S.values() for r in rows};best=result;best_cost=_solution_expected_cost(result,C,B);base_cov=_solution_covered_count(result,C)
	by_cour={}
	for r in C:by_cour.setdefault(r[2],[]).append(r)
	for old_key,old_rows in list(S.items()):
		if time.monotonic()>D-.04:break
		if not old_rows:continue
		old_tasks=set(old_rows[0][1]);old_cour={r[2] for r in old_rows}
		# Replace an entire selected group by one or two rows from same/unused couriers that include a missing task.
		pool=[]
		for r in C:
			if time.monotonic()>D-.04:break
			if r[2] in used and r[2] not in old_cour:continue
			if not (set(r[1])&missing):continue
			if set(r[1])&covered and not (set(r[1])&old_tasks):continue
			pool.append(r)
		pool=sorted(pool,key=lambda r:(_group_expected_cost([r],len(r[1]))-100*len(set(r[1])&missing),_group_expected_cost([r],len(r[1]))))[:24]
		trials=[]
		for r in pool:trials.append([r])
		for i,r in enumerate(pool[:14]):
			for q in pool[i+1:14]:
				if r[0]!=q[0] or r[2]==q[2]:continue
				trials.append([r,q])
		for rows in trials:
			if time.monotonic()>D-.04:break
			cour=[r[2] for r in rows]
			if len(cour)!=len(set(cour)):continue
			NS={k:list(v) for k,v in S.items() if k!=old_key};NS[rows[0][0]]=rows
			R2=_format_selected(NS);cov=_solution_covered_count(R2,C)
			if cov<base_cov:continue
			cost=_solution_expected_cost(R2,C,B)
			if cost<best_cost-1e-09:best=R2;best_cost=cost
	return best
'''
anchor='def _scarce_eject_extra_to_uncovered'
if anchor not in base: raise SystemExit('anchor missing')
s=base.replace(anchor,func+'\n'+anchor)
pat="\t\tif time.monotonic()<A-.24:\n\t\t\tA0=_scarce_eject_extra_to_uncovered(D,C,B,min(A,time.monotonic()+.18))\n\t\t\tif _solution_expected_cost(A0,C,B)<_solution_expected_cost(D,C,B)-1e-09:D=A0;D=_drop_unprofitable_groups(D,C,B)"
new="\t\tif time.monotonic()<A-.28:\n\t\t\tA9=_scarce_pair_replace_for_uncovered(D,C,B,min(A,time.monotonic()+.22))\n\t\t\tif _solution_expected_cost(A9,C,B)<_solution_expected_cost(D,C,B)-1e-09:D=_drop_unprofitable_groups(A9,C,B)\n"+pat
if pat not in s: raise SystemExit('route pattern missing')
s=s.replace(pat,new)
Path('runs/scarce_pair_replace_uncovered.py').write_text(s)
print('runs/scarce_pair_replace_uncovered.py')
