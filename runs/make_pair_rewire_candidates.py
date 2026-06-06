from pathlib import Path
ROOT=Path('/Users/比赛/FOR_AutoSolver_706.72')
s=(ROOT/'solver.py').read_text()
vars={}
vars['pair_pool8']=s.replace('D=_best_group_from_pool(S,2,min(len(I)+1,6))','D=_best_group_from_pool(S,2,min(len(I)+2,8))',1).replace('E=_best_group_from_pool(T,2,min(len(L)+1,6))','E=_best_group_from_pool(T,2,min(len(L)+2,8))',1)
vars['pair_more_time']=s.replace('if time.monotonic()<A-.18:D=_local_improve_mixed_solution(D,C,B,A,include_pair_rewire=_B);D=_drop_unprofitable_groups(D,C,B)','if time.monotonic()<A-.32:D=_local_improve_mixed_solution(D,C,B,min(A,time.monotonic()+.28),include_pair_rewire=_B);D=_drop_unprofitable_groups(D,C,B)\n\t\tif time.monotonic()<A-.18:D=_local_improve_mixed_solution(D,C,B,A,include_pair_rewire=_B);D=_drop_unprofitable_groups(D,C,B)',1)
vars['pair_before_reassign']=s.replace('if G and time.monotonic()<A-.3:\n\t\tD=_reassign_mixed_solution(D,C,B,A);D=_drop_unprofitable_groups(D,C,B)','if G and time.monotonic()<A-.42:\n\t\tD=_local_improve_mixed_solution(D,C,B,min(A,time.monotonic()+.2),include_pair_rewire=_B);D=_drop_unprofitable_groups(D,C,B)\n\tif G and time.monotonic()<A-.3:\n\t\tD=_reassign_mixed_solution(D,C,B,A);D=_drop_unprofitable_groups(D,C,B)',1)
vars['pair_no_drop_after_first']=s.replace('if time.monotonic()<A-.18:D=_local_improve_mixed_solution(D,C,B,A,include_pair_rewire=_B);D=_drop_unprofitable_groups(D,C,B)','if time.monotonic()<A-.18:D=_local_improve_mixed_solution(D,C,B,A,include_pair_rewire=_B)',1)
for name,text in vars.items():
 p=ROOT/'runs'/f'pair_{name}.py'; p.write_text(text); print(p)
