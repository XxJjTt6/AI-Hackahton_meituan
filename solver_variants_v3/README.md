# v3 variants

这组是对 v2 失败后的修正。v2 失败原因：把 `scarce` 改成覆盖优先，导致后台从 `1588.76 / 38-40` 变成 `1971.93 / 40-40`，说明后台不是覆盖数绝对优先，坏覆盖会被重罚。

因此 v3 的原则：

- 不再强制覆盖优先。
- 回到 715 分版本的期望分选择逻辑。
- 只做安全增量：放宽 sparse beam 的触发范围，但 beam 结果仍然必须在本地期望分上更低才会被选。
- 低意愿只增加一个随机单任务初解候选，仍由期望分择优，不强制合单。

版本：

1. `solver_v3_1_cautious_beam.py`: 首选。715 底座 + 更宽 sparse beam + 低意愿随机候选。
2. `solver_v3_2_rollback_715.py`: 完全回滚到 715 左右那版，最安全。
3. `solver_v3_3_safe_time.py`: beam 更保守，平台慢时用。
4. `solver_v3_4_wide_beam.py`: beam 更宽，赌 scarce 有收益，耗时风险略高。
5. `solver_v3_5_no_low_random.py`: 不跑低意愿随机候选，只尝试更宽 sparse beam。
