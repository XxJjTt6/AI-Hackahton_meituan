#!/usr/bin/env python3
import importlib.util, sys, json
from pathlib import Path
ROOT=Path('/Users/比赛/FOR_AutoSolver_706.72')
BAD_SCARCE_PATTERNS=[
    {'missing':['T0028','T0033'], 'groups': {'T0016,T0020': ['C016'], 'T0023,T0025': ['C006']}},
]

def load(path):
    spec=importlib.util.spec_from_file_location('m', ROOT/path)
    mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod

def official_json_pattern(path):
    data=json.load(open(path)); cr=next(c for c in data['result']['case_results'] if c['case_file']=='scarce_couriers_seed401.txt')
    covered={t for g in cr['detail'] for t in g['task_id_list'].split(',')}
    groups={g['task_id_list']:g['couriers'] for g in cr['detail']}
    return {'missing':sorted({f'T{i:04d}' for i in range(40)}-covered),'groups':groups,'score':cr['total_score']}

def is_bad_pattern(pattern):
    for bad in BAD_SCARCE_PATTERNS:
        if pattern['missing'] != bad['missing']:
            continue
        ok=True
        for key,couriers in bad['groups'].items():
            if pattern['groups'].get(key)!=couriers: ok=False; break
        if ok: return True
    return False

def main():
    for arg in sys.argv[1:]:
        p=Path(arg)
        if p.suffix=='.json':
            pat=official_json_pattern(p)
            print(arg, 'bad_pattern', is_bad_pattern(pat), pat['score'], pat['missing'])
        else:
            print(arg, 'script only checks official JSON patterns currently')
if __name__=='__main__': main()
