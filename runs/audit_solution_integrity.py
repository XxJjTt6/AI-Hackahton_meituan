#!/usr/bin/env python3
import importlib.util, sys, json
from pathlib import Path
ROOT = Path('/Users/比赛/FOR_AutoSolver_706.72')
DATA = ROOT/'Fwd_ 【美团AI Hackathon大赛】-【命题四AutoSolver：让AI Agent 自主求解配送分配问题】脱敏数据'/'large_seed301.txt'

def load_solver(path):
    spec = importlib.util.spec_from_file_location('solver_mod', ROOT/path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def parse(text):
    lines = text.strip().splitlines()
    start = 1 if lines and lines[0].startswith('task') else 0
    rows = []
    tasks = set()
    couriers = set()
    for idx, line in enumerate(lines[start:]):
        parts = line.split('\t')
        if len(parts) < 4:
            continue
        key, courier, score, willingness = parts[:4]
        task_tuple = tuple(t.strip() for t in key.split(',') if t.strip())
        rows.append((key, task_tuple, courier, float(score), float(willingness), idx))
        tasks.update(task_tuple)
        couriers.add(courier)
    return rows, tasks, couriers

def audit(output, rows, true_tasks=None):
    row_map = {(r[0], r[2]): r for r in rows}
    key_covered = set()
    row_covered = set()
    used = set()
    errors = []
    for key, couriers in output:
        key_tasks = tuple(t.strip() for t in key.split(',') if t.strip())
        key_covered.update(key_tasks)
        group_rows = []
        for courier in couriers:
            if courier in used:
                errors.append(('duplicate_courier', key, courier))
            used.add(courier)
            row = row_map.get((key, courier))
            if row is None:
                errors.append(('missing_row', key, courier))
            else:
                group_rows.append(row)
        if group_rows:
            base_tasks = tuple(group_rows[0][1])
            for row in group_rows:
                if tuple(row[1]) != base_tasks:
                    errors.append(('mixed_task_rows', key, courier, base_tasks, row[1]))
            if tuple(key_tasks) != base_tasks:
                errors.append(('key_row_task_mismatch', key, base_tasks))
            row_covered.update(base_tasks)
    true_tasks = set(true_tasks or {t for _, ts, *_ in rows for t in ts})
    return {
        'key_covered': sorted(key_covered),
        'row_covered': sorted(row_covered),
        'missing_by_key': sorted(true_tasks - key_covered),
        'missing_by_row': sorted(true_tasks - row_covered),
        'extra_by_key': sorted(key_covered - true_tasks),
        'extra_by_row': sorted(row_covered - true_tasks),
        'used_couriers': len(used),
        'groups': len(output),
        'errors': errors,
        'ok': not errors and key_covered == row_covered and row_covered <= true_tasks,
    }

def main():
    solver_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('solver.py')
    text = DATA.read_text()
    rows, tasks, _ = parse(text)
    mod = load_solver(solver_path)
    output = mod.solve(text)
    report = audit(output, rows, tasks)
    print(json.dumps(report, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main()
