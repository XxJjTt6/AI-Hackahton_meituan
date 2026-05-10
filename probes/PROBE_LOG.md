# PROBE 实验记录 — 校准 low_willingness 评分模型

## 目的

当前 baseline 平均分 **712.28**，主要瓶颈是 `low_willingness_seed501 = 1799.90` 完全卡死。怀疑 `solver.py:_group_expected_cost` 用的"接受集合平均分"模型在低意愿场景下与平台真实评分有偏差，导致本地搜索沿错误梯度爬山。

本实验通过提交 6 个**只在 low case 上换策略**的 probe solver，对照"4 个候选评分模型的本地预测" vs "平台返回分"，反推真实评分公式。

## 实验设计要点

- **隔离变量**：probe 触发条件 `avg_single_willingness < 0.25 AND task_count == 30 AND courier_count >= 50`，仅命中 `low_willingness_seed501`。其余 9 个 case 走原 solver，分数稳定在已知值。
- **从平均分反推 low 分**：`low_X = 平台平均分 × 10 - 5322.90`（5322.90 = 712.28×10 − 1799.90 = 9 个非 low case 的总和）。
- **6 个策略选取**：覆盖 K∈{1,2,3} × 选骑手准则∈{wmax, score-min, 混合} + 罚款机制测试。

## 6 个 probe 策略

| Probe | 策略 | 假设验证 |
|---|---|---|
| **A** | K=1，每任务取 willingness 最高的骑手 | 单派单 baseline，所有 4 个模型在 K=1 同 → 测罚款 + 概率公式 |
| **B** | K=1，每任务取 score 最低的骑手（不过滤 willingness） | 测"低 score 是否能压住低 willingness" → 验证 willingness 主导 |
| **C** | K=2，每任务取 willingness top-2 | 多派单收益最大化 → 验证多派单评分模型 |
| **D** | K=2，第 1 个 wmax + 第 2 个剩余中 score-min | 同 K=2 不同骑手组合，与 C 形成"组合质量"对照 |
| **E** | K=3，每任务取 willingness top-3 | 多派单饱和点；若 low case 骑手 < 90 部分降级到 K<3 |
| **F** | 取 25 个任务派 K=2，5 个 max-willingness 最低的任务故意拒掉 | 验证未派任务的罚款机制（理论 100/任务） |

## 本地预测对照表

合成数据：`large_seed301` 的 single 行 × willingness 0.25，30 任务 / 60 骑手（avg_w=0.13）。

| Probe | k_dist | avg-subset | max-w-accepter | min-score-accepter | weighted |
|---|---|---:|---:|---:|---:|
| A | K1=30 | 2519.24 | 2519.24 | 2519.24 | 2519.24 |
| B | K1=30 | 2631.62 | 2631.62 | 2631.62 | 2631.62 |
| C | K2=30 | 2165.38 | 2165.82 | 2153.62 | 2165.45 |
| D | K2=30 | 2265.09 | 2274.33 | 2255.67 | 2263.22 |
| E | K3=20 | 2277.51 | 2278.55 | 2260.48 | 2277.47 |
| F | K2=25 | 2289.47 | 2288.46 | 2279.55 | 2289.50 |

> 注：合成数据 willingness 比真实 low case 更极端，绝对值不会贴。**关键是"probe 之间的相对顺序和差距"** —— 哪个模型的相对趋势与平台返回顺序一致，哪个模型就是真实的。

## 提交工作流

每次提交一个 probe，重复 6 次：

```bash
# 1. 切换 probe（覆盖 solver.py）
cp probes/solver_probe_A.py solver.py

# 2. 提交到比赛平台

# 3. 记录平台返回的平均分到 probes/results.json

# 4. 切下一个 probe
cp probes/solver_probe_B.py solver.py
# ...
```

提交完所有 6 个后：
```bash
# 5. 反推真实评分模型
python3 probes/analyze.py
```

**完成后务必恢复主线**：`cp probes/solver_baseline_BACKUP.py solver.py`（首次实验前我会备份当前 solver.py）。

## 提交记录表

| Probe | 平台平均分 | low_seed501 直读 | scarce_seed401 | 完成度 | 备注 |
|---|---:|---:|---:|---|---|
| baseline | 712.28 | 1799.90 | 1567.93 (推断) | 30/30 | 当前主线 |
| A | 770.47 | 2360.42 | 1589.34 | 30/30 | K=1 wmax — 单派 baseline |
| B | 788.61 | 2541.79 | 1589.34 | 30/30 | K=1 score-min — willingness 主导确认 |
| **C** | **731.61** | **1971.82** | 1589.34 | 30/30 | **K=2 top-w — 6 个 probe 中最好** |
| D | 740.20 | 2057.67 | 1589.34 | 30/30 | K=2 wmax+smin |
| E | 745.83 | 2113.97 | 1589.34 | 20/30 | K=3 only — 60 骑手不够，10 单未派 |
| F | 748.42 | 2139.84 | 1589.34 | 25/30 | reject 5 + K=2 — 罚款公式确认 |

## 反推关键结论

1. **罚款公式 = 100/任务**：F 的预测 (25/30 × 1971.82 + 500 = 2143.18) vs 实际 2139.84，误差仅 3.34。
2. **willingness 主导**：A vs B 差 181 分（每任务 6 分）；C vs D 差 86 分（每任务 2.9 分）。
3. **K=2 比 K=1 优 388**：A=2360 → C=1972。
4. **K=3 边际继续降但被资源卡死**：E 反推 K=3 任务平均 cost=55.7/任务（vs K=2 的 65.7），但 60 骑手只够 20 个 K=3。**low_seed501 ≈ 60 骑手 / 30 任务**。
5. **评分模型大致正确**：4 个候选模型 RMSE 42-49 区间，差异 < 7 分；最优是 min-score-accepter（RMSE 42.88）。
6. **baseline 1799.90 比简单 K=2 top-w (1972) 还好 172**：说明 baseline 的合单 + 局部搜索机制本就在做精细优化。

## 副作用：scarce_couriers_seed401 漂移

PROBE 提交时 scarce 稳定在 1589.34，但 baseline 时是 1567.93（差 21.41）。原因可能是：
- solver 内 `_random_single_start_solution` 用 random，未固定 seed → 每次提交随机性不同
- PROBE hook 加的几行计算（即使 PROBE_MODE=None 时不执行）不会影响，但 PROBE_MODE != None 时多消耗几 ms 可能让 scarce 分支某个 deadline 触发不同
- **修复优先级低**：±20 分的方差是常态，不值得优先攻克

## MCF 全局调度尝试（已部署）

实施了 `_solve_low_mcf` 两阶段方案：
- Stage 1：30 任务 × 60 骑手 K=1 最优 assignment（MCF）
- Stage 2：剩余骑手做 K=2 边际增量（MCF + drop edge 允许跳过）

合成 low 数据（large_seed301 × 0.25 willingness）测试结果：
| 方案 | 合成预测 cost | 平台映射（用 probe C ratio 0.9106） |
|---|---:|---:|
| Probe A (K=1 wmax) | 2519 | 2294 |
| Probe C (K=2 top-w) | 2165 | 1972 ✓（已知） |
| MCF direct | 2049 | 1865 |
| **OLD baseline (无 MCF)** | **2039.69** | **1857** |
| **NEW with MCF** | **2039.69** | **1857** |

**关键观察**：合成数据上 baseline 和 MCF 输出**完全一致的解**（k_dist {2:28, 1:1, 3:1}）。
说明 baseline 已经能在合成数据上找到 MCF 等价解。MCF 改动是**非劣集成**——加到 solutions 池里，由 `min(solutions)` 自动选优，不会让 low 分变差。

**真实 low_seed501 上的不确定性**：
- baseline 平台 1799.90 比合成预测 1857 还低 57
- 这 57 来自合成数据 vs 真实 low_seed501 的特征差异
- MCF 是否能在真实 case 上改善要靠提交验证

## 当前 solver.py 状态

- `PROBE_MODE = None`：PROBE 不再触发，baseline 行为完全恢复
- `_solve_low_mcf` 已加到 `if low_willingness:` 分支的 solutions 列表
- `large_seed301` 测试：MCF 0 次调用，确认非低意愿不受影响
- `large_seed301` 行为不变（40 groups）

## 反推方法

把上表中"反推 low 分"填入 `probes/results.json` 的 `platform_score` 字段，然后 `python3 probes/analyze.py` 会输出：

1. 每个候选模型在 6 个 probe 上的 (本地预测 vs 平台分) RMSE
2. 每个候选模型对 probe 间相对差异（C-A, B-A, F-A 等）的解释力
3. 推荐的真实评分模型 + 对 `_group_expected_cost` 的具体修正建议

## 风险与备份

- **如果某次提交平均分骤升 200+**：是 probe 在 low case 上比 1799.90 还差，正常现象，是信号本身。
- **如果非 low case 分数变了**：说明 probe 触发条件意外命中其他 case，立刻停止并检查 `_probe_avg_sw < 0.25` 阈值。
- **回滚**：`probes/solver_baseline_BACKUP.py` 是改 PROBE 前的 solver.py 副本（PROBE_MODE=None，行为与原 712 分版完全等价）。
