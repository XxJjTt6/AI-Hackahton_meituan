# v2 variants after score feedback

这组版本基于 715.85 的后台反馈反推：

- `low_willingness_seed501`: 30/30 但 1799.90，说明不是覆盖失败，而是低意愿下多派/合单策略未命中或本地模型选择过保守。
- `scarce_couriers_seed401`: 38/40 且 1588.76，说明稀缺分支有覆盖缺口。原代码在候选行数较大时会跳过 beam，容易停在贪心结果。
- `large_seed301`: 本地 avg-subset 模型约 657.8，后台 655.33，说明主评分模型基本接近，不应改大样例主线。

提交建议：

1. `solver_v2_1_scarce_cover.py`: 首选。稀缺场景覆盖优先，放宽 sparse beam 触发阈值。
2. `solver_v2_2_force_low_bundle.py`: 如果还想赌低意愿，提交这个。更激进地强制低意愿合单。
3. `solver_v2_5_aggressive_scarce.py`: 如果 scarce 仍是最大拖累，提交这个。beam 更宽，有轻微超时风险。
4. `solver_v2_3_safe_beam.py`: 平台机器慢时用，更稳但 scarce 覆盖改善可能弱。
5. `solver_v2_4_no_low_force.py`: 只改 scarce，不赌低意愿合单。
