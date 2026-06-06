# Auto-generated experimental strategy: gen_large_v012
# target_regime: large
from __future__ import annotations


def propose(candidates, all_tasks, deadline, helpers):
    """Return a regime-aware experimental candidate for sandbox evaluation."""
    time_left = helpers.get("time_left")
    used_couriers = set()
    covered_tasks = set()
    result = []
    rows = sorted(candidates, key=lambda row: (len(row[1]), row[3] / max(row[4], 0.001), row[3]))
    for task_key, task_ids, courier_id, _score, _willingness, _row_index in rows:
        if time_left is not None and time_left(deadline) <= 0.01:
            break
        if courier_id in used_couriers:
            continue
        if any(task_id in covered_tasks for task_id in task_ids):
            continue
        used_couriers.add(courier_id)
        covered_tasks.update(task_ids)
        result.append((task_key, [courier_id]))
        if covered_tasks >= set(all_tasks):
            break
    return result
