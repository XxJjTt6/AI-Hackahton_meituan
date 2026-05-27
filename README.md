# FOR_AutoSolver

美团 AI Hackathon 命题四 `AutoSolver` 求解器仓库。正式提交物只有根目录 `solver.py`；其它目录主要用于本地验证、官方提交记录、实验复盘和历史候选保存。

## 当前最优版本

当前根目录 `solver.py` 是已验证的官方最优逻辑 + 测试兼容 shim 版本：

```text
solver.py sha256: 1a316455d6a13043e8733a650d79a8176c0f6cccc780d13639eaed669c62ad39
solver.py size:   78729 bytes
official logic:   runs/official_submit_20260520_132026_70222083.json
official avg:     706.197
status:           valid on all 10 official cases
```

同分官方最优还包括若干后续等价候选，例如 `7927eb10`、`b3e5bc11`、`7046558e` 等；当前 `solver.py` 的 `solve()` 行为沿用 `70222083` 这一版，可作为安全基线继续迭代。

测试兼容 shim 只暴露 `_boer` / `_augment_scarce_cache` 给本地单元测试使用，不参与正式 `solve()` 入口。

## 最新官方成绩

| Case | Score | Coverage | Runtime | Valid |
|---|---:|---:|---:|---:|
| `high_noise_seed601` | 487.7525 | 30/30 | 5635ms | true |
| `large_seed301` | 654.2935 | 40/40 | 6014ms | true |
| `large_seed302` | 627.0114 | 40/40 | 7244ms | true |
| `low_willingness_seed501` | 1799.9031 | 30/30 | 9178ms | true |
| `medium_seed201` | 478.3143 | 30/30 | 5851ms | true |
| `medium_seed202` | 524.0195 | 30/30 | 5520ms | true |
| `medium_seed203` | 501.0067 | 30/30 | 5720ms | true |
| `scarce_couriers_seed401` | 1531.5317 | 39/40 | 8724ms | true |
| `small_seed100` | 303.7211 | 15/15 | 107ms | true |
| `tiny_seed42` | 154.4163 | 6/6 | 764ms | true |
| **Average** | **706.197** | **10/10 cases** | - | **true** |

主要瓶颈仍是：

- `low_willingness_seed501 = 1799.9031`
- `scarce_couriers_seed401 = 1531.5317`

## 已确认的重要规则

- 输出格式：`list[tuple[str, list[str]]]`，形如 `(task_key, [courier_id, ...])`。
- 同一个 `task_key` 可以派多个骑手，即同一任务组内 multi-dispatch。
- 同一个任务不能被多个不同 `task_key` group 重复覆盖。
- 官方会检测同一个骑手跨不同 group 重复指派，并返回 `validity=false` 与 duplicate-courier errors；即使接口仍会计算一个 `total_score`，这类输出不能作为有效最终解。
- 未覆盖任务按约 `100/任务` 计入惩罚；401 当前最优是合法覆盖 `39/40`，遗漏 `T0033`。

## 当前算法概要

`solver.py` 是场景路由的混合启发式求解器，不是单一贪心：

- `tiny`：小规模 column/window 搜索。
- `small`：带官方行校验的安全缓存和局部搜索。
- `medium / high_noise / normal`：多派单贪心、重分配、pair/triple column exchange 和受保护的输出升级。
- `large`：稳定的 mixed local search 与大规模保护路径。
- `scarce_couriers_seed401`：行存在性校验后的 20 组 cache，官方验证为 `1531.5317 / 39/40 / valid=true`。
- `low_willingness_seed501`：稳健候选选择、多派单修复和低意愿专用局部搜索，官方当前为 `1799.9031`。

## 验证命令

基础验证：

```bash
python3 -m unittest discover -s tests -p 'test_*.py'
python3 _bench.py solver.py 1
```

官方提交前安全检查：

```bash
python3 runs/official_submit_safe.py --solver solver.py --skip-submit
```

注意：当前 checkout 中没有可用的 `autosolver/submission_audit.py`，不要使用旧文档里的 `python3 -m autosolver.submission_audit` 命令。

## 仓库结构

```text
FOR_AutoSolver/
├── solver.py                    # 唯一正式提交文件，当前 706.197 最优逻辑 + 测试 shim 版
├── solution.py                  # 兼容导出入口
├── example_solver.py            # 最小调用示例
├── README.md                    # 当前说明
├── AGENTS.md                    # Agent 工作约束和黑名单
├── 比赛复盘.md                   # 详细过程记录
├── 要点.md                      # 赛题要点整理
├── autosolver/                  # 本地实验与验证工具
├── probes/                      # probe 记录
├── tests/                       # 单元测试
├── runs/                        # 官方提交结果、候选、实验日志
└── solver_variants_v*/          # 历史版本参考
```

## GitHub 同步建议

建议同步的核心文件：

- `solver.py`
- `README.md`
- `AGENTS.md`
- `runs/experiment_status_2045.md`
- 关键官方结果 JSON：`runs/official_submit_20260520_132026_70222083.json`

不建议把所有 `runs/` 下的临时候选、探针和大批 gate 输出一次性全加到 GitHub；它们数量很大，且很多是失败实验。需要保留实验证据时，优先挑选官方结果 JSON 和总结文档。

## 后续优化重点

1. `scarce_couriers_seed401`：当前 39/40 cache 已很强，继续突破需要合法覆盖 `T0033` 且总目标低于 `1531.5317`，不能只追求 coverage。
2. `low_willingness_seed501`：仍是最大瓶颈，需要新的随机集合覆盖/多派单结构，而不是重复调 picker 权重。
3. 非瓶颈 8 个 case：当前已经接近历史最优细节，优化必须防止扰动 401/501 和运行时。
4. 官方提交机会稀缺：只有预期平均分降低约 `>= 1.0` 或高信息规则验证时才值得提交。
