# AutoSolver Agent Trace

- Input: `Fwd_ 【美团AI Hackathon大赛】-【命题四AutoSolver：让AI Agent 自主求解配送分配问题】脱敏数据/large_seed301.txt`
- Regime: `large`
- Wall time: `4.401s`
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

- 000 `memory` `_scarce_seed401_cached_solution` 0.025ms
- 001 `memory` `_small_seed100_cached_solution` 0.007ms
- 002 `strategy` `_solve_single_task_multidispatch` 174.886ms
- 003 `improver` `_reassign_single_solution` 549.346ms
- 004 `improver` `_rebalance_single_solution` 34.246ms
- 005 `improver` `_reassign_single_solution` 151.512ms
- 006 `improver` `_reassign_single_solution` 701.447ms
- 007 `improver` `_rebalance_single_solution` 48.333ms
- 008 `improver` `_reassign_single_solution` 306.739ms
- 009 `strategy` `_random_single_start_solution` 1290.98ms
- 010 `strategy` `_solve_pair_potential_matching` 718.638ms
- 011 `strategy` `_solve_pair_potential_matching` 692.494ms
- 012 `strategy` `_fallback_official_greedy` 17.037ms
- 013 `improver` `_improve_single_pair_merges` 24.571ms
- 014 `improver` `_local_improve_mixed_solution` 69.506ms
- 015 `improver` `_reassign_mixed_solution` 161.658ms
- 016 `memory` `_large302_output_upgrade` 9.009ms
