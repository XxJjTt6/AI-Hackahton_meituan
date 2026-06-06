from pathlib import Path
ROOT=Path('/Users/比赛/FOR_AutoSolver_706.72')
s=(ROOT/'solver.py').read_text()
helper=r'''
def _task_shadow_values(candidates,all_tasks):
	# KDD-style value shaping: estimate scarcity/future value of each task from its best safe columns.
	B={T:[] for T in all_tasks}
	for C in candidates:
		if len(C[1])>3:continue
		cost=_group_expected_cost([C],len(C[1]))
		gain=1e2*len(C[1])-cost
		for T in C[1]:
			if T in B:B[T].append((gain,cost,C[4],len(C[1])))
	V={}
	for T,L in B.items():
		if not L:
			V[T]=30.;continue
		L.sort(reverse=True)
		best=L[0][0]
		# Small value for easy tasks, higher value for tasks with few good alternatives.
		good=sum(1 for g,c,w,k in L if g>1e-9)
		V[T]=max(0.,min(45.,8./max(1,good)+max(0.,20.-best)*.08))
	return V

def _value_shaped_row_key(c,task_values,courier_counts):
	D=len(c[1]);base=_group_expected_cost([c],D);shadow=sum(task_values.get(T,0.) for T in c[1])
	pressure=.08*courier_counts.get(c[2],1)
	# Lower is better. Reward moderate scarce-task value, but never enough to force expensive full coverage.
	return (base-.18*shadow+pressure, base/max(1,D), -c[4], c[5])
'''
s=s.replace('\ndef _solve_tiny_column_search(candidates,all_tasks,deadline):', helper+'\ndef _solve_tiny_column_search(candidates,all_tasks,deadline):',1)
old="""def _search_column_window(candidates,all_tasks,deadline,top_riders_per_task_key,max_k,option_limit):
	O=deadline;F=candidates;del all_tasks;F=_canonical_candidates(F);P=sorted({B for A in F for B in A[1]});Q={B:A for(A,B)in enumerate(P)};b={B:A for(A,B)in enumerate(sorted({A[2]for A in F}))};R={}
	for G in F:
		if all(A in Q for A in G[1]):R.setdefault(G[0],[]).append(G)
	H=[]
	for B in R.values():
		if time.monotonic()>O-.05:break
		B=sorted(B,key=lambda c:(_group_expected_cost([c],len(c[1])),-c[4],c[5]))[:top_riders_per_task_key]"""
new="""def _search_column_window(candidates,all_tasks,deadline,top_riders_per_task_key,max_k,option_limit):
	O=deadline;F=candidates;task_values=_task_shadow_values(F,all_tasks);courier_counts={}
	for C0 in F:courier_counts[C0[2]]=courier_counts.get(C0[2],0)+1
	F=_canonical_candidates(F);P=sorted({B for A in F for B in A[1]});Q={B:A for(A,B)in enumerate(P)};b={B:A for(A,B)in enumerate(sorted({A[2]for A in F}))};R={}
	for G in F:
		if all(A in Q for A in G[1]):R.setdefault(G[0],[]).append(G)
	H=[]
	for B in R.values():
		if time.monotonic()>O-.05:break
		B=sorted(B,key=lambda c:_value_shaped_row_key(c,task_values,courier_counts))[:top_riders_per_task_key]"""
if old not in s:
    raise SystemExit('search window pattern not found')
s=s.replace(old,new,1)
# Apply same conservative value-shaped ordering to scarce bundle MCF enum row list.
s=s.replace("C.sort(key=lambda item:(_popcount(item[2]),item[0]/max(item[1],1e-09),item[0],-item[1],-item[4][5]),reverse=_B);C=C[:120]", "C.sort(key=lambda item:(_popcount(item[2]),item[0]/max(item[1],1e-09),item[0]+.12*sum(_task_shadow_values(G,H).get(T,0.) for T in item[4][1]),-item[1],-item[4][5]),reverse=_B);C=C[:120]",1)
out=ROOT/'runs/kdd_value_shaped_column_picker.py'
out.write_text(s)
print(out)
