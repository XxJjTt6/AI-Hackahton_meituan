from pathlib import Path
base=Path('solver.py').read_text()
out=Path('runs/large_window_candidates'); out.mkdir(exist_ok=True)
variants={
 'large_worst_once':[("if 9<=L<=35 and not G and not F and time.monotonic()<A-.55:D=_repair_worst_window_solution", "if 9<=L<=45 and not G and not F and time.monotonic()<A-.55:D=_repair_worst_window_solution")],
 'large_column_once':[("if 9<=L<=35 and not G and not F and time.monotonic()<A-.75:\n\t\t\tD=_column_alns_repair_solution", "if 9<=L<=45 and not G and not F and time.monotonic()<A-.75:\n\t\t\tD=_column_alns_repair_solution")],
 'large_related_once':[("if 9<=L<=35 and not G and not F and time.monotonic()<A-.85:D=_normal_worst_related_repair_solution", "if 9<=L<=45 and not G and not F and time.monotonic()<A-.85:D=_normal_worst_related_repair_solution")],
 'large_related_twice':[("if 9<=L<=35 and not G and not F and time.monotonic()<A-.85:D=_normal_worst_related_repair_solution", "if 9<=L<=45 and not G and not F and time.monotonic()<A-.85:D=_normal_worst_related_repair_solution"),("if 9<=L<=35 and not G and not F and time.monotonic()<A-.95:D=_normal_worst_related_repair_solution", "if 9<=L<=45 and not G and not F and time.monotonic()<A-.95:D=_normal_worst_related_repair_solution")],
 'large_all_normal_repairs':[("9<=L<=35 and not G and not F", "9<=L<=45 and not G and not F")],
}
for name,repls in variants.items():
    s=base
    for a,b in repls:
        if a not in s:
            raise SystemExit(f'missing pattern {name}: {a[:60]}')
        s=s.replace(a,b)
    p=out/(name+'.py')
    p.write_text(s)
    print(p)
