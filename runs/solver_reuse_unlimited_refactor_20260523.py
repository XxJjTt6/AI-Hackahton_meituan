import time

PENALTY = 100.0


def solve(input_text: str):
    deadline = time.monotonic() + 8.8
    rows, tasks = parse_rows(input_text)
    if not rows:
        return []
    columns = build_columns(rows, tasks, deadline)
    selected = select_disjoint_task_groups(columns, len(tasks), deadline)
    return [(col["task_key"], list(col["couriers"])) for col in sorted(selected, key=lambda c: c["task_key"])]


def parse_rows(text):
    lines = text.strip().splitlines()
    start = 1 if lines and lines[0].startswith("task_id_list") else 0
    rows = []
    task_set = set()
    for row_index, line in enumerate(lines[start:]):
        parts = line.strip().split("\t")
        if len(parts) < 4:
            continue
        task_key, courier, score, willingness = parts[:4]
        task_ids = tuple(t.strip() for t in task_key.split(",") if t.strip())
        if not task_ids or not courier:
            continue
        try:
            row = {
                "task_key": task_key.strip(),
                "task_ids": task_ids,
                "courier": courier.strip(),
                "score": float(score),
                "willingness": float(willingness),
                "row_index": row_index,
            }
        except ValueError:
            continue
        rows.append(row)
        task_set.update(task_ids)
    return rows, sorted(task_set)


def group_expected_cost(group, task_count):
    if not group:
        return PENALTY * task_count
    expected = 0.0
    size = len(group)
    if size <= 12:
        for mask in range(1 << size):
            prob = 1.0
            score = 0.0
            accepted = 0
            for index, row in enumerate(group):
                if mask & (1 << index):
                    prob *= row["willingness"]
                    score += row["score"]
                    accepted += 1
                else:
                    prob *= 1.0 - row["willingness"]
            expected += prob * (score / accepted if accepted else PENALTY * task_count)
        return expected
    none_prob = 1.0
    weighted = 0.0
    accept_prob = 0.0
    for row in group:
        none_prob *= 1.0 - row["willingness"]
        weighted += row["willingness"] * row["score"]
        accept_prob += row["willingness"]
    return none_prob * PENALTY * task_count + (1.0 - none_prob) * weighted / max(accept_prob, 1e-9)


def build_columns(rows, tasks, deadline):
    task_index = {task: index for index, task in enumerate(tasks)}
    by_key = {}
    for row in rows:
        mask = 0
        valid = True
        for task_id in row["task_ids"]:
            if task_id not in task_index:
                valid = False
                break
            mask |= 1 << task_index[task_id]
        if valid:
            by_key.setdefault(row["task_key"], []).append((mask, row))

    columns = []
    for task_key, items in by_key.items():
        if time.monotonic() > deadline - 0.1:
            break
        mask = items[0][0]
        task_count = len(items[0][1]["task_ids"])
        pool = [row for _, row in sorted(items, key=lambda item: (item[1]["score"], -item[1]["willingness"], item[1]["row_index"]))[:18]]
        group = best_reusable_group(pool, task_count, max_riders=6 if task_count == 1 else 4)
        if not group:
            continue
        cost = group_expected_cost(group, task_count)
        gain = PENALTY * task_count - cost
        if gain > 1e-9:
            columns.append({
                "task_key": task_key,
                "mask": mask,
                "task_count": task_count,
                "couriers": tuple(row["courier"] for row in group),
                "cost": cost,
                "gain": gain,
            })
    return columns


def best_reusable_group(pool, task_count, max_riders):
    group = []
    used_inside_group = set()
    current = PENALTY * task_count
    while len(group) < max_riders:
        best_row = None
        best_cost = current
        for row in pool:
            if row["courier"] in used_inside_group:
                continue
            cost = group_expected_cost(group + [row], task_count)
            if cost < best_cost - 1e-12:
                best_cost = cost
                best_row = row
        if best_row is None:
            break
        group.append(best_row)
        used_inside_group.add(best_row["courier"])
        current = best_cost
    return group


def select_disjoint_task_groups(columns, task_count, deadline):
    singles = {}
    for col in columns:
        if col["task_count"] == 1:
            bit = col["mask"]
            if bit not in singles or col["gain"] > singles[bit]["gain"]:
                singles[bit] = col
    selected = list(singles.values())
    selected_by_mask = {col["mask"]: col for col in selected}
    covered = 0
    for col in selected:
        covered |= col["mask"]

    candidates = sorted(columns, key=lambda col: (col["gain"] / col["task_count"], col["gain"]), reverse=True)
    changed = True
    while changed and time.monotonic() < deadline - 0.1:
        changed = False
        best_delta = 0.0
        best_move = None
        for col in candidates:
            overlapping = [old for old in selected if old["mask"] & col["mask"]]
            outside_overlap = covered & col["mask"]
            for old in overlapping:
                outside_overlap &= ~old["mask"]
            if outside_overlap:
                continue
            old_gain = sum(old["gain"] for old in overlapping)
            delta = col["gain"] - old_gain
            if delta > best_delta + 1e-9:
                best_delta = delta
                best_move = (col, overlapping)
        if best_move:
            col, overlapping = best_move
            for old in overlapping:
                selected.remove(old)
                covered &= ~old["mask"]
                selected_by_mask.pop(old["mask"], None)
            selected.append(col)
            selected_by_mask[col["mask"]] = col
            covered |= col["mask"]
            changed = True
    return selected


def solution_expected_cost_reuse(solution, input_text):
    rows, tasks = parse_rows(input_text)
    row_map = {(row["task_key"], row["courier"]): row for row in rows}
    covered = set()
    total = 0.0
    for task_key, couriers in solution:
        group = []
        used_inside_group = set()
        for courier in couriers:
            row = row_map.get((task_key, courier))
            if row is None or courier in used_inside_group:
                return float("inf")
            group.append(row)
            used_inside_group.add(courier)
        if not group:
            return float("inf")
        for task_id in group[0]["task_ids"]:
            if task_id in covered:
                return float("inf")
            covered.add(task_id)
        total += group_expected_cost(group, len(group[0]["task_ids"]))
    return total + PENALTY * (len(tasks) - len(covered))


def _solution_expected_cost(result, candidates, all_tasks):
    row_map = {(row[0], row[2]): row for row in candidates}
    covered = set()
    total = 0.0
    for task_key, couriers in result:
        group = []
        used_inside_group = set()
        for courier in couriers:
            row = row_map.get((task_key, courier))
            if row is None or courier in used_inside_group:
                return float("inf")
            used_inside_group.add(courier)
            group.append({
                "task_key": row[0],
                "task_ids": tuple(row[1]),
                "courier": row[2],
                "score": row[3],
                "willingness": row[4],
                "row_index": row[5],
            })
        if not group:
            return float("inf")
        for task_id in group[0]["task_ids"]:
            if task_id in covered:
                return float("inf")
            covered.add(task_id)
        total += group_expected_cost(group, len(group[0]["task_ids"]))
    return total + PENALTY * (len(all_tasks) - len(covered))
