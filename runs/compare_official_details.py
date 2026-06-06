#!/usr/bin/env python3
import json, sys
from pathlib import Path

def detail_map(path, case='scarce_couriers_seed401.txt'):
    data = json.load(open(path))
    cr = next(c for c in data['result']['case_results'] if c['case_file'] == case)
    groups = [(g['task_id_list'], tuple(g['couriers']), g['cost'], g['p_complete']) for g in cr['detail']]
    covered = set()
    for key, *_ in groups:
        covered.update(key.split(','))
    return cr['total_score'], cr['assigned_count'], covered, sorted(groups)

def main():
    base = Path(sys.argv[1])
    cand = Path(sys.argv[2])
    bs, ba, bc, bg = detail_map(base)
    cs, ca, cc, cg = detail_map(cand)
    print('base', base.name, bs, ba, 'missing', sorted({f'T{i:04d}' for i in range(40)} - bc))
    print('cand', cand.name, cs, ca, 'missing', sorted({f'T{i:04d}' for i in range(40)} - cc))
    print('removed:')
    for g in bg:
        if g not in cg: print(' -', g)
    print('added:')
    for g in cg:
        if g not in bg: print(' +', g)

if __name__ == '__main__':
    main()
