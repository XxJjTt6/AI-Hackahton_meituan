#!/usr/bin/env python3
"""Offline low_willingness_seed501 observed-column search.

Mines official result JSON files for valid low_willingness_seed501 detail rows,
treats judge `cost` as the row objective, then searches for a legal recombination
with unique tasks and unique couriers. This is analysis-only: it never imports or
modifies solver.py and never submits anything.
"""
from __future__ import annotations

import argparse
import glob
import json
import math
import time
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

TASK_COUNT = 30
TASKS = tuple(f"T{i:04d}" for i in range(TASK_COUNT))
TASK_INDEX = {task: i for i, task in enumerate(TASKS)}
PENALTY = 100.0
DEFAULT_REPORT = Path("runs/501_official_column_search_latest.md")


@dataclass(frozen=True)
class Row:
    task_key: str
    tasks: tuple[str, ...]
    couriers: tuple[str, ...]
    cost: float
    source: str
    total_score: float

    @property
    def key(self) -> tuple[str, tuple[str, ...]]:
        return self.task_key, self.couriers

    @property
    def task_mask(self) -> int:
        mask = 0
        for task in self.tasks:
            mask |= 1 << TASK_INDEX[task]
        return mask

    @property
    def saving(self) -> float:
        return PENALTY * len(self.tasks) - self.cost


def norm_tasks(task_key: str) -> tuple[str, ...]:
    return tuple(part.strip() for part in task_key.split(",") if part.strip())


def norm_couriers(value: object) -> tuple[str, ...]:
    if isinstance(value, list):
        return tuple(str(c).strip() for c in value if str(c).strip())
    if isinstance(value, str):
        return tuple(part.strip() for part in value.split(",") if part.strip())
    return ()


def iter_low_cases(patterns: Sequence[str]) -> Iterable[tuple[str, dict]]:
    seen = set()
    for pattern in patterns:
        for path in sorted(glob.glob(pattern)):
            if path in seen:
                continue
            seen.add(path)
            try:
                data = json.loads(Path(path).read_text())
            except Exception:
                continue
            result = data.get("result") if isinstance(data, dict) else None
            if not isinstance(result, dict):
                continue
            for case in result.get("case_results", []) or []:
                if not isinstance(case, dict):
                    continue
                if case.get("case_file") == "low_willingness_seed501.txt":
                    yield path, case


def collect_rows(patterns: Sequence[str]) -> tuple[list[tuple[str, dict]], list[Row], list[Row]]:
    cases = list(iter_low_cases(patterns))
    all_rows: list[Row] = []
    valid_rows_by_key: dict[tuple[str, tuple[str, ...]], list[Row]] = defaultdict(list)
    for path, case in cases:
        valid = bool(case.get("validity", True))
        total = float(case.get("total_score", math.nan))
        for detail in case.get("detail", []) or []:
            if not isinstance(detail, dict) or "cost" not in detail:
                continue
            task_key = str(detail.get("task_id_list") or "").strip()
            tasks = norm_tasks(task_key)
            couriers = norm_couriers(detail.get("couriers"))
            if not task_key or not tasks or not couriers:
                continue
            if any(task not in TASK_INDEX for task in tasks):
                continue
            row = Row(task_key, tasks, couriers, float(detail["cost"]), path, total)
            all_rows.append(row)
            if valid:
                valid_rows_by_key[row.key].append(row)
    canonical = [min(rows, key=lambda row: row.cost) for rows in valid_rows_by_key.values()]
    return cases, all_rows, canonical


def prepare_rows(rows: Sequence[Row], per_task_limit: int) -> tuple[list[tuple[int, int, Row]], dict[int, list[tuple[int, int, Row]]], dict[str, int]]:
    couriers = sorted({courier for row in rows for courier in row.couriers})
    courier_index = {courier: i for i, courier in enumerate(couriers)}
    info = []
    for row in rows:
        cm = 0
        for courier in row.couriers:
            cm |= 1 << courier_index[courier]
        info.append((row.task_mask, cm, row))
    by_task: dict[int, list[tuple[int, int, Row]]] = {idx: [] for idx in range(TASK_COUNT)}
    for item in info:
        tm, _cm, _row = item
        for idx in range(TASK_COUNT):
            if tm >> idx & 1:
                by_task[idx].append(item)
    for idx in range(TASK_COUNT):
        by_task[idx].sort(key=lambda item: (item[2].cost / len(item[2].tasks), item[2].cost, len(item[2].couriers)))
        by_task[idx] = by_task[idx][:per_task_limit]
    pool_keys = {(item[2].key) for values in by_task.values() for item in values}
    info = [item for item in info if item[2].key in pool_keys]
    by_task = {idx: [] for idx in range(TASK_COUNT)}
    for item in info:
        tm, _cm, _row = item
        for idx in range(TASK_COUNT):
            if tm >> idx & 1:
                by_task[idx].append(item)
    return info, by_task, courier_index


def greedy_seed(info: Sequence[tuple[int, int, Row]]) -> tuple[float, list[Row]]:
    best_score = PENALTY * TASK_COUNT
    best_rows: list[Row] = []
    orderings = [
        lambda item: (item[2].cost - PENALTY * len(item[2].tasks), item[2].cost),
        lambda item: (item[2].cost / len(item[2].tasks), item[2].cost),
        lambda item: (-item[2].saving / max(1, len(item[2].couriers)), item[2].cost),
    ]
    for key in orderings:
        decided = 0
        couriers = 0
        score = 0.0
        chosen: list[Row] = []
        for tm, cm, row in sorted(info, key=key):
            if tm & decided or cm & couriers:
                continue
            if row.cost >= PENALTY * len(row.tasks):
                continue
            decided |= tm
            couriers |= cm
            score += row.cost
            chosen.append(row)
        score += PENALTY * (TASK_COUNT - decided.bit_count())
        if score < best_score:
            best_score = score
            best_rows = chosen
    return best_score, sorted(best_rows, key=lambda row: row.task_key)


def solve_set_packing(rows: Sequence[Row], per_task_limit: int, seconds: float, initial_best: float | None = None, initial_rows: Sequence[Row] = ()) -> tuple[float, list[Row], int, bool]:
    info, by_task, _courier_index = prepare_rows(rows, per_task_limit)
    seed_score, seed_rows = greedy_seed(info)
    best_score = initial_best if initial_best is not None else seed_score
    best_rows = sorted(initial_rows, key=lambda row: row.task_key)
    if seed_score < best_score - 1e-9 or not best_rows:
        best_score = seed_score
        best_rows = seed_rows
    deadline = time.monotonic() + seconds
    all_mask = (1 << TASK_COUNT) - 1
    nodes = 0
    timed_out = False
    stack: list[Row] = []
    memo: dict[tuple[int, int], float] = {}
    min_unit = []
    for idx in range(TASK_COUNT):
        values = [PENALTY]
        values.extend(item[2].cost / len(item[2].tasks) for item in by_task[idx])
        min_unit.append(min(values))

    def lower_bound(decided: int, score: float) -> float:
        rem = all_mask ^ decided
        bound = score
        while rem:
            bit = rem & -rem
            idx = bit.bit_length() - 1
            bound += min_unit[idx]
            rem ^= bit
        return bound

    def choose(decided: int, couriers: int) -> tuple[int | None, list[tuple[int, int, Row]]]:
        rem = all_mask ^ decided
        best_idx = None
        best_options: list[tuple[int, int, Row]] | None = None
        while rem:
            bit = rem & -rem
            idx = bit.bit_length() - 1
            options = [item for item in by_task[idx] if not (item[0] & decided) and not (item[1] & couriers)]
            if best_options is None or len(options) < len(best_options):
                best_idx = idx
                best_options = options
                if not options:
                    break
            rem ^= bit
        return best_idx, best_options or []

    def dfs(decided: int, couriers: int, score: float) -> None:
        nonlocal best_score, best_rows, nodes, timed_out
        nodes += 1
        if nodes & 4095 == 0 and time.monotonic() > deadline:
            timed_out = True
            return
        if score >= best_score - 1e-9:
            return
        if lower_bound(decided, score) >= best_score - 1e-9:
            return
        state = (decided, couriers)
        old = memo.get(state)
        if old is not None and old <= score + 1e-9:
            return
        memo[state] = score
        if decided == all_mask:
            best_score = score
            best_rows = list(stack)
            return
        idx, options = choose(decided, couriers)
        if idx is None:
            best_score = score
            best_rows = list(stack)
            return
        for tm, cm, row in options:
            if timed_out:
                return
            stack.append(row)
            dfs(decided | tm, couriers | cm, score + row.cost)
            stack.pop()
        dfs(decided | (1 << idx), couriers, score + PENALTY)

    dfs(0, 0, 0.0)
    return best_score, sorted(best_rows, key=lambda row: row.task_key), nodes, timed_out


def validate(rows: Sequence[Row]) -> tuple[int, int, int]:
    tasks = set()
    couriers = set()
    dup_tasks = 0
    dup_couriers = 0
    for row in rows:
        for task in row.tasks:
            dup_tasks += task in tasks
            tasks.add(task)
        for courier in row.couriers:
            dup_couriers += courier in couriers
            couriers.add(courier)
    return len(tasks), dup_tasks, dup_couriers


def best_valid_case_rows(cases: Sequence[tuple[str, dict]]) -> tuple[float | None, list[Row]]:
    best_total = None
    best_rows: list[Row] = []
    for path, case in cases:
        if not bool(case.get("validity", True)) or case.get("total_score") is None:
            continue
        total = float(case["total_score"])
        if best_total is not None and total >= best_total - 1e-9:
            continue
        rows = []
        for detail in case.get("detail", []) or []:
            if not isinstance(detail, dict) or "cost" not in detail:
                continue
            task_key = str(detail.get("task_id_list") or "").strip()
            tasks = norm_tasks(task_key)
            couriers = norm_couriers(detail.get("couriers"))
            if task_key and tasks and couriers and all(task in TASK_INDEX for task in tasks):
                rows.append(Row(task_key, tasks, couriers, float(detail["cost"]), path, total))
        best_total = total
        best_rows = rows
    return best_total, sorted(best_rows, key=lambda row: row.task_key)


def write_report(path: Path, cases: Sequence[tuple[str, dict]], all_rows: Sequence[Row], rows: Sequence[Row], score: float, solution: Sequence[Row], nodes: int, timed_out: bool, best_valid: float | None) -> None:
    covered, dup_tasks, dup_couriers = validate(solution)
    lines = [
        "# low_willingness_seed501 Official Column Search",
        "",
        "## Summary",
        "",
        f"- Official low cases scanned: `{len(cases)}`",
        f"- Detail rows scanned: `{len(all_rows)}`",
        f"- Valid unique rows used: `{len(rows)}`",
        f"- Best valid official total observed: `{best_valid}`",
        f"- Best recombined score from observed rows: `{score:.4f}`",
        f"- Search nodes: `{nodes}`",
        f"- Timed out: `{timed_out}`",
        f"- Solution groups: `{len(solution)}`",
        f"- Covered tasks: `{covered}/{TASK_COUNT}`",
        f"- Duplicate tasks: `{dup_tasks}`",
        f"- Duplicate couriers: `{dup_couriers}`",
        "",
        "## Selected Rows",
        "",
    ]
    for row in solution:
        lines.append(f"- `{row.task_key}` -> `{','.join(row.couriers)}` cost `{row.cost:.4f}` from `{Path(row.source).name}`")
    path.write_text("\n".join(lines) + "\n")


def self_test() -> None:
    rows = [
        Row("T0000", ("T0000",), ("C000",), 60.0, "a", 0.0),
        Row("T0001", ("T0001",), ("C001",), 60.0, "a", 0.0),
        Row("T0000,T0001", ("T0000", "T0001"), ("C002",), 90.0, "a", 0.0),
        Row("T0002", ("T0002",), ("C000",), 1.0, "a", 0.0),
    ]
    score, solution, _nodes, _timed = solve_set_packing(rows, per_task_limit=10, seconds=2.0)
    assert abs(score - 2791.0) < 1e-9, (score, solution)
    covered, dup_tasks, dup_couriers = validate(solution)
    assert (covered, dup_tasks, dup_couriers) == (3, 0, 0), (covered, dup_tasks, dup_couriers)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seconds", type=float, default=20.0)
    parser.add_argument("--per-task-limit", type=int, default=80)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("patterns", nargs="*", default=["runs/official_submit_*.json", "runs/official_result_*.json", "runs/official_probe_*.json"])
    args = parser.parse_args()
    if args.self_test:
        self_test()
        print("self-test ok")
        return
    cases, all_rows, rows = collect_rows(args.patterns)
    best_valid, best_rows = best_valid_case_rows(cases)
    score, solution, nodes, timed_out = solve_set_packing(rows, args.per_task_limit, args.seconds, best_valid, best_rows)
    write_report(args.report, cases, all_rows, rows, score, solution, nodes, timed_out, best_valid)
    print(f"cases={len(cases)} rows={len(rows)} best_valid={best_valid} recombined={score:.4f} nodes={nodes} timed_out={timed_out}")
    print(f"report={args.report}")


if __name__ == "__main__":
    main()
