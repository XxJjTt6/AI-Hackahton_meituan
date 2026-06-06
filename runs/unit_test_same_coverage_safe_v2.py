#!/usr/bin/env python3
import importlib.util
from pathlib import Path
ROOT = Path('/Users/比赛/FOR_AutoSolver_706.72')

def load(path):
    spec = importlib.util.spec_from_file_location('m', ROOT/path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def build_rows(conflict_extra=False):
    pairs=[('T0000,T0027',['C005']),('T0001,T0035',['C018']),('T0002,T0038',['C009']),('T0003,T0024',['C012']),('T0004,T0018',['C007']),('T0005,T0036',['C019']),('T0006,T0030',['C003']),('T0007,T0008',['C001']),('T0009,T0011',['C014']),('T0010,T0029',['C004']),('T0012,T0019',['C010']),('T0013,T0039',['C013']),('T0014,T0031',['C008']),('T0015,T0034',['C015']),('T0016',['C000']),('T0017,T0032',['C002']),('T0020,T0023',['C016']),('T0021,T0026',['C017']),('T0022,T0037',['C011']),('T0025,T0028',['C006'])]
    rows=[]; idx=0
    for key,couriers in pairs:
        for courier in couriers:
            rows.append((key, tuple(key.split(',')), courier, 80.0, .5, idx)); idx += 1
    rows.append(('T0001', ('T0001',), 'C020', 1.0, .99, idx)); idx += 1
    rows.append(('T0035', ('T0035',), 'C021', 1.0, .99, idx)); idx += 1
    if conflict_extra:
        rows.append(('T0013,T0039', ('T0013','T0039'), 'C000', 1.0, .99, idx)); idx += 1
    return pairs, rows

def covered_from_rows(mod, out, rows):
    row = {(r[0], r[2]): r for r in rows}
    sel = mod._result_to_selected(out, row)
    return {t for group in sel.values() for t in group[0][1]}, [r[2] for group in sel.values() for r in group]

def main():
    mod = load(Path('runs/held_20260518_same_coverage_safe_v2.py'))
    for conflict in (False, True):
        pairs, rows = build_rows(conflict)
        base = [(key, couriers) for key, couriers in pairs]
        out = mod._scarce_same_coverage_safe_v2(base, rows, {f'T{i:04d}' for i in range(40)})
        assert out is not None, 'positive replacement should trigger'
        cov, used = covered_from_rows(mod, out, rows)
        base_cov, _ = covered_from_rows(mod, base, rows)
        assert cov == base_cov, (conflict, sorted(base_cov - cov), sorted(cov - base_cov))
        assert len(used) == len(set(used)), 'duplicate courier after safe repack'
    print('same_coverage_safe_v2 tests OK')

if __name__ == '__main__':
    main()
