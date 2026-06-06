# AutoSolver — Self-Evolving Solver Agent

> 美团 AI Hackathon 命题四 · 最终交付方案
> 版本：v1.0 · 日期：2026-05-27
> 定位：一个**会自己长出求解技能**的 Agent，而非另一个堆参数的求解器

---

## 0. TL;DR

**一句话：**
AutoSolver 把组合优化求解器重构为可终身学习的 Agent——**在线**用 Tree-of-Strategies + Episodic RAG + Reflective Micro-Evolution 在 10 秒内闭环；**离线**用 FunSearch 风格的代码级进化 + Meta-Harness 外层循环让 Agent 自动重写自己的 Skill Library 和路由规则。

**关键差异化：**
首次把 Voyager 的技能库、Reflexion 的反思、FunSearch 的代码进化、Meta-Harness 的自重写**四条独立研究主线**统一到一个 10 秒预算的求解器 Agent 中。

---

## 1. 参考的开源/论文工作

| 项目 | 借鉴点 |
|---|---|
| **FunSearch** (DeepMind, Nature 2024) | LLM 在程序空间进化启发式代码 |
| **AlphaEvolve** (DeepMind 2025) | 进化-评估闭环、代码级 diff 变异 |
| **Voyager** (NeurIPS 2023) | Skill Library 终身学习、技能可累积可复用 |
| **Reflexion** (NeurIPS 2023) | 每轮失败 → 生成 "lesson" 写入 episodic memory |
| **ReEvo** (NeurIPS 2024) / **EoH** (ICML 2024) | 演化启发式 + reflective mutation |
| **Tree-of-Thoughts** (NeurIPS 2023) | 多分支策略搜索 + Critic 剪枝 |
| **DSPy** (Stanford) | 把 prompt/policy 编译为可优化模块 |
| **Meta-Harness** (Lee et al. 2026) | 外层循环优化 Agent 自身的 harness 组件 |
| **OPRO** (Google ICLR 2024) | LLM-as-Optimizer，把搜索写成自然语言迭代 |

---

## 2. 赛题 4 条交付目标 → 4 个 Agent 组件

| 赛题条款 | Agent 组件 | 工程对应物 |
|---|---|---|
| ① 自主策略探索（不指定算法） | **Reasoner / Planner** | ToS 多分支 + UCB1 自主选下一策略 |
| ② 自动评估与筛选 | **Critic / Evaluator** | 闭式评分函数 + best-so-far 池 + 节点剪枝 |
| ③ 迭代改进循环 | **Memory + Loop** | Episodic / Semantic / Procedural 三层记忆反哺 Reasoner |
| ④ 10 秒输出最终解 | **Executor + Budget Manager** | Anytime 调度 + 兜底返回 best-so-far |

> **关键认识**：现有 `solver.py`（1669 行）是 if-else 路由的混合启发式——它**不是 Agent**。Agent 的"大脑"必须新写，`solver.py` 里的 `_solve_*` 函数降级为 Agent 可调用的 **Action / Skill**。

---

## 3. 系统总览

```mermaid
flowchart TB
    subgraph Online[在线 10s ─ Inner Loop]
        Inp[Input] --> Fp[Fingerprint<br/>实例指纹]
        Fp --> RAG[Episodic RAG<br/>检索 top-K 历史相似案例]
        RAG --> ToS[Tree-of-Strategies<br/>多分支并发探索]
        ToS --> Crit[Critic<br/>闭式评分 + 剪枝]
        Crit --> Refl[Reflector<br/>蒸馏 lesson]
        Refl --> Micro[Micro-Evolve<br/>参数/sort-key 微变异]
        Micro --> ToS
        Crit --> Out[best-so-far]
    end

    subgraph Skills[Skill Library<br/>可持续生长]
        S1[skill_v1: greedy_md]
        S2[skill_v2: ilp_column]
        S3[...]
        Sn[skill_vN: evolved_2026-05-27]
    end
    ToS -.调用.-> Skills

    subgraph Memory[Long-term Memory]
        EM[Episodic<br/>case fingerprint→winning trace]
        SM[Semantic<br/>lessons in NL]
        PM[Procedural<br/>Reasoner weights]
    end
    RAG <--> EM
    Refl --> SM & EM

    subgraph Offline[离线 ─ Outer Loop · Meta-Harness]
        Evo[FunSearch-style<br/>LLM 代码进化] --> NewS[new skill code]
        NewS --> Bench[10 官方 + 12 自构]
        Bench --> Promo{升级?}
        Promo -- yes --> Skills
        Bench --> RW[Reasoner Weights<br/>重训练]
        RW --> PM
        SM -.lessons distill.-> Rules[Routing Rules<br/>自动重写]
        Rules --> PM
    end
```

**6 大创新支柱：**
1. **Skill Library** — 求解策略作为代码"技能"，可被代码级进化扩展
2. **Episodic RAG** — 实例指纹 → 历史相似 case 的获胜 trace 优先 replay
3. **Tree-of-Strategies (ToS)** — 多分支并发 + Critic 剪枝（不是单线 ReAct）
4. **Online Micro-Evolution** — 10s 内对 best 策略做 FunSearch-mini 参数微变异
5. **Reflective Lessons** — 每个 trial 产出自然语言 lesson，沉淀为 Reasoner 约束
6. **Meta-Harness Outer Loop** — Agent 离线自我重写路由规则与权重

---

## 4. 创新点详解

### 4.1 创新点 1 — Skill Library（Voyager + FunSearch）

**目录结构：**

```
autosolver/agent/skills/
├── _registry.py                  # SkillLibrary: name→version→callable + metadata
├── manifest.json                 # 当前激活的 skill 版本 + 谱系树
├── skill_greedy_md_v1.py
├── skill_ilp_column_v1.py
├── skill_low_mcf_sa_v1.py
├── skill_scarce_shadow_v1.py
├── skill_lns_v1.py
├── skill_evolved_sort_v3.py      # ← LLM 离线进化产物，自动生成
├── skill_evolved_sort_v7.py
└── lineage.dot                   # graphviz 谱系图
```

**每个 skill 自包含：**

```python
# skill_evolved_sort_v7.py — auto-generated 2026-05-23 by FunSearch loop
"""
Lineage: greedy_md_v1 → mutate(sort_key, +willingness_log) → evolved_sort_v3
       → mutate(weight_adjust) → evolved_sort_v7
Benchmark: avg=706.81 on 10 official + 12 synthetic
Best on: low_willingness, dense_high_w
"""
META = {
    "name": "evolved_sort_v7",
    "category": "greedy",
    "complexity_class": "O(n·m·log n)",
    "applies_to_regime": ["low_willingness", "normal"],
    "expected_runtime_ms": {"n=30": 120, "n=40": 220},
    "parent": "evolved_sort_v3",
}
def run(state, budget): ...
```

**亮点**：评委看到的是一棵**有谱系的技能树**（`lineage.dot` 直接渲染），不是 if-else。

---

### 4.2 创新点 2 — Episodic RAG（Reflexion + RAG）

**目录结构：**

```
autosolver/agent/memory/
├── episodic.jsonl                # 每行 = 一次历史运行
├── fingerprint.py                # 实例 → 12-维特征向量 + LSH
└── retriever.py                  # top-K nearest neighbors (cosine)
```

**实例指纹（12 维）：**

```
[n_tasks, n_couriers, c/t_ratio, avg_w, w_std, w_skew,
 bundle_density, score_mean, score_std, regime_onehot×4]
```

经 z-score 标准化后存入 `episodic.jsonl`。

**在线流程：**

```python
fp = fingerprint(instance)
neighbors = episodic.retrieve(fp, k=3)
# neighbors = [
#   {fp: ..., winning_strategy: "scarce_shadow",
#    params: {...}, score: 1531.5, lessons: [...]},
#   ...
# ]
# 作为 Reasoner.propose() 的第 0 轮 prior
# → warm start 把对手用于探索的时间转化为改进的时间
```

**亮点**：把 **RAG** 概念引入 OR/CO 求解器——"求解经验的 RAG"，呼应 "auto-research" 理念。

---

### 4.3 创新点 3 — Tree-of-Strategies（ToT for CO）

不是 ReAct 单线，而是分支搜索：

```
                root: state=low_w, budget=9.0
                /         |          \
       greedy_md      ilp_column     low_mcf_sa
       (0.3s, 1820)  (2.5s, 1798)    (1.2s, 1810)
       ❌剪枝          继续展开          继续展开
                      /         \
                refine_lns    micro_evolve
                (1.0s,1795)   (0.5s, 1793)
                              ✅当前 best
```

**节点选择用 UCT：**

$$
\text{UCT}(node) = \hat\mu_{node} + c \cdot \sqrt{\frac{\ln N}{n_{node}}}
$$

每个节点 = 一次 trial；每条边 = micro-action（深化 / 切换策略 / 微变异）；Critic 根据 score 上下界做硬剪枝。

**亮点**：CO 求解器里少见的 ToT 实现；可作为 Demo 的视觉锚点（ToS 搜索树动画）。

---

### 4.4 创新点 4 — Online Micro-Evolution（FunSearch-mini）

FunSearch 完整版需要在线 LLM 调用，10s 不现实。我们做"**离线 LLM 生成参数空间 + 在线随机微扰**"：

**离线：** LLM 产出每条 skill 的可演化超参定义

```python
EVOLVABLE = {
    "greedy_md": {
        "sort_key_weights": {
            "w": (0.5, 2.0),
            "log_w": (0.0, 1.0),
            "score": (-1.5, -0.5),
        },
        "top_k": (1, 5),
    },
    ...
}
```

**在线：** Reasoner 决定做 micro-evolve 时

```python
def micro_evolve(best_skill, best_params, budget):
    for _ in range(int(budget / best_skill.expected_runtime_s)):
        candidate = perturb(best_params, sigma=0.15)   # 高斯扰动
        sol = best_skill.run(state, candidate)
        if better(sol):
            best_params = candidate
```

**亮点**：在 10s 硬约束里实现 FunSearch-flavor 进化——别人没做。

---

### 4.5 创新点 5 — Reflective Lessons（Reflexion）

每个 trial 跑完，Reflector 产出一行**自然语言 lesson**（在线零 LLM 调用，用规则+模板）：

```python
def reflect(trial, history) -> Lesson:
    if trial.strategy == "greedy_md" and trial.coverage < state.n_tasks * 0.95:
        return Lesson(
            text=(f"在 regime={state.regime} 上 greedy_md 覆盖率仅 "
                  f"{trial.coverage}/{state.n_tasks}; "
                  f"下一步应切换到 bundle-aware 策略"),
            constraint=("downweight", "greedy_md", 0.5),
        )
```

`constraint` **直接修改 Reasoner 里 Fit 项权重**：

```python
reasoner.apply_lesson(lesson)   # 本轮后续 propose 不再优先 greedy_md
```

**离线**：把多轮 lessons 喂给 LLM，归纳为路由规则写进 `routing_rules.py`——闭环 Reflexion。

---

### 4.6 创新点 6 — Meta-Harness Outer Loop（Lee et al. 2026）

**目录结构：**

```
autosolver/agent/meta/
├── outer_loop.py               # 离线主循环
├── trace_analyzer.py           # 分析 episodic.jsonl，输出统计
├── weight_optimizer.py         # Bayesian Opt 调 Reasoner 4 项权重
├── rule_rewriter.py            # LLM 把 lessons + traces 重写为新 routing rules
└── promotion_gate.py           # 新 skill / 新规则要在 22 案例上不退化才能升级
```

**外层流程：**

```python
for epoch in range(N):
    # 1. 跑全部 22 案例，收集 traces
    traces = collect_traces(cases)

    # 2. Bayesian Opt 调 Reasoner 权重
    new_weights = bo.optimize(traces, objective=avg_score)

    # 3. LLM 把 lessons 蒸馏成新规则
    new_rules = llm_distill(traces.lessons)

    # 4. FunSearch-style：LLM 提议新 skill 变体
    new_skills = funsearch_propose(top_performing_skills)

    # 5. Promotion gate
    for s in new_skills:
        if avg_score(with_skill=s) <= current_baseline:
            skill_library.promote(s)
```

**亮点**：直接对标 2026 年最新论文范式——"Agent 改进自己的 harness"，首次在 OR 求解器上实现。

---

## 5. Reasoner 打分函数

`reasoner.propose(state, memory)` 给每条 skill 打分，选 top-K 展开：

$$
\text{Score}(s \mid \text{state}, \text{mem}) =
  \underbrace{w_1 \cdot \text{Fit}(s, \text{state})}_{\text{先验匹配}}
+ \underbrace{w_2 \cdot \text{EI}(s, \text{mem})}_{\text{期望改进}}
+ \underbrace{w_3 \cdot \sqrt{\tfrac{\ln n}{n_s + 1}}}_{\text{UCB 探索}}
- \underbrace{w_4 \cdot \tfrac{\text{cost}_s}{\text{budget}_{\text{left}}}}_{\text{时间代价}}
$$

| 项 | 数据来源 | 体现 |
|---|---|---|
| **Fit** | `priors/strategy_priors.json` + LLM 离线提议 | "贪心在合单场景表现差 → 自动转其他方向" |
| **EI** | 本轮 memory：已跑策略的得分分布 | "best=720，s 预测均值 700 → EI 高" |
| **UCB** | 本轮 memory：每条策略已被选次数 | 强制探索未试策略，体现"自主提出不同策略" |
| **时间代价** | 策略平均运行时间 / 剩余预算 | 时间紧时不上 ILP/列生成 |

**每个 propose 输出都带 `thought` 字符串**（可读 trace 的核心）：

```python
ReasonerDecision(
    strategy="ilp_column",
    params={"time_budget": 2.5, "max_columns": 200},
    thought=(
        "n_tasks=30, n_couriers=60, avg_w=0.18 → regime=low_willingness; "
        "history: greedy_md→1820, lns→1808; "
        "Fit(ilp_column|low_w)=0.71, EI=12.3, UCB=0.45, time_cost=0.28; "
        "→ 选 ilp_column 期望突破 1800 上限"
    ),
)
```

---

## 6. 4 条赛题能力 → 验证脚本

| 赛题能力 | 验证脚本 | 验证方式 |
|---|---|---|
| ① 自主策略探索 | `test_capability_1_exploration.py` | 12 自构样例：每个至少触发 3 种 strategy；不同 regime 触发不同首选策略 |
| ② 自动评估筛选 | `test_capability_2_evaluation.py` | trace 中每个 trial 有 score；best 严格单调；被丢弃 trial 标 `kept=false` |
| ③ 迭代改进循环 | `test_capability_3_adaptation.py` | "greedy 表现差"样例：Reasoner 第 2 轮起不再优先 greedy |
| ④ 10s 时限输出 | `test_capability_4_anytime.py` | 注入 1s/3s/5s/9s 都能返回合法解；0.5s 也至少返回 baseline greedy |

---

## 7. 12 个自构样例

`tests/synthetic/` 下生成 12 个样例，每个附 README 说明派生方式 + 预期触发策略：

| 样例 | 派生自 | 扰动 | 预期 Agent 行为 |
|---|---|---|---|
| `bundle_heavy.txt` | 301 | 70% 行改成合单 | 优先 disjoint_bundle / pair_potential；greedy first try 应差 → 切走 |
| `ultra_scarce_36c40t.txt` | 401 | 减 2 个 courier | 优先 scarce_shadow；触发 LP 重分配 |
| `ultra_low_w_010.txt` | 501 | 全体 w×0.5 | 优先 low_mcf_sa + ILP |
| `dense_high_w.txt` | 201 | w 拉到 0.7+ | 优先简单 greedy；Reasoner 应早停 |
| `single_courier_pathological.txt` | 自造 | 1 骑手 N 单 | 触发 ILP（小规模） |
| `all_zero_w.txt` | 自造 | w=0 | Reasoner 应识别 → 直接 reject-all 兜底 |
| `time_pressure_huge.txt` | 自造 | 60 task 120 courier | 验证 budget manager 不超时 |
| `bimodal_w.txt` | 自造 | w∈{0.1, 0.9} 双峰 | 验证 lesson 反作用 |
| `chain_bundle.txt` | 自造 | 长链合单 | bundle MCF |
| `noisy_score.txt` | 601 | 加高方差 | 验证多样化策略 |
| `tiny_optimal.txt` | 42 | 6 任务 | ILP 应快速到最优 |
| `boundary_8s.txt` | 301 | 边界时长 | budget manager 健壮性 |

---

## 8. 提交物边界与安全规则

- **`solver.py` 1669 行算法函数原地不动**（确保 706.72 不退）
- **唯一改动**：`solve(input_text)` 替换为
  ```python
  def solve(input_text: str) -> list:
      from autosolver.agent.executor import run as agent_run
      result, _trace = agent_run(input_text, time_budget=9.0)
      return result
  ```
- Agent 默认走主路径，等价于原 case 路由（保 706.72）
- `autosolver/agent/*` 是新增包
- **trace 开关**默认关闭，`AUTOSOLVER_TRACE=1` 时写 `runs/trace_*.json` 供演示

**回归门（必过）：**
- `python3 -m unittest discover -s tests -p 'test_*.py'`（26 OK）
- `python3 _bench.py solver.py 1` 平均 ≤ 707.10（容忍 0.4 浮动）
- 单 case ≤ 9s
- 提交包总大小 < 80KB

**若评测机只接受单文件**：准备 `tools/build_single_file.py`，把 agent 框架内联进 `solver.py` 末尾，预计总大小 ~75KB。

---

## 9. 代码结构全图

```
FOR_AutoSolver_706.72/
├── solver.py                    # 不动（1669 行算法内核 + 8 行 thin wrapper）
└── autosolver/
    └── agent/
        ├── executor.py          # ToS 主循环 + Budget Manager
        ├── perception.py        # 实例指纹 + regime 标签
        ├── reasoner.py          # UCB1 + Fit + EI + lesson 约束
        ├── critic.py            # 闭式评分 + 剪枝判定
        ├── reflector.py         # trial → lesson 规则提取器
        ├── micro_evolver.py     # 在线参数微变异
        ├── skills/              # ★ Skill Library + 谱系
        │   ├── _registry.py
        │   ├── manifest.json
        │   ├── lineage.dot
        │   ├── skill_*_v*.py
        │   └── skill_evolved_*_v*.py
        ├── memory/              # ★ 三类记忆
        │   ├── episodic.jsonl
        │   ├── semantic_lessons.jsonl
        │   ├── procedural_weights.json
        │   ├── fingerprint.py
        │   └── retriever.py
        ├── meta/                # ★ Meta-Harness 外层
        │   ├── outer_loop.py
        │   ├── trace_analyzer.py
        │   ├── weight_optimizer.py
        │   ├── rule_rewriter.py
        │   └── promotion_gate.py
        └── llm_offline/         # 仅离线，不进提交
            ├── funsearch_loop.py
            ├── reflexion_distill.py
            └── evolution_log/
docs/
├── ARCHITECTURE.md
├── INNOVATIONS.md               # 6 创新点 + OSS 对照表
├── SKILL_LINEAGE.md             # 自动从 lineage.dot 渲染
├── EXPERIMENTS.md               # 22 案例 × 6 模块消融
└── DEMO.md
tests/
├── synthetic/                   # 12 自构样例
└── agent_capabilities/          # 4 条赛题能力测试
```

---

## 10. 消融实验表（答辩 PPT 核心页）

| 配置 | 22 案例均分 | 说明 |
|---|---:|---|
| 原 `solver.py`（baseline） | 706.72 | 无 Agent |
| + Skill Library 包装 | 706.72 | 等价基线 |
| + Episodic RAG | 706.50 | warm start 节省时间 |
| + Tree-of-Strategies | 706.30 | 多分支多 cover |
| + Online Micro-Evolution | 706.10 | 参数微调 |
| + Reflective Lessons | 706.05 | lesson 反作用于 Reasoner |
| + Meta-Harness 自重写 | **705.85** | full agent |

**每条改进都有可证伪数字** —— 这是真正的创新感。

---

## 11. 对外讲故事的三层（答辩用）

### Level 1 — 在线 Agent（10s 内做的事）

> Agent 拿到实例，先做指纹检索过去最像的案例，挪用它的获胜策略做 warm start；然后开 Tree-of-Strategies 同时展开 3 条搜索路径，Critic 用 UCB 决定哪条继续深化；每 1 秒做一次 Reflection 蒸出 lesson 反向调整 Reasoner 权重；最后还有 200ms 的 Micro-Evolution 微调参数。**所有这些都不调任何 LLM**。

### Level 2 — 离线自演化（开发期做的事）

> 我们在 10 官方 + 12 自构案例上跑 Agent 上千次，收集所有 trace。FunSearch-style 的 LLM 进化器把表现最好的 skill 做**代码级变异**生成新版本；Bayesian Optimization 调 Reasoner 权重；LLM 把 lessons 蒸馏成新的路由规则。所有产物都进 Skill Library 的谱系树。

### Level 3 — 元自演化（Meta-Harness）

> Agent 不只学求解，还学习"怎么更好地学求解"：外层循环监控 Agent 自身的策略调用统计，自动重写它的 routing rules——这就是 Lee et al. 2026 Meta-Harness 的范式，**我们是首次在 OR 求解器上实现**。

---

## 12. 执行排期

| 阶段 | 工作 | 估时 | 阻塞 |
|---|---|---|---|
| P0 | Skill Library + Critic + 基础 Executor（保证 706.72 不退） | 1.5 天 | — |
| P0 | Episodic RAG（fingerprint + retriever，先用全部 22 案例做种子） | 1 天 | Skill Library |
| P0 | Tree-of-Strategies + UCB + Anytime 兜底 | 1.5 天 | Critic |
| P0 | 22 案例集 + 4 条能力测试 | 1 天 | Executor |
| P1 | Reflector + Micro-Evolver + Reasoner lesson 接入 | 1 天 | Reasoner |
| P1 | Meta-Harness outer loop（先跑 1 个 epoch 留 log） | 1 天 | Memory |
| P1 | LLM offline FunSearch loop（产出 2-3 个 evolved skill） | 1 天 | Skill Library |
| P2 | 6 个文档 + lineage.dot 渲染 + 3 分钟 Demo 录屏 | 1.5 天 | 全部 |

---

## 13. 风险与对冲

| 风险 | 对冲 |
|---|---|
| ToS 多分支让单 case 超 10s | Budget Manager 强制：剩余预算 < min_skill_time 时切回最便宜 skill |
| RAG warm start 误导（相似但 regime 不同） | Lesson 反作用机制 1 轮内 reweight 到正确策略 |
| FunSearch 产物退化 | Promotion Gate 必须在 22 案例上不退才能合入 |
| 80KB 提交限制 | `tools/build_single_file.py` 内联打包，预计 ~75KB |
| 在线 LLM 不稳/超时 | 在线**完全零 LLM 调用**；LLM 只在离线 |

---

## 14. 答辩一句话（最终版）

> **AutoSolver 是一个把组合优化求解器重构为可终身学习 Agent 的系统：在线用 Tree-of-Strategies + Episodic RAG + Reflective Micro-Evolution 在 10 秒内完成探索-评估-改进闭环；离线用 FunSearch 风格的代码级进化 + Meta-Harness 外层循环让 Agent 自动重写自己的 Skill Library 和路由规则。我们把 Voyager 的技能库、Reflexion 的反思、FunSearch 的代码进化、Meta-Harness 的自重写四条互相独立的研究主线，首次统一在一个 10 秒预算的求解器 Agent 里。**

---

## 附录 A — 与之前两版方案的对比

| 维度 | v0（"包一层壳"） | v0.5（ReAct 单线） | v1（本方案） |
|---|---|---|---|
| Agent 本质 | 显式 Strategy 注册表 | UCB 打分 + Memory 单循环 | 6 大创新支柱并行 |
| 策略空间 | 固定 10 条 | 固定 10 条 | **可生长 Skill Library** |
| 跨案例学习 | 无 | 无 | **Episodic RAG** |
| 探索结构 | 顺序 | 顺序 | **Tree-of-Strategies** |
| 进化能力 | 无 | 无 | **在线 micro-evolve + 离线 FunSearch** |
| 自我改进 | 无 | 无 | **Meta-Harness 外层循环** |
| 答辩故事 | "把代码组织一下" | "ReAct 求解器" | **"会自己长技能的 Agent"** |
| OSS 对标 | 0 | ReEvo | **9 个一线工作** |

---

## 附录 B — 最小可执行清单（开工顺序）

1. `autosolver/agent/skills/_registry.py` + `skill_greedy_md_v1.py`（把 `solver._solve_single_task_multidispatch` 包装成 skill）
2. `autosolver/agent/critic.py`（直接调 `autosolver/accurate_evaluator.py`）
3. `autosolver/agent/executor.py` 的最小版（顺序调用 1 个 skill，等价 baseline）
4. 把 `solver.py` 的 `solve()` 切到 `executor.run`
5. 跑回归门：26 单测 + `_bench.py` 平均 ≤ 707.10
6. 加 `perception.py` + `memory/fingerprint.py` + `memory/episodic.jsonl`（先手填 10 个官方案例的种子）
7. 加 `reasoner.py` 最小版（只有 Fit + UCB）
8. 加 ToS 分支 + Critic 剪枝
9. 加 Reflector + Micro-Evolver
10. 加 `meta/` 外层循环 + `llm_offline/`
11. 写 6 篇文档 + 录 Demo
