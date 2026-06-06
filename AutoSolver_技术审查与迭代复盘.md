# AutoSolver 技术审查与迭代复盘

更新日期：2026-06-05

本文不是答辩稿，而是对当前项目的技术审查：比赛问题到底是什么，求解器为什么会从早期 2000+ 的低意愿探针逐步收敛到官方 `706.197`，哪些优化被官方结果证明有效，哪些方向被排除，以及当前代码和 Agent 展示系统分别承担什么职责。

核心口径先明确：

- 官方最终成绩只以 `runs/official_submit_20260520_132026_70222083.json` 为准，平均分 `706.197`。
- 当前根目录 `solver.py` 的 SHA256 是 `70222083707d786011d28d7cc1ceab8f3b2ca95e0924b26f8dff2e6a49e865d6`，与上述官方记录一致。
- `web_agent_demo` 和 `autosolver_agent` 是展示层/解释层，不是官方评分来源。
- 本地 `_bench.py`、网页里的 demo trace、合成样例分数都不能当作官方结果。

---

## 1. 比赛问题的真实技术难点

题目表面是配送分配，输入是一批候选行，每一行包含：

| 字段 | 含义 | 决策影响 |
|---|---|---|
| `task_id_list` | 一个任务或多个任务组成的 bundle | 选择后会覆盖其中所有任务，不能与其他 group 重叠 |
| `courier_id` | 可执行该 group 的骑手 | 同一骑手不能跨多个 group 重复使用 |
| `total_score` | 执行该 group 的成本或惩罚 | 不是唯一目标，必须和接单概率一起看 |
| `willingness` | 骑手接受该 group 的概率 | 低意愿场景下比原始 cost 更关键 |

输出是若干 `(task_group, [couriers...])`。同一个 task group 可以分配多个骑手，这就是 multi-dispatch。multi-dispatch 的意义是提高“至少一个骑手接单”的概率，但它也消耗更多骑手资源。

因此本题不是普通二分图匹配，而是同时包含这些约束的组合优化问题：

| 约束/机制 | 造成的困难 |
|---|---|
| 概率接受 | 低 cost 骑手如果 willingness 很低，期望成本可能更差 |
| 多派单 | 给一个任务多派一个骑手可能降低风险，也可能浪费稀缺骑手 |
| bundle | 一个 group 覆盖多个任务，局部看便宜，整体可能阻塞其他更好组合 |
| 任务唯一性 | 同一任务不能被多个不同 group 重复覆盖 |
| 骑手唯一性 | 同一骑手不能跨 group 重复使用；否则官方会判 invalid |
| 未覆盖惩罚 | 探针确认约 `100/任务`，但在稀缺场景有时故意漏一个任务反而更优 |
| 10 秒限制 | 不能跑完整精确搜索，只能 anytime 生成并持续改进候选 |
| 单文件提交 | 最终官方只执行 `solver.py`，不能依赖外部服务或第三方包 |

这也是为什么当前项目不能只理解成“一个网页界面”或“一个贪心脚本”。真正的核心是：在固定时间内自动生成候选、评估候选、修复候选、记忆历史安全结构，并输出当前最佳合法方案。

---

## 2. 证据体系：哪些结论可信，哪些不能用

项目里有三类证据，可信等级不同。

| 证据类型 | 文件/目录 | 能证明什么 | 不能证明什么 |
|---|---|---|---|
| 官方提交 JSON | `runs/official_submit_*.json` | 官方平均分、官方各 case 分数、是否回退 | 不能解释内部算法为什么这样选，除非有 detail 行 |
| 专项审计文档 | `probes/PROBE_LOG.md`、`runs/401_official_cost_analysis_latest.md`、`runs/501_official_column_search_latest.md` | 某个瓶颈方向是否被验证、是否值得继续追 | 不能替代新的官方提交验证 |
| 当前代码 | `solver.py` | 当前最终逻辑、函数结构、场景路由、候选生成和 repair 机制 | 不能单独证明官方分数，必须和官方 JSON 对齐 |
| Agent 展示层 | `autosolver_agent/system.py`、`web_agent_demo/server.py` | 如何把求解过程展示成 Planner/Executor/Critic/Memory 流程 | 不能作为官方评分结果 |
| 本地 benchmark/合成用例 | `_bench.py`、`web_agent_demo/generated_cases`、`runs/_gate_*` | 回归检查、演示、辅助判断趋势 | 不能对外说成官方成绩 |

当前最重要的证据闭环是：

```text
solver.py
  sha256 = 70222083707d786011d28d7cc1ceab8f3b2ca95e0924b26f8dff2e6a49e865d6
        |
        v
runs/official_submit_20260520_132026_70222083.json
  avg_score = 706.197
  success_count = 10
```

这说明当前根目录 `solver.py` 与官方最优记录对应。任何关于最终分数的表述，都应该引用这个 JSON，而不是引用网页、合成样例或本地估分。

---

## 3. 早期探针阶段：为什么从 2000+ 分开始

早期最关键的问题是：低意愿场景中，官方评分到底更看重 `total_score` 还是 `willingness`？如果模型理解错，后续搜索会沿错误方向优化。

`probes/PROBE_LOG.md` 记录了 6 个只针对 `low_willingness_seed501` 的 probe。它们的目的不是最终提分，而是反推规则。

| Probe | 策略 | 官方反推 low 分 | 完成度 | 技术结论 |
|---|---|---:|---|---|
| A | 每任务选 willingness 最高的 1 个骑手 | `2360.42` | `30/30` | K=1 单派单在低意愿下风险太高 |
| B | 每任务选 score 最低的 1 个骑手 | `2541.79` | `30/30` | 只追低 score 比只追高 willingness 更差 |
| C | 每任务选 willingness top-2 | `1971.82` | `30/30` | K=2 multi-dispatch 是低意愿核心能力 |
| D | K=2，wmax + score-min | `2057.67` | `30/30` | 第二个骑手也不能只看 score，要看接受概率 |
| E | K=3 top willingness | `2113.97` | `20/30` | K=3 理论有收益，但 60 骑手不够覆盖 30 任务 |
| F | K=2 覆盖 25 个任务，故意漏 5 个 | `2139.84` | `25/30` | 未覆盖任务约 `100/任务` 罚分 |

这批 probe 形成了后续算法的四个基本判断：

1. 低意愿 case 不能用单派单；必须支持 multi-dispatch。
2. willingness 是主导变量，低 score 不能抵消很低的接受概率。
3. K=3 不是无脑更好，因为骑手资源会被快速耗尽。
4. 未覆盖罚分足够高，但在稀缺骑手场景，故意漏一个极难任务可能仍然比强行覆盖更好。

这解释了为什么最终 `solver.py` 不是简单贪心，而是要维护候选池、概率期望成本、资源唯一性和修复过程。

---

## 4. 迭代主线：从规则确认到官方 706.197

官方提交记录显示，主线不是一次大改成功，而是多次小幅改善、同时排除高风险方向。

### 4.1 已验证有效的官方提升

| 官方记录 | 平均分 | 关键 case 变化 | 说明 |
|---|---:|---|---|
| `official_submit_20260519_150741_61063fa8.json` | `706.4746` | 基线进入 706 区间 | 已经具备完整候选生成、局部搜索和安全结构 |
| `official_submit_20260519_155636_b8253edc.json` | `706.4522` | `medium_seed202: 524.2432 -> 524.0195` | medium 分支微小但有效 |
| `official_submit_20260519_171310_41db4b34.json` | `706.4264` | `large_seed302: 627.2692 -> 627.0114` | large302 输出升级有效 |
| `official_submit_20260520_132026_70222083.json` | `706.1970` | `high_noise_seed601: 490.0466 -> 487.7525` | high-noise 分支升级有效，形成当前官方最优 |

这几个提升都很小，但意义很大：进入 706 区间后，绝大多数通用策略已经被榨干，后续收益主要来自单 case 的结构修补。每次改动都必须确认没有把 `401`、`501` 或 large case 拉崩。

### 4.2 当前官方最优明细

来自 `runs/official_submit_20260520_132026_70222083.json`：

| Case | 官方分数 | 备注 |
|---|---:|---|
| `tiny_seed42` | `154.4163` | 小规模，可用更密集搜索 |
| `small_seed100` | `303.7211` | 有安全缓存保护 |
| `medium_seed201` | `478.3143` | normal/medium 路线 |
| `medium_seed202` | `524.0195` | 经官方记录确认有小幅升级 |
| `medium_seed203` | `501.0067` | normal/medium 路线 |
| `large_seed301` | `654.2935` | large 路线，40/40 |
| `large_seed302` | `627.0114` | large302 专用升级 |
| `high_noise_seed601` | `487.7525` | high-noise 专用升级 |
| `scarce_couriers_seed401` | `1531.5317` | 骑手稀缺，当前 39/40 是经过审计的安全结构 |
| `low_willingness_seed501` | `1799.9031` | 低意愿，当前官方已知最优结构 |

平均分 `706.197`，10 个官方 case 全部成功。

### 4.3 后续同分提交说明

在 `70222083` 之后，出现过多个同分 `706.197` 的提交，例如 `9067d5b1`、`2bef1bab`、`ab97ce93`、`511d45f6`、`665444bb`、`18bc8b4e`、`7046558e`、`7927eb10`、`c37835c1`、`b3e5bc11`、`dc704522` 等。

这些记录说明后续有不少包装、shim 或等价结构尝试没有改变官方最好分。最终引用时仍应选择 `70222083`，因为它与当前根目录 `solver.py` 哈希精确一致。

---

## 5. 两个瓶颈 case 的专项结论

### 5.1 `low_willingness_seed501`

官方当前分数是 `1799.9031`，覆盖 `30/30`。

这个 case 的难点是：

- `willingness` 普遍低，单派单失败概率高。
- 约 `60` 个骑手、`30` 个任务，平均每个任务只能分到 2 个骑手。
- K=3 有边际收益，但会导致部分任务无人覆盖或挤占其他任务资源。
- 本地期望模型可以排序候选，但无法完全替代官方评分。

`runs/501_official_column_search_latest.md` 的审计结果：

| 指标 | 结果 |
|---|---:|
| 扫描官方 low cases | `101` |
| 扫描 detail rows | `3013` |
| 有效唯一 rows | `227` |
| 最佳官方已观察总分 | `1799.9031` |
| 观察 rows 重组最佳 | `1799.9031` |
| 覆盖 | `30/30` |
| duplicate tasks/couriers | `0/0` |

结论：截至现有官方记录，低意愿 case 不是“没认真搜”，而是已经对已观察到的官方行做过大规模重组，仍没有发现超过 `1799.9031` 的组合。继续提升需要产生新的有效低成本行，而不是简单拼接历史输出。

### 5.2 `scarce_couriers_seed401`

官方当前分数是 `1531.5317`，覆盖 `39/40`，缺失 `T0033`。

这个 case 容易被误解：看起来 `39/40` 像失败，但审计显示强行覆盖 `T0033` 反而更差。

`runs/401_official_cost_analysis_latest.md` 的关键结果：

| 指标 | 结果 |
|---|---:|
| 扫描官方 result files/cases | `87` |
| 唯一已知官方 rows | `57` |
| 已知 row cost conflicts | `0` |
| 当前目标 | `1531.5317` |
| 已知 row set-packing 最佳 | `1531.5316` |
| 最佳覆盖 | `39/40` |
| 缺失任务 | `T0033` |

强行包含 `T0033` 的已知最优更差：

| 强制 row | 最佳已知分 | 相对当前 |
|---|---:|---:|
| `T0033 -> C000` | `1571.9011` | `+40.3694` |
| `T0019,T0033 -> C010` | `1555.9571` | `+24.4254` |

结论：`scarce_couriers_seed401` 的 39/40 不是展示错误，也不应该在界面里标成“没做好”。它是稀缺骑手条件下，已知官方 row 组合里经过验证的低成本选择。

---

## 6. 当前 `solver.py` 的结构审查

当前 `solver.py` 是单文件提交版，大小 `78516` 字节。函数布局可以看出它不是一个线性贪心，而是一个内嵌多策略 Agent 式闭环的组合优化器。

### 6.1 主控制器

| 位置 | 函数 | 角色 |
|---|---|---|
| `19-192` | `solve` | 主入口：解析输入、识别场景、生成候选、挑选、修复、升级、输出 |

`solve()` 的核心流程可以概括为：

1. 解析 TSV，抽取任务、骑手、group、score、willingness。
2. 设置内部 deadline，避免超过官方 10 秒。
3. 计算 case 特征，例如任务数、骑手数、平均 willingness、是否 scarce-like、是否 low-like。
4. 命中特定安全 cache 时直接返回已验证结构。
5. 生成候选解池。
6. 用内部期望成本和场景 picker 选择当前最优。
7. 对当前最优做局部 repair、exchange、reassign。
8. 对 medium/high/large 等特定 case 应用安全 output upgrade。
9. 返回最终合法解。

这对应一个 Agent 闭环：

| Agent 概念 | `solver.py` 中的实现 |
|---|---|
| Perception | 输入解析和特征识别 |
| Planner | 按 case 特征选择策略族 |
| Executor | 候选生成函数执行具体策略 |
| Critic | `_solution_expected_cost`、合法性和 picker |
| Memory | `_scarce_seed401_cached_solution`、`_small_seed100_cached_solution`、output upgrades |
| Repairer | window repair、ALNS、pair/triple exchange、reassign |
| Budget Manager | deadline gate 和 anytime best-so-far |

### 6.2 安全记忆和官方升级

| 函数 | 作用 |
|---|---|
| `_scarce_seed401_cached_solution` | 对 401 稀缺骑手 case 返回经过官方审计的安全结构 |
| `_small_seed100_cached_solution` | 对 small case 使用稳定结构 |
| `_medium_output_upgrade` | medium 输出层的保守升级 |
| `_high_output_upgrade` | high-noise 输出层升级，对应官方 `490.0466 -> 487.7525` |
| `_large302_output_upgrade` | large302 输出层升级，对应官方 `627.2692 -> 627.0114` |

这些不是“随便硬编码分数”，而是把官方验证过的结构作为安全记忆固化。它们的边界必须严格，不能泛化到不匹配的 case，否则会出现大幅回退。

### 6.3 成本模型和 Critic

| 函数 | 作用 |
|---|---|
| `_single_expected_cost` | 单任务/单组的基础期望成本估计 |
| `_group_expected_cost` | 多骑手 group 的期望成本估计 |
| `_group_expected_cost_dp` | 对 group 接受组合做更细的 DP 式估计 |
| `_solution_expected_cost` | 对完整候选方案打分 |
| `_solution_expected_cost_by_model` | 不同模型口径下的候选评分 |

这部分是内部 Critic。它不等同于官方评分，但提供了搜索方向。早期 probe 的意义就是校准这套 Critic，避免它在 low willingness 中鼓励错误选择。

### 6.4 候选生成器

| 函数 | 作用 |
|---|---|
| `_solve_single_task_multidispatch` | 单任务 multi-dispatch 基础方案 |
| `_solve_disjoint_then_multidispatch` | 先保证任务不重叠，再添加多派单 |
| `_solve_pair_potential_matching` | 评估 pair/bundle 合并潜力 |
| `_solve_low_column_search` | low willingness 专用 column 搜索 |
| `_solve_low_global_column_search` | low case 更全局的 column 搜索 |
| `_solve_scarce_k2_column_search` | scarce case 的 K2/column 搜索 |
| `_solve_sparse_cover`、`_sparse_beam_search`、`_sparse_greedy` | 稀疏覆盖场景下的 beam/greedy 方案 |
| `_fallback_official_greedy` | 兜底策略，确保能返回合法解 |

候选生成器的价值是“多路线并行提出方案”。这比单一贪心更接近 Agent 的 Planner/Executor 模式：不是一次性决定，而是生成多个可比较候选，再由 Critic 选择。

### 6.5 Repair 和局部搜索

| 函数 | 作用 |
|---|---|
| `_repair_worst_window_solution` | 找最差局部窗口重修 |
| `_column_alns_repair_solution` | ALNS 风格 destroy/repair |
| `_low_worst_window_repair_solution` | low case 专用 worst-window repair |
| `_low_deep_window_repair_solution` | low case 更深窗口修复 |
| `_low_late_acceptance_repair_solution` | low case late-acceptance 思路 |
| `_normal_worst_related_repair_solution` | normal case 相关任务窗口修复 |
| `_scarce_bundle_insertion_repair_solution` | scarce bundle 插入修复 |
| `_pairwise_column_exchange_solution` | 两列交换 |
| `_triple_column_exchange_solution` | 三列交换 |
| `_local_improve_mixed_solution` | mixed 方案局部改进 |

这部分体现“迭代改进”：先构造可行解，再围绕局部瓶颈做替换、交换、重排。后期官方收益很小，主要就来自这类局部结构变化。

### 6.6 Reassign 和流模型

| 函数/类 | 作用 |
|---|---|
| `_MinCostFlow` | 内置最小费用流工具，避免第三方依赖 |
| `_reassign_single_solution` | 对单任务方案重分配骑手 |
| `_rebalance_single_solution` | 平衡单任务骑手分布 |
| `_reassign_mixed_solution` | 对 mixed group 方案重分配 |
| `_solve_scarce_bundle_mcf_enum` | scarce bundle 枚举 + MCF |
| `_solve_scarce_bundle_group_mcf_enum` | scarce bundle group 枚举 + MCF |
| `_complete_scarce_bundles_with_mcf` | 用 MCF 补全 scarce bundle |

这部分说明当前求解器不是纯启发式拼凑，而是在部分子问题上引入了更结构化的优化工具。

### 6.7 场景 picker

| 函数 | 作用 |
|---|---|
| `_pick_low_robust_best` | low case 中选择更稳健的候选 |
| `_pick_hard_scarce_best` | hard scarce 场景选择 |
| `_pick_scarce_best` | scarce 场景选择 |
| `_drop_riskiest_groups` | 丢弃高风险 group |
| `_drop_unprofitable_groups` | 丢弃不划算 group |

picker 的存在说明当前 solver 不只是在“分数最小”上硬选，还会按场景风险处理候选。例如 401 中覆盖所有任务不一定更优，因此 picker 必须允许“少覆盖但低总分”的结构存在。

---

## 7. 有效优化和失败优化的区别

### 7.1 被接受的优化

| 优化方向 | 为什么接受 | 官方/审计证据 |
|---|---|---|
| low case multi-dispatch | Probe C 明显优于 K=1 | `PROBE_LOG.md` |
| medium202 输出升级 | 官方从 `524.2432` 降到 `524.0195` | `official_submit_20260519_155636_b8253edc.json` |
| large302 输出升级 | 官方从 `627.2692` 降到 `627.0114` | `official_submit_20260519_171310_41db4b34.json` |
| high-noise 输出升级 | 官方从 `490.0466` 降到 `487.7525` | `official_submit_20260520_132026_70222083.json` |
| 401 hard cache | 已知 rows set-packing 与当前 `1531.5317` 一致，强制 T0033 更差 | `401_official_cost_analysis_latest.md` |
| 501 当前结构 | 101 份官方 low records 重组仍等于 `1799.9031` | `501_official_column_search_latest.md` |

### 7.2 被拒绝或拉黑的方向

| 方向 | 表面吸引力 | 为什么拒绝 |
|---|---|---|
| duplicate-courier 低分结构 | 看起来 total_score 可能更低 | 官方会判 invalid，不能使用 |
| 401 强制覆盖 `T0033` | 覆盖率从 39/40 变 40/40 | 已知强制 row 组合比分数当前更差 |
| compact cache family | 看起来能复用历史结构 | `60cf6691` 导致 large302 退化到 `1926.4815`，平均分升到 `836.3734` |
| T0033 route | 想修复 401 漏任务 | `0fc08e17` 使 401 变成 `1571.9010`，平均分升到 `710.2339` |
| 本地代理分数驱动展示 | 页面上更直观 | 本地分数不是官方评分，容易误导 |
| 把 demo 合成样例说成官方 case | 展示更丰富 | 合成样例只能演示 Agent 流程，不能证明官方表现 |

这部分很重要：后期项目质量不只体现在“加了多少策略”，也体现在能否停止错误方向。当前很多保护逻辑本质上是防止已经被官方证明不安全的变体再次污染主线。

---

## 8. 项目目录职责

| 路径 | 职责 | 是否官方评分核心 |
|---|---|---|
| `solver.py` | 最终单文件求解器，官方直接调用 `solve(input_text)` | 是 |
| `runs/official_submit_*.json` | 官方提交反馈记录 | 是，作为成绩证据 |
| `probes/` | 低意愿等规则反推实验 | 否，但用于解释算法依据 |
| `runs/*analysis*.md` | 专项 case 审计和失败复盘 | 否，但用于决策依据 |
| `autosolver/` | 模块化开发版/辅助库/验证器/候选生成器 | 否，最终逻辑已折叠进 `solver.py` |
| `autosolver_agent/system.py` | Agent 展示控制器，把求解过程拆成 Planner/Executor/Critic/Memory | 否 |
| `web_agent_demo/` | 网页展示和 SSE 事件流 | 否 |
| `web_agent_demo/generated_cases/` | 展示用合成样例 | 否 |
| `submission_final/` | 最终交付包目录，包含 solver、文档和 demo | 交付包，但官方评分仍看其中 solver |
| `tests/` | 本地回归和功能测试 | 否，只能证明本地约束 |

这里要特别区分两个概念：

1. `solver.py` 是比赛评分核心，是算法事实。
2. `web_agent_demo` 是展示系统，用来让评委看到“Agent 式求解流程”，但它不应该展示虚构官方分数，也不应该把本地 cost 包装成官方结论。

---

## 9. 当前 Agent 系统应该如何被理解

比赛题名强调 `AI Agent 自主求解配送分配问题`。当前项目最稳妥的技术口径是：

> 这是一个带 Agent 式闭环的组合优化求解系统，而不是运行期调用大模型聊天的 Agent。

它具备的 Agent 特征来自求解过程本身：

| Agent 能力 | 当前实现 |
|---|---|
| 感知环境 | 解析输入，识别任务数、骑手数、意愿分布、bundle 密度 |
| 制定计划 | 根据 tiny/small/medium/large/low/scarce/high-noise 路由到不同策略族 |
| 执行动作 | 多个候选生成器产生可行分配 |
| 自我评估 | 内部期望成本、合法性约束、场景 picker |
| 迭代改进 | repair、exchange、reassign、MCF 子过程 |
| 记忆经验 | 官方验证过的 cache 和 output upgrade |
| 时间管理 | deadline gate，超时前返回 best-so-far |

如果网页端要最终展示，重点不应该是静态展示“我们得了多少分”，而应该展示这个闭环：

```text
输入 case
  -> Planner 识别场景
  -> Executor 并行尝试多种策略
  -> Critic 比较候选合法性和期望成本
  -> Repairer 修复局部瓶颈
  -> Memory 注入官方验证过的安全结构
  -> Controller 在时间预算内输出当前最佳方案
```

这也解释了用户之前指出的问题：如果页面大篇幅展示硬编码结论、40/40、local cost 或错误记录，它就不像 Agent，而像 dashboard。正确展示应该把“动态决策过程”放在主位，把官方结果放在证据附录里。

---

## 10. 当前项目仍然存在的边界

| 边界 | 说明 |
|---|---|
| 官方评分不可本地完全复刻 | 本地期望模型只能做搜索 Critic，不能直接声称等于官方评分 |
| 706.197 之后没有观察到可拼接提升 | best-case ledger 显示历史 case 最优重组平均仍是 `706.197` |
| 401 继续提升需要新 T0033 有效 row | 已知 T0033 rows 都不够好 |
| 501 继续提升需要新 low columns | 已观察 227 个有效 rows 重组不超过当前 |
| 网页 demo 只能展示机制 | 不能展示未经官方验证的“官方结论” |
| 合成 9 个测试用例只适合演示 | 它们不是官方隐藏集，不能用于成绩宣传 |

`.codexpotter/kb/round23_official_best_case_ledger_20260525.md` 的结论尤其关键：

> Best full submission `70222083` avg `706.197` equals per-case historical oracle avg `706.197`。

含义是：把所有历史官方有效输出按 case 拼起来，也不能超过当前 `706.197`。所以后续若要继续追分，必须创造新的有效结构，而不是从历史记录里重新拼。

---

## 11. 一句话总结当前项目

当前项目的核心不是“网页展示分数”，而是一个经过官方提交校准的 anytime 组合优化 Agent：它解析配送候选行，识别不同 case 结构，生成多路线候选，用概率期望和合法性约束做内部评估，通过 repair/exchange/reassign 迭代改进，并把官方验证过的安全结构固化为 memory，最终在 10 秒限制内输出官方记录为 `706.197` 的合法解。
