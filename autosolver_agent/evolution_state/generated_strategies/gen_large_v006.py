# Auto-generated experimental strategy: gen_large_v006
from __future__ import annotations


def propose(candidates, all_tasks, deadline, helpers):
    """Return a safe greedy baseline candidate for sandbox evaluation."""
    fallback = helpers.get("fallback_greedy")
    if fallback is not None:
        return fallback(candidates)
    used_couriers = set()
    covered_tasks = set()
    result = []
    for task_key, task_ids, courier_id, _score, _willingness, _row_index in sorted(candidates, key=lambda row: row[3]):
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
