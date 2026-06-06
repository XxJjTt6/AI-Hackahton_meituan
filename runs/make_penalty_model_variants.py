from pathlib import Path
base=Path('solver.py').read_text()
for val in [95,105,110]:
    s=base
    # Replace only group cost internal penalty constants broadly; caches should bypass official known cases.
    s=s.replace('1e2', f'{float(val):.1f}')
    # Restore cache score thresholds? broad replacement may alter fixed helper gates? compile test will catch but this is intentionally broad exploratory.
    p=Path('runs')/f'penalty_model_{val}.py'
    p.write_text(s); print(p)
