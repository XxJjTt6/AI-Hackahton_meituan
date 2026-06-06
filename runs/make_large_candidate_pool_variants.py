from pathlib import Path
base=Path('solver.py').read_text()
variants={
 'large_pair_lookahead6.py': base.replace('lookahead=5 if F else 4,flexible_initial=F', 'lookahead=5 if F else 6,flexible_initial=F',1),
 'large_pair_flex.py': base.replace('lookahead=5 if F else 4,flexible_initial=F', 'lookahead=5 if F else 4,flexible_initial=_B',1),
 'large_destroy_short.py': base.replace('AB=min(A,time.monotonic()+5.5)if O else min(A,time.monotonic()+_E)', 'AB=min(A,time.monotonic()+3.5)if O else min(A,time.monotonic()+_E)',1),
}
for name,s in variants.items():
    p=Path('runs')/name; p.write_text(s); print(p)
