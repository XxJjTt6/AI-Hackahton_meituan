#!/usr/bin/env python3
from __future__ import annotations

import argparse
import itertools
import sys
import time
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from autosolver.competition_audit import (  # noqa: E402
    group_expected_cost,
    parse_competition_rows,
    result_metrics,
    summarize_solver,
)


def build_columns(rows_by_key, tasks, max_k=2, top_rows_per_key=10, max_columns=1800):
    task_list = sorted(tasks)
    task_index = {task: index for index, task in enumerate(task_list)}
    courier_list = sorted({row.courier_id for row in rows_by_key.values()})
    courier_index = {courier: index for index, courier in enumerate(courier_list)}
    by_key = defaultdict(list)
    for row in rows_by_key.values():
        if all(task in task_index for task in row.task_ids):
            by_key[row.task_key].append(row)
    columns = []
    for key, rows in by_key.items():
        rows = sorted(rows, key=lambda row: (group_expected_cost([row], len(row.task_ids)), -row.willingness, row.total_score, row.row_index))[:top_rows_per_key]
        task_mask = 0
        for task in rows[0].task_ids:
            task_mask |= 1 << task_index[task]
        task_count = len(rows[0].task_ids)
        options = []
        for k in range(1, min(max_k, len(rows)) + 1):
            for combo in itertools.combinations(rows, k):
                courier_mask = 0
                couriers = []
                ok = True
                for row in combo:
                    bit = 1 << courier_index[row.courier_id]
                    if courier_mask & bit:
                        ok = False
                        break
                    courier_mask |= bit
                    couriers.append(row.courier_id)
                if not ok:
                    continue
                cost = group_expected_cost(combo, task_count)
                saving = 100.0 * task_count - cost
                if saving <= -25.0:
                    continue
                options.append((cost, -saving, len(couriers), tuple(sorted(couriers)), combo, courier_mask))
        options.sort()
        for cost, _neg_saving, _k, couriers, combo, courier_mask in options[:8]:
            saving = 100.0 * task_count - cost
            density = saving / max(1, task_count + len(couriers) * 0.35)
            columns.append((density, saving, cost, task_mask, courier_mask, key, couriers, task_count))
    columns.sort(key=lambda item: (item[0], item[1], -item[2], item[7]), reverse=True)
    return columns[:max_columns], task_list


def solution_state(solution, rows, task_index, courier_index):
    used_tasks = 0
    used_couriers = 0
    cost = 0.0
    from autosolver.competition_audit import group_expected_cost
    for task_key, couriers in solution:
        group = []
        for courier in couriers:
            row = rows.get((task_key, courier))
            if row is None:
                return None
            group.append(row)
            bit = 1 << courier_index[courier]
            if used_couriers & bit:
                return None
            used_couriers |= bit
        if not group:
            return None
        for task in group[0].task_ids:
            bit = 1 << task_index[task]
            if used_tasks & bit:
                return None
            used_tasks |= bit
        cost += group_expected_cost(group, len(group[0].task_ids))
    return cost, used_tasks, used_couriers, list(solution)


def pack_columns(columns, task_count, beam_width=4000, incumbent_state=None):
    states = [(0.0, 0, 0, [])]
    best = (100.0 * task_count, 0, 0, [])
    if incumbent_state is not None:
        states.append(incumbent_state)
        best = incumbent_state
    seen_best = {}
    for column in columns:
        _density, _saving, cost, task_mask, courier_mask, key, couriers, _task_count = column
        new_states = []
        for current_cost, used_tasks, used_couriers, path in states:
            if used_tasks & task_mask or used_couriers & courier_mask:
                continue
            new_cost = current_cost + cost
            new_tasks = used_tasks | task_mask
            new_couriers = used_couriers | courier_mask
            new_path = path + [(key, list(couriers))]
            new_states.append((new_cost, new_tasks, new_couriers, new_path))
            total = new_cost + 100.0 * (task_count - new_tasks.bit_count())
            if total < best[0] - 1e-9 or (abs(total - best[0]) < 1e-9 and new_tasks.bit_count() > best[1].bit_count()):
                best = (total, new_tasks, new_couriers, new_path)
        if new_states:
            states.extend(new_states)
            states.sort(key=lambda state: (state[0] + 100.0 * (task_count - state[1].bit_count()), -state[1].bit_count(), state[2].bit_count()))
            pruned = []
            seen_best.clear()
            for state in states:
                key_state = (state[1], state[2])
                if key_state in seen_best:
                    continue
                seen_best[key_state] = state[0]
                pruned.append(state)
                if len(pruned) >= beam_width:
                    break
            states = pruned
    return best[3], best[0]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input_file")
    parser.add_argument("--baseline", default="runs/baselines/official_best_70222083.py")
    parser.add_argument("--max-k", type=int, default=2)
    parser.add_argument("--top-rows", type=int, default=10)
    parser.add_argument("--max-columns", type=int, default=1800)
    parser.add_argument("--beam", type=int, default=4000)
    args = parser.parse_args()

    input_text = Path(args.input_file).read_text(encoding="utf-8")
    rows, tasks = parse_competition_rows(input_text)
    start = time.monotonic()
    t_base0=time.monotonic(); baseline = summarize_solver(args.baseline, input_text); t_base=time.monotonic()
    columns, task_list = build_columns(rows, tasks, max_k=args.max_k, top_rows_per_key=args.top_rows, max_columns=args.max_columns)
    task_index = {task: index for index, task in enumerate(task_list)}
    courier_list = sorted({row.courier_id for row in rows.values()})
    courier_index = {courier: index for index, courier in enumerate(courier_list)}
    t_build=time.monotonic()
    incumbent_solution = __import__("autosolver.competition_audit", fromlist=["load_solver_module"]).load_solver_module(args.baseline).solve(input_text); t_inc=time.monotonic()
    incumbent_state = solution_state(incumbent_solution, rows, task_index, courier_index)
    solution, packed_cost = pack_columns(columns, len(task_list), beam_width=args.beam, incumbent_state=incumbent_state)
    t_pack=time.monotonic(); metrics = result_metrics(solution, rows, tasks)
    elapsed = time.monotonic() - start
    print("columns", len(columns), "tasks", len(task_list), "elapsed", round(elapsed, 3), "base", round(t_base-t_base0,3), "build", round(t_build-t_base,3), "inc", round(t_inc-t_build,3), "pack", round(t_pack-t_inc,3))
    print("baseline", round(baseline["expected_cost"], 6), "cov", baseline["covered_tasks"], "struct", baseline["tasks_per_group"], baseline["riders_per_group"])
    print("packed", round(metrics["expected_cost"], 6), "delta", round(metrics["expected_cost"] - baseline["expected_cost"], 6), "cov", metrics["covered_tasks"], "struct", metrics["tasks_per_group"], metrics["riders_per_group"], "valid", metrics["valid"])
    if metrics["expected_cost"] < baseline["expected_cost"] - 1e-9:
        print(solution)


if __name__ == "__main__":
    main()
