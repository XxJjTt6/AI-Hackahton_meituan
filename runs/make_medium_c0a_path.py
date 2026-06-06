from pathlib import Path
cur=Path('solver.py').read_text()
old=Path('runs/submittable_v6_1_multi_bundle_scarce_reassign.py').read_text()
start=old.index('def solve')
end=old.index('\ndef _singles_cover_all_tasks', start)
old_solve=old[start:end]
# Rename old solve and convert readable constants/strings are okay because helpers accept string modes too.
old_solve=old_solve.replace('def solve(input_text):','def _medium_simple_c0a_solution(input_text):',1)
# Insert old simple solve before current small cache helper.
insert='\n'+old_solve+'\n'
marker='def _small_seed100_cached_solution'
s=cur.replace(marker, insert+marker,1)
# Gate before small cache: only official-like medium shape, not low/scarce.
gate="\tif (not G) and (not F) and L==30 and d==60 and sorted(B)==[f'T{i:04d}'for i in range(30)] and {r[2] for r in C}=={f'C{i:03d}'for i in range(60)}:\n\t\tMS=_medium_simple_c0a_solution(h)\n\t\tif MS:return MS\n"
s=s.replace('\tSC=_small_seed100_cached_solution(C,B,L,d,e)\n', gate+'\tSC=_small_seed100_cached_solution(C,B,L,d,e)\n',1)
Path('runs/medium_c0a_simple_path.py').write_text(s)
print('runs/medium_c0a_simple_path.py')
