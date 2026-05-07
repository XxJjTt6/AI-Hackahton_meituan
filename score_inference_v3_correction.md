# v3 修正说明

v2 判断错误点：

- 我把 `scarce` 当成“覆盖数绝对优先”，但你的截图反证了这一点：
  - 旧版：`scarce_couriers_seed401 = 1588.76`，完成 `38/40`
  - v2：`scarce_couriers_seed401 = 1971.93`，完成 `40/40`
- 这说明后台评分不是字典序先最大化完成数；很差的覆盖会比少覆盖更糟。不能强制 40/40。

新的结论：

- `large_seed301` 本地 avg-subset 模型约 `657.8`，后台约 `655.33`，主模型是对的。
- `scarce` 应该仍按期望分择优，只能让 beam 多探索，不能强制覆盖优先。
- `low_willingness` 的坏分不是简单合单能修复，v2_2 也说明强制合单没有命中 hidden 分布。

v3 改动：

- 回滚 v2 的覆盖优先逻辑。
- 保留 715 版本作为安全底座。
- 只放宽 sparse beam 触发范围，且 beam 结果必须本地期望分更优才会被选。
- 增加一个低意愿随机候选，但同样不强制，仍由期望分择优。

提交建议：

1. `solver_variants_v3/solver_v3_1_cautious_beam.py`
2. 如果还差，提交 `solver_variants_v3/solver_v3_2_rollback_715.py` 保底回滚。
3. 不建议再提交 v2 系列。
