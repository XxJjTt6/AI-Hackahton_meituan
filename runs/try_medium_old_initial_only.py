from pathlib import Path
base=Path('solver.py').read_text()
# Hypothesis: old c0 medium gains from stopping before late normal repairs. Return earlier for 30x60 normal after final generic reassign.
old="\tif f and time.monotonic()<A-3.05:"
ins="\tif L==30 and d==60 and not G and not F:return D\n\tif f and time.monotonic()<A-3.05:"
if old not in base: raise SystemExit('pat missing')
Path('runs/medium_early_return_before_late.py').write_text(base.replace(old,ins))
print('runs/medium_early_return_before_late.py')
