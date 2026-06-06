from pathlib import Path
base=Path('solver.py').read_text()
# Change random seeds in destroy/late acceptance only; deterministic variants might find different local minima.
repls=[('seed_destroy_321.py','random.Random(123)','random.Random(321)'),('seed_destroy_777.py','random.Random(123)','random.Random(777)'),('seed_random_start_42.py','random.Random(18)','random.Random(42)'),('seed_late_8128.py','random.Random(70331+len(D))','random.Random(8128+len(D))')]
for name,old,new in repls:
 s=base.replace(old,new,1); p=Path('runs')/name; p.write_text(s); print(p)
