# FOR_AutoSolver

美团 AI Hackathon 命题四 `AutoSolver` 求解器仓库。当前仓库以 `solver.py` 为唯一正式提交物，其余模块用于本地验证、脱敏数据评估、实验编排与复盘。

## 最新正式成绩

当前最优官方评测结果：

| Case | Score | Coverage | Runtime |
|---|---:|---:|---:|
| `high_noise_seed601` | 490.05 | 30/30 | 6707ms |
| `large_seed301` | 654.29 | 40/40 | 6168ms |
| `large_seed302` | 627.27 | 40/40 | 7218ms |
| `low_willingness_seed501` | 1803.24 | 30/30 | 9337ms |
| `medium_seed201` | 478.31 | 30/30 | 6932ms |
| `medium_seed202` | 524.72 | 30/30 | 6642ms |
| `medium_seed203` | 502.27 | 30/30 | 6822ms |
| `scarce_couriers_seed401` | 1531.53 | 39/40 | 8759ms |
| `small_seed100` | 304.38 | 15/15 | 3417ms |
| `tiny_seed42` | 154.42 | 6/6 | 773ms |
| **Average** | **707.05** | **10/10** | - |

当前大头瓶颈仍然是：

- `low_willingness_seed501 = 1803.24`
- `scarce_couriers_seed401 = 1531.53`

## 当前生产提交

当前仓库里的 `solver.py` 就是已验证的稳定生产版，并且与 `/tmp/current_best_submission/solver.py` 完全一致。

```text
sha256: 60bfdc441f2b4b1f9278cc9b3d4a2cf2ba88d6d1db43a03bd91d3e67dc08bdf8
size: 65646 bytes
format: v6-compatible output
```

约束状态：

- 提交包大小低于 `80KB`
- 正式版未开启 probe 开关
- 线上输出格式保持与 `solver_variants_v6` 兼容

## 本地验证基线

当前稳定版最近一次完整本地审计结果来自：

```text
/tmp/current_audit_hard_shadow_selector_full.json
```

关键结论：

- `81` 个单元测试全部通过
- `large_seed301 expected_cost = 657.1040208060375`
- `proxy mean = 675.4536886467943`
- `scarce proxy mean = 1245.0108432112506`
- `low proxy mean = 1587.7874834478007`

这说明当前版本在脱敏数据与代理评估上是稳定可复现的，但距离最终 `400` 目标仍有明显差距。

## 当前算法概要

当前生产版 `solver.py` 不是单一贪心，而是一个按场景路由的混合求解器，重点围绕 `401` 和 `501` 做了专门处理：

- `tiny` 场景：小规模精确/近精确搜索
- `normal / medium / large`：多派单贪心 + 重分配 + 局部改良
- `scarce` 场景：hard-scarce shadow selector + bundle MCF + insertion repair
- `low_willingness` 场景：稳健评分选择 + 多候选修复

当前稳定线保留了被验证有效的 scarce 专项增强，去掉了多轮实验后证明不稳或整体退化的分支。

## 仓库结构

```text
FOR_AutoSolver/
├── solver.py                    # 正式提交文件
├── solution.py                  # 兼容导出入口
├── example_solver.py            # 最小调用示例
├── README.md                    # 当前说明
├── 比赛复盘.md                   # 详细过程记录
├── 要点.md                      # 赛题要点整理
├── autosolver/                  # 本地实验与验证工具
├── probes/                      # 官方反馈与 probe 数据
├── tests/                       # 单元测试
└── solver_variants_v*/          # 历史版本参考
```

说明：

- 比赛真正上传的只有 `solver.py`
- `autosolver/` 主要用于离线审计、代理评估、probe 管理和实验
- `solver_variants_v6/` 主要作为输出格式与历史稳定行为参考

## 快速使用

直接调用 `solver.solve`：

```python
from pathlib import Path
from solver import solve

input_text = Path("your_case.txt").read_text()
result = solve(input_text)
print(result)
```

运行测试：

```bash
python3 -m unittest discover -s tests -p 'test_*.py'
```

运行提交审计：

```bash
python3 -m autosolver.submission_audit \
  --solver solver:solve \
  --large-input 'Fwd_ 【美团AI Hackathon大赛】-【命题四AutoSolver：让AI Agent 自主求解配送分配问题】脱敏数据/large_seed301.txt' \
  --proxy-seed 0 \
  --proxy-case scarce \
  --proxy-case medium_anomaly
```

## 后续优化重点

后续不再做版本堆叠，默认只维护一条主生产线，优化重点放在高权重瓶颈：

1. `scarce_couriers_seed401`：继续做 scarce 专项结构优化，重点看 coverage 与 score 的真实 trade-off，而不是只盯 `39/40`
2. `low_willingness_seed501`：继续做稳健打分与分配结构创新，避免对脱敏数据过拟合
3. `large / medium`：控制运行时间，避免为局部提分引入超时风险
4. 新策略先走本地审计，再决定是否进入正式提交

## 备注

当前 `main` 分支目标是保存“最新稳定可提交版本”，不是保留所有试验分支。若要继续冲击 `400`，建议在现有生产线之上做更强的结构性优化，而不是简单堆叠更多小修补。
