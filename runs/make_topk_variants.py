from pathlib import Path
base=Path('solver.py').read_text()
variants=[]
helper='''\ndef _topk_candidate_filter(candidates, per_task=14, per_courier=18):\n\tby_task={}\n\tby_courier={}\n\tfor A in candidates:\n\t\tfor T in A[1]: by_task.setdefault(T,[]).append(A)\n\t\tby_courier.setdefault(A[2],[]).append(A)\n\tkeep=set()\n\tfor rows in by_task.values():\n\t\tfor A in sorted(rows,key=lambda c:(_group_expected_cost([c],len(c[1])),-c[4],c[5]))[:per_task]: keep.add(A[5])\n\tfor rows in by_courier.values():\n\t\tfor A in sorted(rows,key=lambda c:(_group_expected_cost([c],len(c[1])),-len(c[1]),-c[4],c[5]))[:per_courier]: keep.add(A[5])\n\tR=[A for A in candidates if A[5] in keep]\n\treturn R if R else candidates\n'''
insert_after="def _bias_scores_for_willingness(candidates,alpha):return[(B,C,D,E/(A+.05)**alpha,A,F)for(B,C,D,E,A,F)in candidates]\n"
for name, pt, pc, gate in [
    ('topk_normal_14_18',14,18,"if 9<=L<=35 and not G and not F and len(C)>900 and time.monotonic()<A-1.15:\n\t\tTC=_topk_candidate_filter(C,14,18)\n\t\tif len(TC)<len(C):\n\t\t\tfor P in (_I,_G,_H):\n\t\t\t\tif time.monotonic()<A-.5:E.append(_solve_disjoint_then_multidispatch(TC,B,mode=P,deadline=A))\n\t\t\tif time.monotonic()<A-.6:\n\t\t\t\tTV=_solve_pair_potential_matching(TC,B,min(A,time.monotonic()+.8),lookahead=5,flexible_initial=_B)\n\t\t\t\tif TV:E.append(TV)"),
    ('topk_normal_10_12',10,12,"if 9<=L<=35 and not G and not F and len(C)>900 and time.monotonic()<A-1.15:\n\t\tTC=_topk_candidate_filter(C,10,12)\n\t\tif len(TC)<len(C):\n\t\t\tfor P in (_I,_G,_H):\n\t\t\t\tif time.monotonic()<A-.5:E.append(_solve_disjoint_then_multidispatch(TC,B,mode=P,deadline=A))\n\t\t\tif time.monotonic()<A-.6:\n\t\t\t\tTV=_solve_pair_potential_matching(TC,B,min(A,time.monotonic()+.8),lookahead=5,flexible_initial=_B)\n\t\t\t\tif TV:E.append(TV)"),
    ('topk_all_nonscarce_12_16',12,16,"if not G and not F and len(C)>700 and time.monotonic()<A-1.1:\n\t\tTC=_topk_candidate_filter(C,12,16)\n\t\tif len(TC)<len(C):\n\t\t\tfor P in (_I,_G,_H):\n\t\t\t\tif time.monotonic()<A-.5:E.append(_solve_disjoint_then_multidispatch(TC,B,mode=P,deadline=A))\n\t\t\tif time.monotonic()<A-.6:\n\t\t\t\tTV=_solve_pair_potential_matching(TC,B,min(A,time.monotonic()+.8),lookahead=5,flexible_initial=_B)\n\t\t\t\tif TV:E.append(TV)")]:
    s=base
    s=s.replace(insert_after, insert_after+helper.replace('per_task=14, per_courier=18',f'per_task={pt}, per_courier={pc}'),1)
    marker="\tif not O or F or AA:\n"
    gate='\n'.join('\t'+line if line else line for line in gate.split('\n'))
    s=s.replace(marker, gate+"\n"+marker,1)
    p=Path('runs')/(name+'.py')
    p.write_text(s)
    variants.append(str(p))
print('\n'.join(variants))
