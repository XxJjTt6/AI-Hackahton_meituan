from pathlib import Path
base=Path('solver.py').read_text()
# Candidate combining current best caches with rank_ratio_first no-op speed tweak.
s=base.replace("return F,A/max(1,H),G,A/max(B,1e-09),A,-len(E)", "return A/max(B,1e-09),F,A/max(1,H),G,A,-len(E)",1)
Path('runs/current_best_rank_ratio_first.py').write_text(s)
print('runs/current_best_rank_ratio_first.py')
