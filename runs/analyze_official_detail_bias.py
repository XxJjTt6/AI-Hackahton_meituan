#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from autosolver.competition_audit import group_expected_cost, parse_competition_rows  # noqa: E402


def find_input(case_file: str) -> Path | None:
    data_dir = ROOT / "Fwd_ 【美团AI Hackathon大赛】-【命题四AutoSolver：让AI Agent 自主求解配送分配问题】脱敏数据"
    p = data_dir / case_file
    if p.exists():
        return p
    return None


def main():
    result_path = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "runs/official_submit_20260520_132026_70222083.json"
    data = json.loads(result_path.read_text())
    result = data.get("result", data)
    print("result", result_path, "avg", result.get("avg_score"))
    for case in result.get("case_results", []):
        input_path = find_input(case["case_file"])
        if not input_path:
            continue
        rows, _tasks = parse_competition_rows(input_path.read_text())
        buckets = defaultdict(list)
        total_local = 0.0
        total_official = 0.0
        missing = 0
        for group in case.get("detail", []):
            task_key = group["task_id_list"]
            couriers = group["couriers"]
            group_rows = []
            for courier in couriers:
                row = rows.get((task_key, courier))
                if row is None:
                    missing += 1
                    continue
                group_rows.append(row)
            if not group_rows:
                continue
            local = group_expected_cost(group_rows, len(group_rows[0].task_ids))
            official = float(group.get("cost", group.get("expected_score", 0.0)))
            total_local += local
            total_official += official
            key = (len(group_rows[0].task_ids), len(group_rows))
            buckets[key].append((local, official, task_key, couriers, group.get("p_complete"), group.get("expected_score")))
        print("\n", case["case_file"], "official", case["total_score"], "local_detail_sum", round(total_local, 4), "official_detail_sum", round(total_official, 4), "missing", missing)
        for key, values in sorted(buckets.items()):
            diffs = [official - local for local, official, *_ in values]
            print("  bucket tasks,riders", key, "n", len(values), "avg_diff", round(sum(diffs)/len(diffs), 4), "min", round(min(diffs), 4), "max", round(max(diffs), 4))
        worst = []
        for values in buckets.values():
            worst.extend(values)
        worst.sort(key=lambda item: abs(item[1] - item[0]), reverse=True)
        for local, official, task_key, couriers, p_complete, cost in worst[:5]:
            print("    drift", task_key, couriers, "local", round(local, 4), "official", official, "diff", round(official-local, 4), "p", p_complete, "expected_score", cost)


if __name__ == "__main__":
    main()
