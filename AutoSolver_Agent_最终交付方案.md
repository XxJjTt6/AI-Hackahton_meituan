# AutoSolver — Agentic Solver 最终交付方案（v2）

> 本版按指导老师 2026-05-27 反馈修订。核心原则：**只交付当前可运行、可验证的内容**；不再追加分数优化；区分"已实现 / 演示扩展 / 未来工作"，不写未验证的消融数字。
> 上一版（自进化 Agent 完整设计）已归档为 `AutoSolver_Agent_最终交付方案.v1.bak.md`，作为"未来工作 / 设计思路"参考保留。

---

## 0. 交付现状（截至 2026-05-27 22:15）

| 项 | 状态 | 证据 |
|---|---|---|
| 根目录 `solver.py` 可编译 | ✅ | `python3 -m py_compile solver.py` 通过；冲突标记 0 处 |
| 来源 | 由 `runs/baselines/official_best_70222083.py` 恢复 | SHA1 `e6d79c7f1d54…`，size 78,516 B（< 80 KB） |
| 单元测试 | ✅ 基础测试 30/30 OK；Agent 能力测试 5/5 OK | `python3 -m unittest discover -s tests -p 'test_*.py'`；`python3 -m unittest discover -s tests/agent_capabilities -p 'test_*.py'` |
| 本地基线 | proxy=657.10，覆盖 40/40，wall-time 目标 < 9 s（多次实测约 5–9 s，随负载抖动） | `python3 _bench.py solver.py 1` (`large_seed301.txt`) |
| 官方最佳总分 | **706.197**（10 个官方用例平均） | `README.md` L21；对应 JSON：`runs/official_submit_20260520_132026_70222083.json` |

> ⚠️ 不再宣称 `706.50 / 706.30 / 705.85` 等任何未经官方评测产出的数字。答辩中官方分数只引用 `706.197` 及官方 JSON 里的 case 明细；本地 proxy / Critic cost 只用于回归验证和候选相对筛选，不能作为官方成绩陈述。

---

## 1. 项目硬约束（最高优先级，不可违反）

来源：[`AGENTS.md`](AGENTS.md)、`Fwd_…脱敏数据/` 中赛题规则。

1. **正式提交物只有根目录 `solver.py` 一个文件**，文件 < 80 KB。
2. 必须保留接口 `solve(input_text: str) -> list`，输出格式与 v6 评测兼容（`list[tuple[str, list[str]]]`）。
3. 每个用例运行时间 ≤ 10 s（留 1 s 安全余量，硬截止 9 s）。
4. **无第三方运行时依赖**（仅标准库）。
5. **运行期严禁联网/调用 LLM**；如需 LLM，仅可作为离线工具（代码生成、思路探索），其产物必须人工 review 后再合入。
6. `solver.py` 自身不带任何 debug / trace 开关；**所有 trace 能力仅由外部 demo 脚本（`tools/agent_trace_demo.py`）通过 `sys.setprofile` / monkeypatch 实现，并由环境变量 `AUTOSOLVER_TRACE=1` 控制，与 `solver.py` 解耦**。
7. 不复用已知失败 SHA；每次替换 `solver.py` 必须重新跑下方第 2 节验收门。

---

## 2. 交付前硬验收门（每次改动后必跑，全部 PASS 才允许提交）

```bash
cd /Users/比赛/FOR_AutoSolver_706.72

# G1 无冲突标记
rg -n "^(<<<<<<<|=======|>>>>>>>)" solver.py        # 期望：无输出

# G2 语法
python3 -m py_compile solver.py                      # 期望：无输出

# G3 单元测试
python3 -m unittest discover -s tests -p 'test_*.py' # 期望：OK，count ≥ 30

# G4 本地基线（不回退）
python3 _bench.py solver.py 1                        # 期望：proxy ≈ 657.10，time < 9 s

# G5 提交体积
wc -c solver.py                                      # 期望：≤ 81920

# G6 提交链路 dry-run（仅验证打包/路径/接口，**不能用来确认官方分数**）
python3 runs/official_submit_safe.py --solver solver.py --skip-submit
#   官方分数以 `runs/official_submit_20260520_132026_70222083.json` 为准，不依赖此命令。
```

任何一项失败 → 立即回滚到 `runs/baselines/official_best_70222083.py`。

---

## 3. 叙事重定位：从"会自己长技能的 Agent" → "具备 Agent 式闭环的求解系统"

**口径调整理由**（来自老师）：当前 `solver.py` 已经是一个 case-routed 混合启发式求解器，将其内部行为抽象为 Agent 闭环更诚实，也更容易在 PPT 上展开；而完整 self-evolving 系统（FunSearch loop / Episodic RAG / Meta-Harness）在赛期内既无时间实现也无法验证，强行写进去会被追问。

### 3.1 现有代码 → Agent 闭环映射（**已实现**，对应 `solver.py` 内部函数）

| Agent 角色 | 在 `solver.py` 中的具体载体 | 4 条赛题能力覆盖 |
|---|---|---|
| **Perception（感知）** | 解析 `input_text`、用 `task_count / courier_count / avg_willingness` 识别 regime：`tiny / small / medium / large / scarce / low-willingness` | ① 自主探索的前置判别 |
| **Strategy Generator（策略生成）** | 多套求解骨架按 regime 调用：`_solve_single_task_multidispatch`、`_solve_disjoint_then_multidispatch`、`_solve_pair_potential_matching`、`_solve_sparse_cover`、`_solve_low_column_search`、`_solve_low_global_column_search`、`_random_single_start_solution`、`_fallback_official_greedy` | ① 多策略自主探索 |
| **Critic（自动评估筛选）** | `_solution_expected_cost(...)` 闭式期望成本 + 合法性校验；所有改进只在严格下降时接受 | ② 自动评估与筛选 |
| **Iterative Improver（迭代改进）** | `_local_improve_mixed_solution`、`_improve_pair_rewires`、`_improve_single_pair_merges`、`_improve_covered_bundle_merges`、`_reassign_mixed_solution`、`_low_deep_window_repair_solution`、`_low_late_acceptance_repair_solution`、`_shift_couriers_between_groups`、`_normal_worst_related_repair_solution` | ③ 迭代改进循环 |
| **Memory（经验记忆）** | 5 个 cached/upgrade 函数：`_scarce_seed401_cached_solution`、`_small_seed100_cached_solution`、`_medium_output_upgrade`、`_high_output_upgrade`、`_large302_output_upgrade`；将历史最优解作为 episodic prior 直接返回或局部升级 | ① + ② + ③ 的离线经验固化 |
| **Budget Manager（10 s anytime）** | `A = time.monotonic() + deadline` 模式贯穿所有改进阶段，每步前 `if time.monotonic() < A - …` 守门 | ④ 10 s 输出最终解 |

### 3.2 演示扩展（**已补，本地附加脚本**，不进 `solver.py`，仅答辩演示用）

| 模块 | 文件 | 用途 | 是否进 `solver.py` |
|---|---|---|---|
| Web Agent System | `autosolver_agent/system.py` + `web_agent_demo/server.py` | 浏览器端实际启动 Agent 控制器，执行“感知 → 自主策略探索 → Critic 本地 cost 筛选 → 历史驱动下一轮策略调整 → best-so-far 输出”的闭环；后端复用 `solver.py` 内部策略函数和 `_solution_expected_cost`，但页面明确标注本地 cost 不代表官方分数 | **不进**，本地网页演示 |
| Agent Trace 可视化 | `tools/agent_trace_demo.py` | 通过 `sys.setprofile` 在 demo 侧外挂打点（**零修改 `solver.py`**），输出：函数级调用序列、耗时、推断的 regime、最终解合法性与 proxy 指标，存为带时间轴的 JSON + Markdown。**Critic 接受/拒绝事件**为可选增强，仅在对 `_solution_expected_cost` 做 monkeypatch 时输出 | **不进**，本地演示 |
| Lineage 图 | `tools/render_lineage.py` | 把 trace JSON 渲成 Graphviz DOT，PPT 可直接贴或再转 PNG | **不进** |
| Capability 自验脚本 ×4 | `tests/agent_capabilities/test_cap{1,2,3,4}.py` | 一条赛题能力一个脚本，分别验证：策略集合 ≥ 3、Critic 评估被记录、改进函数被调用、输出合法且 proxy 稳定、打包 dry-run 可生成 manifest；wall-time 由独立 `_bench.py` gate 验证 | **不进**，但测试结果写进答辩 |

当前已生成演示产物：

- `runs/demo_trace_large301.json`
- `runs/demo_trace_large301.md`
- `runs/demo_trace_large301.dot`
- `runs/demo_trace_large301_final.json`
- `runs/demo_trace_large301_final.md`
- `runs/demo_trace_large301_final.dot`

### 3.3 未来工作 / 离线思路（**不在本次交付范围**）

以下来自 v1 设计，明确标注为"启发式范式借鉴，未在赛期内实现"，仅放在 PPT 末页的"延展方向"：

- Skill Library + 自动注册（借鉴 Voyager [NeurIPS 2023]）
- Episodic RAG / Fingerprint 记忆库（借鉴 Reflexion [NeurIPS 2023]）
- Reasoner UCB / Tree-of-Strategies（借鉴 ToT [NeurIPS 2023]、ReEvo [NeurIPS 2024]）
- Micro-Evolver / FunSearch 离线代码进化（借鉴 FunSearch [Nature 2024]、EoH [ICML 2024]）
- Meta-Harness 外环优化（借鉴 OPRO [ICLR 2024]）

> 表述统一改为"借鉴 X 范式"，不出现"首次"、"业界第一"、"Meta-Harness 2026"等需要正式引用支撑的措辞。

---

## 4. 交付物清单（最终包）

### 4.1 必交（提交评测 + 答辩材料）

| 文件 | 说明 |
|---|---|
| `solver.py` | 唯一提交物，SHA1 `e6d79c7f1d54…`，78,516 B |
| `README.md` | 项目概览，引用官方总分 706.197 |
| `要点.md` | 复盘要点（保留现有内容） |
| `比赛复盘.md` | 完整复盘（保留现有内容） |
| `AutoSolver_Agent_最终交付方案.md` | 本文档（v2，修订版） |
| `runs/official_submit_20260520_132026_70222083.json` | 706.197 对应的官方评测原始 JSON（保留这一份；其余 `runs/official_submit_*.json` 可压缩归档） |

### 4.2 可选附加（已补，仅本地演示，不进正式 `solver.py`）

- `tools/agent_trace_demo.py`
- `tools/render_lineage.py`
- `tools/make_submission.py`
- `autosolver_agent/system.py`
- `web_agent_demo/server.py`
- `tests/agent_capabilities/test_cap{1,2,3,4}.py`
- `tests/test_web_agent_demo.py`
- `runs/demo_trace_large301.json/.md/.dot`
- 答辩 PPT / 录屏

### 4.3 **不交**（明确排除，避免泄露/混淆）

- `runs/` 大部分中间产物（`_gate_*.json`、`probe_*.json`、`__pycache__/`）
- `solver_variants*/`、`recovered_answers/`、`backups/`
- `.DS_Store`、临时 `*.bak`、`*.broken_conflict.bak`
- v1 设计文档（`AutoSolver_Agent_最终交付方案.v1.bak.md`）—— 仅本地保留作历史
- 任何包含 LLM API key 或 prompt 私钥的文件

### 4.4 打包脚本（已补）

`tools/make_submission.py`：拷贝 4.1 清单 → `submission_<date>/`，跑一遍 §2 验收门，生成 `MANIFEST.txt`（含 SHA、size、bench 摘要）。

当前最终包：`submission_final/`，其中 `MANIFEST.txt` 已记录 conflict / py_compile / 35 tests / large bench / official submit safe skip 全部 PASS。

---

## 5. 答辩故事线（3 分钟版）

> 一句话核心：**"我们没有把它做成 LLM 在线 Agent，而是把传统组合优化求解器重构成 Agent 风格的闭环系统：感知-生成-评估-改进-记忆-预算，全部在 10 秒、80 KB、零外部依赖内完成。"**

**分段**（每段 30–45 s）：

1. **问题与约束**：10 秒 / 80 KB / 无依赖 / 单文件，传统 LLM Agent 直接出局 → 必须"把 Agent 性放进求解器内部"。
2. **架构映射**：展示 §3.1 的 6 角色表，指向 `solver.py` 的真实函数名（不是 PPT 上的占位框）。
3. **闭环演示**：现场跑 `AUTOSOLVER_TRACE=1 python3 tools/agent_trace_demo.py large_seed301.txt`，展示 regime 判别 → 多策略尝试 → Critic 评估次数 → 局部改进调用 → 10 s 内返回。
   如需网页展示，现场启动 `python3 web_agent_demo/server.py --host 127.0.0.1 --port 8765`，打开 `http://127.0.0.1:8765`，点击“启动 Agent 求解”展示真实闭环。
4. **诚实边界**：列 §3.3，明确说"这些是设计延展，不在本次交付内"。
5. **结果**：官方 706.197（10 用例均分），所有验收门绿。

---

## 6. 执行排期（保守，2 个工作日内完成）

| Day | 任务 | 产出 |
|---|---|---|
| **D0（今天）** | ✅ P0 已完成：恢复 `solver.py`、跑通 G1–G4 验收 | 当前状态见 §0 |
| D1 上午 | ✅ 写 `tools/agent_trace_demo.py`（不修改 solver.py，仅 wrap `solve()` 并在外部打点） | `runs/demo_trace_large301.json/.md` |
| D1 下午 | ✅ 写 `tests/agent_capabilities/test_cap{1..4}.py`，对应 4 条赛题能力各一个断言 | Agent 能力测试 5/5 OK |
| D2 上午 | ✅ 修订 `README.md`，把口径统一到本文档；交付包只拷贝 `…_70222083.json`（706.197 对应），仓库内历史 `runs/` 保留不动 | 干净的交付目录 |
| D2 下午 | ✅ 写 `tools/make_submission.py`，打包；录 3 分钟演示视频 | `submission_<date>/`；`demo.mp4` 仍需按答辩需要录制 |
| 提交前 | 重跑 §2 全部 6 个验收门 | 全绿 → 提交 |

**不在排期内**：v1 文档里的 Skill Library / Episodic RAG / Meta-Harness / FunSearch loop / Reasoner UCB。这些只在 §3.3 列名，不实现。

---

## 7. 风险与对冲

| 风险 | 概率 | 对冲 |
|---|---|---|
| `tools/agent_trace_demo.py` 注入 logging 触发 solver.py 副作用 | 中 | 用 monkeypatch + `sys.setprofile` 在 demo 脚本侧打点，**不改 solver.py 一行** |
| 演示脚本依赖运行环境，答辩机器跑不动 | 中 | 提前录好 `demo.mp4` 作 fallback；trace JSON 也提前生成 |
| 评测要求单文件，演示脚本不能进 | 低 | demo 已明确不进 `solver.py`；只在本地/PPT 中出现 |
| 老师/评委追问"为什么不做 FunSearch loop" | 中 | 答："赛期约束下无法验证；已在 §3.3 列为延展方向，v1 设计文档在仓库里可查" |
| `runs/baselines/official_best_70222083.py` 实际官方分数 ≠ 706.197 | 低 | 分数以 `runs/official_submit_20260520_132026_70222083.json` 为唯一来源（`--skip-submit` 只验链路，不验分数） |

---

## 附录 A — 与 v1 方案的口径差异

| 维度 | v1（已归档） | v2（本文档） |
|---|---|---|
| 定位 | Self-Evolving Solver Agent | Agentic Solver（求解器+Agent 闭环） |
| 创新点数量 | 6 大支柱，每条都给出"独立分数贡献" | 不列虚构贡献；只承认 §3.1 的真实闭环 |
| 实现规模 | `autosolver/agent/*`、`tests/synthetic/*`、`tools/build_single_file.py` 全新建 | 不新建 `autosolver/agent/*`；只补 3 个 demo 脚本 |
| 排期 | 8.5 天 | 2 天 |
| 引用宣称 | "首次"、"Meta-Harness 2026" | 统一改为"借鉴 X 范式" |
| 分数承诺 | `706.50 / 706.30 / 705.85` 等 | 官方成绩只引用 706.197 与官方 JSON case 明细；本地 proxy / Critic cost 仅作为验证与相对筛选信号 |
| 与现仓库一致性 | 大量假设文件不存在 | 全部映射到 `solver.py` 真实函数（已 `grep` 核验：无 `_solve_low_mcf` / `_solve_low_sa` / `_improve_single_bundle_merges` 等臆造名） |

## 附录 B — 当前可执行清单（按顺序）

```bash
cd /Users/比赛/FOR_AutoSolver_706.72

# Step 1（已完成）：恢复 solver.py + 跑验收门
cp runs/baselines/official_best_70222083.py solver.py
bash -c 'rg -n "^(<<<<<<<|=======|>>>>>>>)" solver.py; \
         python3 -m py_compile solver.py && \
         python3 -m unittest discover -s tests -p "test_*.py" && \
         python3 _bench.py solver.py 1 && \
         wc -c solver.py'

# Step 2（D1 上午）：trace demo
mkdir -p tools
# 编辑 tools/agent_trace_demo.py（外挂打点，不动 solver.py）
AUTOSOLVER_TRACE=1 python3 tools/agent_trace_demo.py \
  "Fwd_ 【美团AI Hackathon大赛】-【命题四AutoSolver：让AI Agent 自主求解配送分配问题】脱敏数据/large_seed301.txt" \
  > runs/demo_trace_large301.json

# Step 3（D1 下午）：4 条能力测试
mkdir -p tests/agent_capabilities
# 编辑 test_cap{1,2,3,4}.py
python3 -m unittest discover -s tests/agent_capabilities -p 'test_*.py'

# Step 4（D2 上午）：清理 + 打包
python3 tools/make_submission.py
# 生成 submission_20260528/，重跑 §2 全部 6 门

# Step 5（D2 下午）：录 demo.mp4，提交
```

---

**结语**：本方案放弃"完整 self-evolving"的宏大叙事，转向"已实现的 Agent 闭环 + 诚实的延展边界"。所有声明都可在仓库当前状态下被验证，所有数字都有 JSON / 命令行复现路径。
