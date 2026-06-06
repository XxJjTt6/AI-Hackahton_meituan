from pathlib import Path
ROOT=Path('/Users/比赛/FOR_AutoSolver_706.72')
base=(ROOT/'solver.py').read_text()
module=(ROOT/'solver_variants_v7/y1_lagrangian_pricer.py').read_text()
start=module.index('def _cand_atomic_cost')
end=module.index('\n\n# ---------- Local sanity test ----------')
funcs=module[start:end]
funcs=funcs.replace('def _cand_atomic_cost(group_cost_fn, c):', 'def _lag_cand_atomic_cost(group_cost_fn, c):')
funcs=funcs.replace('_cand_atomic_cost(S._group_expected_cost, c)', '_lag_cand_atomic_cost(S._group_expected_cost, c)')
funcs=funcs.replace('def _greedy_assign', 'def _lag_greedy_assign')
funcs=funcs.replace('_greedy_assign(rc_list, all_tasks_set)', '_lag_greedy_assign(rc_list, all_tasks_set)')
funcs=funcs.replace('def _result_from_picked', 'def _lag_result_from_picked')
funcs=funcs.replace('_result_from_picked(picked)', '_lag_result_from_picked(picked)')
funcs=funcs.replace('def lagrangian_columns', 'def _lagrangian_columns')
funcs=funcs.replace('import solver as solver_module', 'solver_module=None')
funcs=funcs.replace('    S = solver_module\n', '    S = globals().get("_SELF_MODULE") or __import__(__name__)\n')
# remove doc import math dependency unnecessary; time already imported in solver.py
funcs='\n# Lagrangian candidate injector (generated from v7 helper)\n_SELF_MODULE=None\n'+funcs+'\n'

def write(name, text):
    p=ROOT/'runs'/f'lag_{name}.py'
    p.write_text(text)
    print(p)

# low-only after low candidate generation, before generic branch
needle="\tif not O or F or AA:\n"
insert="\tif J and time.monotonic()<A-1.05:\n\t\tLG=_lagrangian_columns(C,B,min(A,time.monotonic()+.8),max_iter=18,robust_pick=_B)\n\t\tif LG:E.append(LG)\n"
write('low_only', base.replace(needle, insert+needle, 1)+funcs)
# scarce only before hard-scarce picking stage
needle2="\tE.append(_fallback_official_greedy(C))\n"
insert2="\tif G and time.monotonic()<A-.95:\n\t\tLG=_lagrangian_columns(C,B,min(A,time.monotonic()+.7),max_iter=16,robust_pick=_D)\n\t\tif LG:E.append(LG)\n"
write('scarce_only', base.replace(needle2, insert2+needle2, 1)+funcs)
# low + scarce
write('low_scarce', base.replace(needle, insert+needle, 1).replace(needle2, insert2+needle2, 1)+funcs)
