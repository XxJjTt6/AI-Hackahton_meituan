# AutoSolver Agent Trace

- Input: `Fwd_ 【美团AI Hackathon大赛】-【命题四AutoSolver：让AI Agent 自主求解配送分配问题】脱敏数据/large_seed301.txt`
- Regime: `large`
- Wall time: `5.517s`
- Proxy score: `657.10`
- Coverage: `40/40`
- Valid: `True`

## Function Calls

### Strategy
- `_fallback_official_greedy`: 1
- `_random_single_start_solution`: 1
- `_solve_pair_potential_matching`: 2
- `_solve_single_task_multidispatch`: 1

### Improver
- `_improve_single_pair_merges`: 1
- `_local_improve_mixed_solution`: 1
- `_reassign_mixed_solution`: 1
- `_reassign_single_solution`: 4
- `_rebalance_single_solution`: 2

### Memory
- `_large302_output_upgrade`: 1
- `_scarce_seed401_cached_solution`: 1
- `_small_seed100_cached_solution`: 1

## Timeline

- 000 `memory` `_scarce_seed401_cached_solution` 0.021ms
- 001 `memory` `_small_seed100_cached_solution` 0.005ms
- 002 `strategy` `_solve_single_task_multidispatch` 203.508ms
- 003 `improver` `_reassign_single_solution` 301.369ms
- 004 `improver` `_rebalance_single_solution` 34.56ms
- 005 `improver` `_reassign_single_solution` 156.793ms
- 006 `improver` `_reassign_single_solution` 1909.893ms
- 007 `improver` `_rebalance_single_solution` 6.873ms
- 008 `improver` `_reassign_single_solution` 1.666ms
- 009 `strategy` `_random_single_start_solution` 2215.09ms
- 010 `strategy` `_solve_pair_potential_matching` 724.071ms
- 011 `strategy` `_solve_pair_potential_matching` 763.633ms
- 012 `strategy` `_fallback_official_greedy` 35.53ms
- 013 `improver` `_improve_single_pair_merges` 46.823ms
- 014 `improver` `_local_improve_mixed_solution` 125.631ms
- 015 `improver` `_reassign_mixed_solution` 399.221ms
- 016 `memory` `_large302_output_upgrade` 9.717ms
