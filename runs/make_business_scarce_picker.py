from pathlib import Path
base=Path('solver.py').read_text()
old="return C+60.*(len(I)-len(B))+14.*L+N+M/5."
new="return C+60.*(len(I)-len(B))+14.*L+N+M/5."
func=r'''
def _hard_scarce_business_cost(result,candidates,all_tasks):
	K={(a[0],a[2]):a for a in candidates};covered=set();used=set();cost=_C;risk=_C;groups=0
	for key,cs in result:
		rows=[]
		for c in cs:
			r=K.get((key,c))
			if r is _A or c in used:return float(_F)
			used.add(c);rows.append(r)
		if not rows:return float(_F)
		for t in rows[0][1]:
			if t in covered:return float(_F)
			covered.add(t)
		D=len(rows[0][1]);gc=_group_expected_cost(rows,D);cost+=gc;groups+=1
		# Business risk: high cost near/above penalty and low implied completion should be less attractive.
		p=1.0
		for r in rows:p*=(1-r[4])
		p=1-p
		risk+=max(_C,gc-100.*D)*.35 + max(_C,.72-p)*18.*D
	return cost+100.*(len(all_tasks)-len(covered))+risk+groups*.03
'''
anchor='def _pick_hard_scarce_best'
if anchor not in base: raise SystemExit('anchor missing')
s=base.replace(anchor,func+'\n'+anchor)
oldret="return min(E,key=lambda s:(_hard_scarce_shadow_cost(s,B,C),_solution_expected_cost(s,B,C)))"
newret="return min(E,key=lambda s:(_hard_scarce_business_cost(s,B,C),_hard_scarce_shadow_cost(s,B,C),_solution_expected_cost(s,B,C)))"
if oldret not in s: raise SystemExit('ret missing')
s=s.replace(oldret,newret)
Path('runs/business_scarce_picker.py').write_text(s)
print('runs/business_scarce_picker.py')
