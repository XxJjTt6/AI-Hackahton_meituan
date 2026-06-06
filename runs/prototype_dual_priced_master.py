#!/usr/bin/env python3
"""Dual-priced restricted master prototype for AutoSolver.

Offline experiment only. It imports the current solver for parsing-compatible
cost functions and incumbent generation, then builds a reduced-cost column pool
and solves a small exact set-packing master under a time/node budget.
"""
from __future__ import annotations

import argparse
import importlib.util
import sys
import time
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
import solver  # type: ignore

Candidate = Tuple[str, Tuple[str, ...], str, float, float, int]
Result = List[Tuple[str, List[str]]]


def parse_input(text: str) -> Tuple[List[Candidate], List[str]]:
    lines = text.strip().splitlines()
    start = 1 if lines and lines[0].startswith("task_id_list") else 0
    candidates: List[Candidate] = []
    tasks = set()
    for row_id, line in enumerate(lines[start:]):
        parts = line.strip().split("\t")
        if len(parts) < 4:
            continue
        task_key, courier, score, willing = parts[:4]
        task_tuple = tuple(part.strip() for part in task_key.split(",") if part.strip())
        if not task_tuple or not courier:
            continue
        try:
            score_f = float(score)
            willing_f = float(willing)
        except ValueError:
            continue
        candidates.append((task_key.strip(), task_tuple, courier.strip(), score_f, willing_f, row_id))
        tasks.update(task_tuple)
    return candidates, sorted(tasks)


def group_cost(rows: Sequence[Candidate], task_count: int) -> float:
    return solver._group_expected_cost(tuple(rows), task_count)  # type: ignore[attr-defined]


def solution_cost(result: Result, candidates: Sequence[Candidate], tasks: Sequence[str]) -> float:
    return solver._solution_expected_cost(result, list(candidates), set(tasks))  # type: ignore[attr-defined]


def covered_count(result: Result, candidates: Sequence[Candidate]) -> int:
    return solver._solution_covered_count(result, list(candidates))  # type: ignore[attr-defined]


def selected_rows(result: Result, candidates: Sequence[Candidate]) -> Dict[Tuple[str, Tuple[str, ...]], List[Candidate]]:
    by_key = {(cand[0], cand[2]): cand for cand in candidates}
    selected: Dict[Tuple[str, Tuple[str, ...]], List[Candidate]] = {}
    for task_key, couriers in result:
        rows = [by_key.get((task_key, courier)) for courier in couriers]
        rows = [row for row in rows if row is not None]
        if rows:
            selected[(task_key, tuple(couriers))] = rows  # type: ignore[arg-type]
    return selected


def build_prices(incumbent: Result, candidates: Sequence[Candidate], tasks: Sequence[str]) -> Tuple[Dict[str, float], Dict[str, float]]:
    task_price = {task: 100.0 for task in tasks}
    courier_price: Dict[str, float] = {}
    for rows in selected_rows(incumbent, candidates).values():
        task_count = len(rows[0][1])
        cost = group_cost(rows, task_count)
        per_task = cost / max(1, task_count)
        for task in rows[0][1]:
            task_price[task] = max(task_price.get(task, 0.0), per_task)
        for row in rows:
            courier_price[row[2]] = max(courier_price.get(row[2], 0.0), cost / max(1, len(rows)))
    return task_price, courier_price


def make_column(rows: Sequence[Candidate], task_index: Dict[str, int], courier_index: Dict[str, int], source_rank: int):
    if not rows:
        return None
    task_tuple = rows[0][1]
    task_key = rows[0][0]
    if any(row[0] != task_key or row[1] != task_tuple for row in rows):
        return None
    if len({row[2] for row in rows}) != len(rows):
        return None
    task_mask = 0
    for task in task_tuple:
        if task not in task_index:
            return None
        task_mask |= 1 << task_index[task]
    courier_mask = 0
    for row in rows:
        courier_mask |= 1 << courier_index[row[2]]
    cost = group_cost(rows, len(task_tuple))
    return {
        "task_key": task_key,
        "rows": tuple(rows),
        "task_mask": task_mask,
        "courier_mask": courier_mask,
        "cost": cost,
        "source_rank": source_rank,
    }


def build_columns(candidates: Sequence[Candidate], tasks: Sequence[str], incumbent: Result, max_columns: int) -> List[dict]:
    task_index = {task: idx for idx, task in enumerate(tasks)}
    courier_index = {courier: idx for idx, courier in enumerate(sorted({cand[2] for cand in candidates}))}
    task_price, courier_price = build_prices(incumbent, candidates, tasks)
    columns: Dict[Tuple[int, int], dict] = {}

    def add_column(rows: Sequence[Candidate], source_rank: int) -> None:
        col = make_column(rows, task_index, courier_index, source_rank)
        if col is None:
            return
        key = (col["task_mask"], col["courier_mask"])
        old = columns.get(key)
        if old is None or col["cost"] < old["cost"] - 1e-9 or source_rank > old["source_rank"]:
            columns[key] = col

    # Always keep incumbent columns, so the master can reproduce current solution.
    for rows in selected_rows(incumbent, candidates).values():
        add_column(rows, 10)

    by_task_key: Dict[str, List[Candidate]] = {}
    for cand in candidates:
        by_task_key.setdefault(cand[0], []).append(cand)

    priced = []
    for task_key, rows in by_task_key.items():
        task_tuple = rows[0][1]
        task_value = sum(task_price.get(task, 100.0) for task in task_tuple)
        # Best single-courier row for this task_key/courier already canonical enough.
        best_by_courier: Dict[str, Candidate] = {}
        for row in rows:
            old = best_by_courier.get(row[2])
            if old is None or group_cost([row], len(task_tuple)) < group_cost([old], len(task_tuple)):
                best_by_courier[row[2]] = row
        elite = sorted(best_by_courier.values(), key=lambda row: group_cost([row], len(task_tuple)))[:10]
        for row in elite:
            cost = group_cost([row], len(task_tuple))
            reduced = cost - task_value + 0.15 * courier_price.get(row[2], 0.0)
            priced.append((reduced, cost, (row,)))
        # Multi-rider redundancy for low willingness / high penalty keys.
        for i in range(min(7, len(elite))):
            for j in range(i + 1, min(7, len(elite))):
                rows2 = (elite[i], elite[j])
                cost = group_cost(rows2, len(task_tuple))
                reduced = cost - task_value + 0.15 * sum(courier_price.get(row[2], 0.0) for row in rows2)
                if reduced < 20.0:
                    priced.append((reduced, cost, rows2))

    priced.sort(key=lambda item: (item[0], item[1], len(item[2])))
    for _reduced, _cost, rows in priced[:max_columns]:
        add_column(rows, 1)
    return list(columns.values())


def solve_master(columns: Sequence[dict], tasks: Sequence[str], deadline: float, node_limit: int) -> Result:
    task_count = len(tasks)
    all_mask = (1 << task_count) - 1
    by_task: List[List[dict]] = [[] for _ in tasks]
    for col in columns:
        mask = col["task_mask"]
        for idx in range(task_count):
            if mask & (1 << idx):
                by_task[idx].append(col)
    for opts in by_task:
        opts.sort(key=lambda col: (-col["source_rank"], col["cost"] / max(1, int(col["task_mask"]).bit_count()), col["cost"]))

    best_score = 100.0 * task_count
    best_cols: List[dict] = []
    memo: Dict[Tuple[int, int], float] = {}
    nodes = 0

    def choose_task(decided: int, couriers: int):
        rem = all_mask & ~decided
        best_idx = None
        best_opts = None
        while rem:
            bit = rem & -rem
            idx = bit.bit_length() - 1
            opts = [col for col in by_task[idx] if not (col["task_mask"] & decided) and not (col["courier_mask"] & couriers)]
            if best_opts is None or len(opts) < len(best_opts):
                best_idx = idx
                best_opts = opts
                if not opts:
                    break
            rem ^= bit
        return best_idx, best_opts or []

    def dfs(decided: int, couriers: int, score: float, selected: List[dict]) -> None:
        nonlocal best_score, best_cols, nodes
        nodes += 1
        if nodes > node_limit or time.monotonic() > deadline:
            return
        lower = score + 100.0 * (task_count - int(decided.bit_count()))
        # This lower bound is not tight for columns covering multiple tasks, so use only current score prune.
        if score >= best_score - 1e-9:
            return
        state = (decided, couriers)
        old = memo.get(state)
        if old is not None and old <= score + 1e-9:
            return
        memo[state] = score
        if decided == all_mask:
            best_score = score
            best_cols = list(selected)
            return
        idx, opts = choose_task(decided, couriers)
        if idx is None:
            if score < best_score:
                best_score = score
                best_cols = list(selected)
            return
        branch_opts = [col for col in opts if col["source_rank"] >= 10] + [col for col in opts if col["source_rank"] < 10][:16]
        for col in branch_opts:
            selected.append(col)
            dfs(decided | col["task_mask"], couriers | col["courier_mask"], score + col["cost"], selected)
            selected.pop()
        dfs(decided | (1 << idx), couriers, score + 100.0, selected)

    dfs(0, 0, 0.0, [])
    result = []
    for col in sorted(best_cols, key=lambda c: (min(row[5] for row in c["rows"]), c["task_key"])):
        result.append((col["task_key"], [row[2] for row in col["rows"]]))
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input")
    parser.add_argument("--max-columns", type=int, default=260)
    parser.add_argument("--seconds", type=float, default=4.0)
    parser.add_argument("--nodes", type=int, default=25000)
    args = parser.parse_args()

    text = Path(args.input).read_text()
    candidates, tasks = parse_input(text)
    start = time.monotonic()
    incumbent = solver.solve(text)
    inc_cost = solution_cost(incumbent, candidates, tasks)
    cols = build_columns(candidates, tasks, incumbent, args.max_columns)
    result = solve_master(cols, tasks, time.monotonic() + args.seconds, args.nodes)
    cand_cost = solution_cost(result, candidates, tasks)
    print(f"tasks={len(tasks)} candidates={len(candidates)} columns={len(cols)}")
    print(f"incumbent cost={inc_cost:.6f} covered={covered_count(incumbent, candidates)} groups={len(incumbent)}")
    print(f"master    cost={cand_cost:.6f} covered={covered_count(result, candidates)} groups={len(result)}")
    print(f"delta={cand_cost - inc_cost:+.6f} elapsed={time.monotonic() - start:.3f}s")
    if cand_cost < inc_cost - 1e-9:
        print("IMPROVED")
        print(result)


if __name__ == "__main__":
    main()
