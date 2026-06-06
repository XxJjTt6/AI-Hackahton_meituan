from pathlib import Path
base=Path('solver.py').read_text()
helper=r'''
def _topk_by_task_candidate_pool(candidates,per_task):
	keep=set();by={}
	for r in candidates:
		for t in r[1]:by.setdefault(t,[]).append(r)
	for rows in by.values():
		for r in sorted(rows,key=lambda c:(_group_expected_cost([c],len(c[1])),-c[4],c[5]))[:per_task]:keep.add(r[5])
	out=[r for r in candidates if r[5] in keep]
	return out if out else candidates
'''
s=base.replace('def _scarce_seed401_cached_solution', helper+'\ndef _scarce_seed401_cached_solution',1)
# Use topK pool only for non-scarce disjoint/pair initial candidate generation, original C still used for final scoring/repairs.
old="\tif not O or F or AA:\n\t\tAD=(_G,_H)if F else(_I,_G,_H)\n\t\tfor P in AD:\n\t\t\tif time.monotonic()<A-.35:E.append(_solve_disjoint_then_multidispatch(C,B,mode=P,deadline=A))\n\t\tif time.monotonic()<A-.55:\n\t\t\tv=_solve_pair_potential_matching(C,B,A,lookahead=5 if F else 4,flexible_initial=F)"
new="\tif not O or F or AA:\n\t\tCC=_topk_by_task_candidate_pool(C,14) if (not G and not F and len(C)>1200) else C\n\t\tAD=(_G,_H)if F else(_I,_G,_H)\n\t\tfor P in AD:\n\t\t\tif time.monotonic()<A-.35:E.append(_solve_disjoint_then_multidispatch(CC,B,mode=P,deadline=A))\n\t\tif time.monotonic()<A-.55:\n\t\t\tv=_solve_pair_potential_matching(CC,B,A,lookahead=5 if F else 4,flexible_initial=F)"
if old not in s: raise SystemExit('marker not found')
s=s.replace(old,new,1)
Path('runs/non_scarce_topk_inside.py').write_text(s)
print('runs/non_scarce_topk_inside.py')
