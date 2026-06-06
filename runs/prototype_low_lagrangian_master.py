#!/usr/bin/env python3
from __future__ import annotations

import argparse
import itertools
import math
import random
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from autosolver.competition_audit import (  # noqa: E402
    CompetitionRow,
    group_expected_cost,
    parse_competition_rows,
    result_metrics,
    summarize_solver,
)


def build_task_columns(rows_by_key, all_tasks, max_k=4, top_rows=14, column_limit=90):
    by_task = defaultdict(list)
    for row in rows_by_key.values():
        if len(row.task_ids) == 1:
            by_task[row.task_ids[0]].append(row)
    columns = {}
    for task in sorted(all_tasks):
        pool = sorted(
            by_task.get(task, []),
            key=lambda row: (group_expected_cost([row], 1), -row.willingness, row.total_score, row.row_index),
        )[:top_rows]
        task_columns = []
        for k in range(1, min(max_k, len(pool)) + 1):
            for combo in itertools.combinations(pool, k):
                couriers = tuple(sorted(row.courier_id for row in combo))
                base_cost = group_expected_cost(combo, 1)
                avg_w = sum(row.willingness for row in combo) / len(combo)
                avg_score = sum(row.total_score for row in combo) / len(combo)
                task_columns.append((base_cost, couriers, combo, avg_w, avg_score))
        task_columns.sort(key=lambda item: (item[0], len(item[1]), -item[3], item[4]))
        dedup = []
        seen = set()
        for item in task_columns:
            if item[1] in seen:
                continue
            seen.add(item[1])
            dedup.append(item)
            if len(dedup) >= column_limit:
                break
        columns[task] = dedup
    return columns


def greedy_repair(chosen_by_task, columns, prices=None, cardinality_penalty=0.0):
    prices = prices or defaultdict(float)
    selected = {}
    used = set()
    order = []
    for task, chosen in chosen_by_task.items():
        best = columns[task][0]
        regret = (columns[task][1][0] - best[0]) if len(columns[task]) > 1 else 100.0
        order.append((regret, chosen[0], task))
    for _, _, task in sorted(order, reverse=True):
        feasible = [col for col in columns[task] if not (set(col[1]) & used)]
        if not feasible:
            continue
        col = min(feasible, key=lambda item: item[0] + cardinality_penalty * len(item[1]) + 0.05 * sum(prices[c] for c in item[1]))
        selected[task] = col
        used.update(col[1])
    return selected


def selected_to_solution(selected):
    solution = []
    for task, (_, couriers, _combo, _avg_w, _avg_score) in sorted(selected.items()):
        solution.append((task, list(couriers)))
    return solution


def lagrangian_master(rows_by_key, all_tasks, max_k=4, top_rows=14, iterations=80, seed=7, cardinality_penalty=12.0):
    columns = build_task_columns(rows_by_key, all_tasks, max_k=max_k, top_rows=top_rows)
    rng = random.Random(seed)
    prices = defaultdict(float)
    best_solution = []
    best_cost = float("inf")
    best_selected = {}
    for iteration in range(iterations):
        chosen = {}
        usage = Counter()
        temperature = max(0.0, 1.0 - iteration / max(1, iterations - 1))
        for task, task_columns in columns.items():
            if not task_columns:
                continue
            scored = []
            for col in task_columns:
                base_cost, couriers, _combo, avg_w, avg_score = col
                noisy = temperature * 0.015 * rng.random() * base_cost
                score = base_cost + cardinality_penalty * len(couriers) + sum(prices[c] for c in couriers) + noisy - 0.02 * avg_w + 0.002 * avg_score
                scored.append((score, col))
            col = min(scored, key=lambda item: item[0])[1]
            chosen[task] = col
            usage.update(col[1])
        repaired = greedy_repair(chosen, columns, prices, cardinality_penalty=cardinality_penalty)
        solution = selected_to_solution(repaired)
        metrics = result_metrics(solution, rows_by_key, all_tasks)
        if metrics["valid"] and metrics["expected_cost"] < best_cost:
            best_cost = metrics["expected_cost"]
            best_solution = solution
            best_selected = repaired
        step = 3.0 / math.sqrt(iteration + 1)
        for courier, count in usage.items():
            prices[courier] = max(-8.0, min(20.0, prices[courier] + step * (count - 1)))
        used_best = Counter(c for col in best_selected.values() for c in col[1])
        for courier in list(prices):
            if used_best[courier] == 0:
                prices[courier] *= 0.985
    return best_solution, best_cost


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input_file")
    parser.add_argument("--baseline", default="runs/baselines/official_best_70222083.py")
    parser.add_argument("--iterations", type=int, default=100)
    parser.add_argument("--top-rows", type=int, default=14)
    parser.add_argument("--max-k", type=int, default=4)
    parser.add_argument("--penalties", default="0,5,10,12,15,20,30")
    args = parser.parse_args()

    input_text = Path(args.input_file).read_text(encoding="utf-8")
    rows, tasks = parse_competition_rows(input_text)
    start = time.monotonic()
    baseline = summarize_solver(args.baseline, input_text)
    best = None
    for penalty in [float(x) for x in args.penalties.split(",") if x.strip()]:
        solution, cost = lagrangian_master(rows, tasks, max_k=args.max_k, top_rows=args.top_rows, iterations=args.iterations, cardinality_penalty=penalty)
        metrics = result_metrics(solution, rows, tasks)
        ranked = (0 if metrics["covered_tasks"] == len(tasks) else 1, cost, penalty, solution, metrics)
        if best is None or ranked < best:
            best = ranked
        print("trial_penalty", penalty, "cost", round(cost, 6), "covered", metrics["covered_tasks"], "struct", metrics["riders_per_group"])
    _, cost, penalty, solution, metrics = best
    elapsed = time.monotonic() - start
    print("baseline_cost", round(baseline["expected_cost"], 6), "baseline_struct", baseline["riders_per_group"])
    print("master_cost", round(cost, 6), "delta", round(cost - baseline["expected_cost"], 6), "best_penalty", penalty, "elapsed", round(elapsed, 3))
    print("master_valid", metrics["valid"], "covered", metrics["covered_tasks"], "groups", metrics["groups"], "used", metrics["used_couriers"])
    print("master_struct", metrics["riders_per_group"], "tasks/group", metrics["tasks_per_group"])
    for item in solution[:5]:
        print("sample", item)


if __name__ == "__main__":
    main()
