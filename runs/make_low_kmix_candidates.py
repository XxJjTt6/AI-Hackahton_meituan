from pathlib import Path
base=Path('solver.py').read_text()
out=Path('runs/low_kmix_candidates'); out.mkdir(exist_ok=True)
insert_after="def _simple_result_score(result,candidates,all_tasks):return _solution_expected_cost(result,candidates,all_tasks)\n"
func=r'''
def _solve_low_kmix_single_solution(candidates,all_tasks,deadline):
	D=deadline;B=sorted(all_tasks);A=candidates;by={t:[]for t in B}
	for c in A:
		if len(c[1])==1 and c[1][0] in by:by[c[1][0]].append(c)
	if any(not by[t] for t in B):return[]
	opts=[]
	for t in B:
		rows=sorted(by[t],key=lambda c:(_single_expected_cost(c),c[3],-c[4],c[5]))[:18]
		choices=[]
		for k in (1,2,3):
			if len(rows)<k:continue
			best=[]
			for comb in itertools.combinations(rows,k):
				if len({x[2] for x in comb})<k:continue
				cost=_group_expected_cost(comb,1);best.append((cost,comb,frozenset(x[2] for x in comb)))
			best.sort(key=lambda z:(z[0],tuple(x[5] for x in z[1])))
			choices.extend(best[:10 if k==2 else 6])
		if not choices:return[]
		opts.append((t,sorted(choices,key=lambda z:z[0])[:18]))
	opts.sort(key=lambda x:(len(x[1]),x[0]));mins=[min(c[0] for c in ch) for t,ch in opts];suf=[0]*(len(opts)+1)
	for i in range(len(opts)-1,-1,-1):suf[i]=suf[i+1]+mins[i]
	best=[];best_cost=float(_F);cur=[];used=set()
	def dfs(i,cost):
		nonlocal best,best_cost
		if time.monotonic()>D-.035:return
		if cost+suf[i]>=best_cost-1e-09:return
		if i==len(opts):best_cost=cost;best=list(cur);return
		t,choices=opts[i]
		for cc,rows,cs in choices:
			if used&cs:continue
			if cost+cc+suf[i+1]>=best_cost-1e-09:continue
			used.update(cs);cur.append((rows[0][0],[r[2] for r in rows]));dfs(i+1,cost+cc);cur.pop();used.difference_update(cs)
	dfs(0,_C)
	return sorted(best)
'''
if insert_after not in base: raise SystemExit('insert point missing')
s=base.replace(insert_after,insert_after+func+'\n')
# add candidate before low worst repair
pat="\tif J and time.monotonic()<A-.78:D=_low_worst_window_repair_solution(D,C,B,min(A,time.monotonic()+.62))"
new="\tif J and time.monotonic()<A-1.05:\n\t\tKM=_solve_low_kmix_single_solution(C,B,min(A,time.monotonic()+.85))\n\t\tif KM and _pick_low_robust_best([D,KM],C,B) is KM:D=KM\n"+pat
if pat not in s: raise SystemExit('route pattern missing')
(Path('runs/low_kmix_candidates/low_kmix_robust.py')).write_text(s.replace(pat,new))
# force if expected cost better only
s2=s.replace(pat,"\tif J and time.monotonic()<A-1.05:\n\t\tKM=_solve_low_kmix_single_solution(C,B,min(A,time.monotonic()+.85))\n\t\tif KM and _solution_expected_cost(KM,C,B)<_solution_expected_cost(D,C,B)-1e-09:D=KM\n"+pat)
(Path('runs/low_kmix_candidates/low_kmix_cost.py')).write_text(s2)
print('done')
