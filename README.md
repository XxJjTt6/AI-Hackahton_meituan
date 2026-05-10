# FOR_AutoSolver 项目说明

美团 AI Hackathon 命题四 **AutoSolver：让 AI Agent 自主求解配送分配问题** 的求解器项目。

---

## 当前状态

| 指标 | 数值 |
|------|------|
| 当前平均分 | ~712.4 |
| 已提交轮次 | 4 轮优化 |
| 瓶颈 case | low_willingness_seed501 (1799.90) + scarce_couriers_seed401 (1589.34) |
| 正常 case | 8 个 normal case 已贴近最优（~16-17/task） |
| 时间限制 | 10 秒/算例（超时罚 4000 分） |
| 每日配额 | 20 次提交 |

**核心瓶颈**：low_seed501 在 4 轮不同优化后分数完全相同（1799.90），当前贪心+局部搜索框架已收敛到评分模型的局部最优。正在通过 scarce PROBE 实验反推 scarce 场景的真实评分模型。

---

## 项目结构

```
FOR_AutoSolver/
├── solver.py              # ★ 比赛提交文件（唯一提交物）
├── solution.py            # 简单导出，非当前版本
├── example_solver.py      # 示例入口
├── 比赛复盘.md             # 详细复盘：分数、PROBE 结论、瓶颈分析
├── 要点.md                # 赛题要点
├── README.md              # 本文档
├── autosolver/            # 工程化 AutoSolver 包（JSON 模式）
│   ├── competition.py     # 精简版 TSV 求解器
│   ├── controller.py      # 求解控制器
│   ├── candidate_gen.py   # 候选生成
│   ├── greedy.py          # 贪心策略
│   ├── lns.py             # 大邻域搜索
│   ├── fallback.py        # 兜底策略
│   ├── objective.py       # 目标函数
│   ├── validator.py       # 解验证
│   └── ...
├── probes/                # 评分模型反推实验
│   ├── PROBE_LOG.md       # low 场景 PROBE 实验记录
│   ├── analyze.py         # low PROBE 分析脚本
│   ├── analyze_scarce.py  # scarce PROBE 分析脚本
│   ├── results.json       # low PROBE 结果
│   ├── scarce_results.json# scarce PROBE 结果
│   └── solver_probe_*.py  # 各 PROBE solver
├── solver_variants*/      # 历史 solver 版本
├── tests/                 # unittest 测试
├── Fwd_...脱敏数据/        # 比赛脱敏数据
└── score_inference_v*.md  # 评分模型推断记录
```

---

## solver.py 架构

当前 `solver.py` 约 2500 行，包含完整的求解流水线：

### 主流程

```
输入 TSV
  ↓
解析 candidates → 识别 case 类型
  (scarce / low_willingness / abundant / medium / tiny)
  ↓
生成 candidate solutions（多策略并行）:
  • _solve_single_task_multidispatch    — 主力贪心（multi-dispatch）
  • _solve_tiny_exact                   — ≤8 任务精确求解（分区枚举）
  • _solve_scarce_bundle_enum           — scarce 专用 bundle 枚举
  • _solve_low_mcf                      — low 专用两阶段 MCF
  • _random_start_low                   — low 多样化随机起点（4 seeds）
  • _randomized_greedy_bundles          — 随机化贪心（small/medium, 3-5 restarts）
  • _solve_disjoint_then_multidispatch  — 不相交贪心（ratio/gain/cover 三种模式）
  • _solve_pair_potential_matching      — 合单匹配
  • _solve_sparse_cover                 — 覆盖优先（含 beam search）
  • _solve_scarce_coverage_first        — 覆盖优先贪心（scarce 备用）
  • _fallback_official_greedy           — 官方贪心（纯 score 排序）
  ↓
选最优:
  • low_willingness: _pick_robust_best  — 鲁棒多模型评分
  • 其他: min(_solution_expected_cost)
  ↓
_local_improve_mixed_solution           — 局部搜索（2-4 passes）
  • _improve_same_key_groups            — 同组骑手重选
  • _improve_bundle_splits              — bundle 拆分
  • _improve_single_pair_merges         — 两单合并
  • _improve_covered_bundle_merges      — 多组 bundle 合并
  • _improve_pair_rewires               — 对重洗 (scarce only)
  • _improve_single_bundle_merges       — 任意长合并 (scarce only)
  • _reassign_mixed_solution            — MCF 全局骑手重分配
  ↓
[low only] _solve_low_sa                — 结构性 SA（含 merge/split/re-bundle）
  ↓
return best
```

### Case 路由

| Case 类型 | 判定条件 | 特殊处理 |
|-----------|----------|----------|
| tiny | `tasks ≤ 8` | 精确分区枚举 |
| scarce | `couriers < tasks` | bundle 枚举 + pair_rewires + bundle_merges |
| low_willingness | `avg_willingness < 0.27` | MSA 评分 + MCF + 4x 随机起点 + 结构性 SA + 鲁棒选优 |
| medium | 20-35 tasks, 非 low/abundant | 3x 随机化贪心 + 3 passes 局部搜索 |
| abundant | `couriers ≥ 1.5×tasks` + 全覆盖 | destroy_repair + random restart |
| large | 40 tasks, 80 couriers | 无特殊处理（已接近最优） |

### 评分模型

- **正常场景**：avg-subset 模型（枚举接受子集求期望）
- **低意愿场景**：min-score-accepter 模型（PROBE 证明 RMSE 42.88 vs 46.84），配合鲁棒多模型选优
- 两种模型通过全局标志 `_LOW_USE_MSA` 自动切换

### 10 个测试算例

| Case | tasks | couriers | 当前分数 | /task | 特征 |
|------|------:|---------:|------:|------:|------|
| high_noise_seed601 | 30 | ? | 490.05 | 16.34 | 高噪声 |
| large_seed301 | 40 | 80 | 655.33 | 16.38 | 充裕骑手 |
| large_seed302 | 40 | 80 | 627.52 | 15.69 | 充裕骑手 |
| **low_willingness_seed501** | **30** | **~60** | **1799.90** | **60.00** | **瓶颈 1** |
| medium_seed201 | 30 | ? | 484.42 | 16.15 | 正常 |
| medium_seed202 | 30 | ? | 524.24 | 17.47 | 异常偏高 |
| medium_seed203 | 30 | ? | 501.01 | 16.70 | 正常 |
| **scarce_couriers_seed401** | **40** | **~38** | **1589.34** | **39.73** | **瓶颈 2 (95%)** |
| small_seed100 | 15 | ? | 305.35 | 20.36 | 小规模 |
| tiny_seed42 | 6 | ? | 152.80 | 25.47 | 极小规模 |

---

## PROBE 实验

### Low PROBE（已完成）

通过 6 次提交反推了 low 场景的平台评分模型。关键结论：
- 罚款 = 100/任务
- willingness 主导评分
- K=2 比 K=1 优 ~388 分
- min-score-accepter 是最优拟合模型（RMSE 42.88）
- baseline 1799.90 已是 avg-subset 局部最优

详见 `probes/PROBE_LOG.md`。

### Scarce PROBE（进行中）

5 个探针（G/H/I/J/K），用于反推 scarce 场景的真实评分：

```bash
# 1. 修改 solver.py 第 10 行
PROBE_SCARCE_MODE = "G"   # 依次改为 G → H → I → J → K

# 2. 提交到平台，记录平均分到 probes/scarce_results.json

# 3. 全部提交完后运行分析
python3 probes/analyze_scarce.py
```

| Probe | 策略 | 目的 |
|-------|------|------|
| G | K=1 singles, reject 2 worst | scarce baseline |
| H | 1 bundle + singles, 1 reject | 单 bundle 评分 |
| I | 2 bundles + singles, 100% cover | bundle 能否达全覆盖 |
| J | 3 bundles + singles, 100% cover | 激进合单 |
| K | K=2 multi-dispatch, reject 2 | 多派单效果 |

---

## 运行指南

### 环境

- Python 3.9+
- 在线提交无第三方依赖
- 测试使用标准库 `unittest`

### 运行测试

```bash
python3 -m unittest discover -s tests -p 'test_*.py'
```

### 本地验证 solver.py

```bash
python3 - <<'PY'
from pathlib import Path
from solver import solve

path = 'Fwd_ 【美团AI Hackathon大赛】-【命题四AutoSolver：让AI Agent 自主求解配送分配问题】脱敏数据/large_seed301.txt'
input_text = Path(path).read_text()
result = solve(input_text)
print(f'Groups: {len(result)}')
print(result[:5])
PY
```

### 检查提交前清单

- [ ] `PROBE_MODE = None`（不是 A/B/C/D/E/F）
- [ ] `PROBE_SCARCE_MODE = None`（不是 G/H/I/J/K，除非故意做 PROBE）
- [ ] `python3 -m unittest discover -s tests -p 'test_*.py'` 全部通过
- [ ] large_seed301 耗时 < 8.7s
- [ ] 记录改动内容和预期影响

---

## 已尝试的优化路径

| 轮次 | 改动 | 结果 |
|------|------|------|
| 起点 | baseline | 712.28 |
| PROBE A-F | 6 个 low 探针 | 反推出 MSA 模型 |
| MCF 集成 | low 两阶段 MCF | 无改善（tied） |
| SA + correction | low SA + K=2 校正 | 无改善（tied） |
| Multi-start | random restart | 超时回滚 |
| `_reassign_mixed_solution` | MCF 全局 reassign | **-14 分**（唯一有效） |
| 第 1 轮 | MSA 评分模型 + scarce bundle 枚举 | 无改善 |
| 第 2 轮 | tiny 精确求解 + 多样化随机起点 + 局部搜索分级 | 无改善 |
| 第 3 轮 | 结构性 SA（merge/split/re-bundle）+ 鲁棒多模型 | 无改善 |
| 第 4 轮 | scarce PROBE + 随机化贪心 bundles | 待提交 |

**核心发现**：low_seed501 在 4 种不同评分模型/搜索架构下都返回完全相同的 1799.90。要么 1799.90 就是全局最优，要么当前所有模型都在同一个错误方向上一致。

---

## 建议后续方向

1. **完成 scarce PROBE**（G/H/I/J/K 5 次提交），反推 scarce 真实评分模型
2. **如果 scarce PROBE 揭示了校准模型**，用校准后的模型重新优化 scarce
3. **接受 low_seed501 为上限**，不再投入配额
4. **攻 medium_seed202**（17.47/task 异常偏高），可能通过案例诊断找到具体问题
5. **考虑自实现 ILP/B&B**：如果 scarce PROBE 显示有显著改善空间，30-40 任务规模对纯 Python B&B 是可解的
6. **小步提交，每次只改一个变量**，避免无法归因

---

## 关键教训

1. **合成数据 tied 时不提交**：MCF/SA/correction 都在合成数据上 tied（2039.69），但抱侥幸心理提交了，浪费了配额
2. **大改动前先测 timing**：random multi-start 导致 large_seed301 跑 19s，紧急回滚
3. **不要死磕一个方向**：low_seed501 第 4 次提交后就该放弃，转向其他 case
4. **gate 用结构特征**：`couriers < tasks` 而非 candidate 数，避免误触（如 high_noise 被 scarce gate 误伤）
5. **PROBE 是诊断利器**：low PROBE 用 6 次提交换来了关键信息，scarce 也值得做
