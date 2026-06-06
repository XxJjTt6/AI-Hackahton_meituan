from pathlib import Path
base=Path('solver.py').read_text()
# Reuse regret helper from nonscarce candidate, but call only if J low official-like before late low repairs.
helper=Path('runs/nonscarce_regret_insert.py').read_text().split('def _regret_insert_window_solution',1)[1].split('\ndef _scarce_seed401_cached_solution',1)[0]
helper='def _regret_insert_window_solution'+helper
s=base.replace('def _scarce_seed401_cached_solution', helper+'\ndef _scarce_seed401_cached_solution',1)
marker='\tif J and time.monotonic()<A-1.35:D=_low_deep_window_repair_solution(D,C,B,min(A,time.monotonic()+1.2))\n'
insert='\tif J and time.monotonic()<A-1.85:D=_regret_insert_window_solution(D,C,B,min(A,time.monotonic()+.45),max_remove=4)\n'
s=s.replace(marker,insert+marker,1)
Path('runs/low_regret_only.py').write_text(s)
print('runs/low_regret_only.py')
