"""Offline experiment: apply EXACT-objective local descent to the solver's
output on synthetic tail cases. Measures the ceiling of exact-objective polish
WITHOUT modifying solver.py. Pure measurement, no submission.
"""
import importlib.util, sys, os, time as _t
sys.path.insert(0, 'runs')
import exact_score as ex

spec = importlib.util.spec_from_file_location('sv', 'solver.py')
sv = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sv)

CD = 'web_agent_demo/generated_cases'


def build_index(txt):
    """(task_key,courier) -> (score, willingness); plus per-task-key courier list."""
    idx = {}
    bykey = {}
    lines = [l for l in txt.replace('\r\n', '\n').split('\n') if l.strip()]
    for line in lines[1:]:
        p = line.split('\t')
        if len(p) < 4:
            continue
        tk, cid, sc, wl = p[0], p[1], p[2], p[3]
        try:
            idx[(tk, cid)] = (float(sc), float(wl))
        except ValueError:
            continue
        bykey.setdefault(tk, []).append(cid)
    return idx, bykey


def exact_group_cost(tk, couriers, idx):
    k = len(tk.split(','))
    rows = [idx[(tk, c)] for c in couriers if (tk, c) in idx]
    return ex.group_cost(rows, k)


def exact_descent(solution, idx, bykey, all_tasks, deadline):
    """Local descent under EXACT cost. Moves: per group, try add/remove/swap one
    courier from the group's own candidate pool, respecting global courier
    uniqueness. Accept strict improvements only. Coverage preserved."""
    sol = {tk: list(cs) for tk, cs in solution}
    used = set()
    for cs in sol.values():
        used.update(cs)
    improved = True
    while improved and _t.monotonic() < deadline:
        improved = False
        for tk in list(sol.keys()):
            cur = sol[tk]
            base = exact_group_cost(tk, cur, idx)
            pool = [c for c in bykey.get(tk, []) if c not in used or c in cur]
            best_delta = -1e-9
            best_new = None
            # try removing one
            for c in cur:
                if len(cur) <= 1:
                    break
                nw = [x for x in cur if x != c]
                d = exact_group_cost(tk, nw, idx) - base
                if d < best_delta:
                    best_delta = d
                    best_new = nw
            # try adding one unused
            for c in pool:
                if c in cur:
                    continue
                nw = cur + [c]
                d = exact_group_cost(tk, nw, idx) - base
                if d < best_delta:
                    best_delta = d
                    best_new = nw
            # try swap one in-group with one pool
            for ci in cur:
                for c in pool:
                    if c in cur:
                        continue
                    nw = [x for x in cur if x != ci] + [c]
                    d = exact_group_cost(tk, nw, idx) - base
                    if d < best_delta:
                        best_delta = d
                        best_new = nw
            if best_new is not None:
                for c in cur:
                    used.discard(c)
                for c in best_new:
                    used.add(c)
                sol[tk] = best_new
                improved = True
            if _t.monotonic() >= deadline:
                break
    return [(tk, cs) for tk, cs in sol.items()]


def main():
    cases = ['scarce_couriers_seed401.txt', 'low_willingness_seed501.txt',
             'small_seed100.txt', 'tiny_seed42.txt', 'medium_seed201.txt',
             'high_noise_seed601.txt', 'medium_seed202.txt', 'medium_seed203.txt',
             'large_seed302.txt']
    tot_b = tot_a = 0.0
    for case in cases:
        txt = open(os.path.join(CD, case)).read()
        idx, bykey = build_index(txt)
        _, tasks = ex.parse_input(txt)
        out = sv.solve(txt)
        b, vb, ib = ex.score_solution(out, idx, tasks)
        polished = exact_descent(out, idx, bykey, tasks, _t.monotonic() + 1.0)
        a, va, ia = ex.score_solution(polished, idx, tasks)
        tot_b += b
        tot_a += a
        flag = '' if va and ia['covered'] >= ib['covered'] else '  <<INVALID/COV-DROP'
        print('%-30s base=%9.2f exact-descent=%9.2f delta=%+8.2f%s' % (
            case, b, a, a - b, flag))
    print('--- total base=%.2f after=%.2f delta=%+.2f ---' % (tot_b, tot_a, tot_a - tot_b))


if __name__ == '__main__':
    main()
