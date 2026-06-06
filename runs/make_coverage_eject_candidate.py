from pathlib import Path
ROOT=Path('/Users/比赛/FOR_AutoSolver_706.72')
s=(ROOT/'solver.py').read_text()
helper=r'''
def _force_cover_uncovered_by_eject(result,candidates,all_tasks,deadline,max_removed=2):
	K={(A[0],A[2]):A for A in candidates};S=_result_to_selected(result,K)
	if not S:return result
	covered={T for rows in S.values() if rows for T in rows[0][1]}
	missing=set(all_tasks)-covered
	if not missing:return result
	used_couriers={R[2] for rows in S.values() for R in rows}
	owner={}
	for key,rows in S.items():
		if rows:
			for T in rows[0][1]:owner[T]=key
	best=result;best_cost=_solution_expected_cost(result,candidates,all_tasks)
	# Prefer candidates that cover currently missing tasks; allow removing up to max_removed conflicting groups.
	pool=[C for C in candidates if set(C[1])&missing]
	pool.sort(key=lambda c:(-len(set(c[1])&missing), _group_expected_cost([c],len(c[1])), -c[4], c[5]))
	for cand in pool[:120]:
		if time.monotonic()>deadline-.04:break
		tasks=set(cand[1]); remove=set()
		for T in tasks:
			if T in owner: remove.add(owner[T])
		if cand[2] in used_couriers:
			for key,rows in S.items():
				if any(R[2]==cand[2] for R in rows):remove.add(key)
		if len(remove)>max_removed:continue
		NS={k:list(v) for k,v in S.items() if k not in remove}
		# If same task-key remains impossible, replace it; otherwise add new group.
		NS[cand[0]]=[cand]
		R=_format_selected(NS)
		R=_drop_unprofitable_groups(R,candidates,all_tasks)
		cov=_solution_covered_count(R,candidates)
		if cov<_solution_covered_count(result,candidates):continue
		cost=_solution_expected_cost(R,candidates,all_tasks)
		if cost<best_cost-1e-09:
			best=R;best_cost=cost
	return best
'''
# insert helper before _drop_unprofitable_groups
s=s.replace('\ndef _drop_unprofitable_groups(result,candidates,all_tasks):', helper+'\ndef _drop_unprofitable_groups(result,candidates,all_tasks):',1)
# call near end of scarce block after shift/eject, before F blocks. Conservative 0.16s window.
old="""\t\tif time.monotonic()<A-.22:\n\t\t\tA1=_shift_couriers_between_groups(D,C,B,min(A,time.monotonic()+.18),max_moves=18)\n\t\t\tif _solution_expected_cost(A1,C,B)<_solution_expected_cost(D,C,B)-1e-09:D=_drop_unprofitable_groups(A1,C,B)\n\tif F and time.monotonic()<A-.34:"""
new="""\t\tif time.monotonic()<A-.22:\n\t\t\tA1=_shift_couriers_between_groups(D,C,B,min(A,time.monotonic()+.18),max_moves=18)\n\t\t\tif _solution_expected_cost(A1,C,B)<_solution_expected_cost(D,C,B)-1e-09:D=_drop_unprofitable_groups(A1,C,B)\n\t\tif time.monotonic()<A-.18:\n\t\t\tA2=_force_cover_uncovered_by_eject(D,C,B,min(A,time.monotonic()+.14),max_removed=2)\n\t\t\tif _solution_expected_cost(A2,C,B)<_solution_expected_cost(D,C,B)-1e-09:D=_drop_unprofitable_groups(A2,C,B)\n\tif F and time.monotonic()<A-.34:"""
if old not in s:
    raise SystemExit('call insertion pattern not found')
s=s.replace(old,new,1)
out=ROOT/'runs/coverage_eject_uncovered.py'
out.write_text(s)
print(out)
