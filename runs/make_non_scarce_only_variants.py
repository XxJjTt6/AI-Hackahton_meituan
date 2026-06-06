from pathlib import Path
base=Path('solver.py').read_text()
# Add non-scarce only additional medium/large tweaks after D chosen, guarded by not G.
variants={
 'nonscarce_skip_late_medium201.py': base.replace("\tif L==30 and d==60 and not G and not F:\n\t\tD=_medium_output_upgrade(D,C,B,L,d,e)\n\t\treturn D", "\tif L==30 and d==60 and not G and not F:\n\t\tD=_medium_output_upgrade(D,C,B,L,d,e)\n\t\treturn D",1),
 'nonscarce_extra_reassign.py': base.replace("\tif 9<=L<=35 and not G and not F and time.monotonic()<A-.95:D=_normal_worst_related_repair_solution(D,C,B,min(A,time.monotonic()+.75))", "\tif 9<=L<=35 and not G and not F and time.monotonic()<A-.95:D=_normal_worst_related_repair_solution(D,C,B,min(A,time.monotonic()+.75))\n\tif not G and not F and time.monotonic()<A-.28:\n\t\tK=_reassign_mixed_solution(D,C,B,min(A,time.monotonic()+.22))\n\t\tif _solution_expected_cost(K,C,B)<_solution_expected_cost(D,C,B)-1e-09:D=K",1),
 'nonscarce_extra_local.py': base.replace("\tif 9<=L<=35 and not G and not F and time.monotonic()<A-.95:D=_normal_worst_related_repair_solution(D,C,B,min(A,time.monotonic()+.75))", "\tif 9<=L<=35 and not G and not F and time.monotonic()<A-.95:D=_normal_worst_related_repair_solution(D,C,B,min(A,time.monotonic()+.75))\n\tif not G and not F and time.monotonic()<A-.35:D=_local_improve_mixed_solution(D,C,B,min(A,time.monotonic()+.28),include_pair_rewire=_D)",1),
}
for name,s in variants.items():
    p=Path('runs')/name; p.write_text(s); print(p)
