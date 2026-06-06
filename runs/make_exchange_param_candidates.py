from pathlib import Path
base=Path('solver.py').read_text()
out=Path('runs/exchange_param_candidates'); out.mkdir(exist_ok=True)
vars={
 'normal_pair_more_pairs': {'max_pairs=32':'max_pairs=52'},
 'normal_triple_more_triples': {'max_triples=16':'max_triples=32'},
 'normal_exch_wide_tasks': {'max_window_tasks=10,max_pairs=32':'max_window_tasks=12,max_pairs=32', 'max_window_tasks=12,max_triples=16':'max_window_tasks=14,max_triples=16'},
 'normal_exch_top10': {'top_riders_per_task_key=8,option_limit=55,max_window_tasks=10,max_pairs=32':'top_riders_per_task_key=10,option_limit=70,max_window_tasks=10,max_pairs=32'},
 'normal_all_exchange_more': {'max_pairs=32':'max_pairs=48','max_triples=16':'max_triples=28'},
 'large_enable_all_normal': {'9<=L<=35 and not G and not F':'9<=L<=45 and not G and not F'},
}
for name,repls in vars.items():
    s=base
    for a,b in repls.items():
        n=s.count(a)
        if n==0: raise SystemExit(f'{name} missing {a}')
        s=s.replace(a,b)
    p=out/(name+'.py'); p.write_text(s); print(p)
