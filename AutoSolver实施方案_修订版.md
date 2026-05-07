# AutoSolver 项目实施方案（修订版）

> 本方案根据老师反馈重新整理。核心变化：**LLM 离线化、评估器闭式化、合单候选化、技术栈瘦身**。
>
> 一句话定位：**这是一个可自主选择策略、自动评估候选解、在时间预算内持续改进的组合优化 AutoSolver**。LLM 是"策略生成器/解释器"，真正的得分能力来自**评估器 + 启发式搜索 + 合单建模**。

---

## 一、问题重新形式化

### 1.1 必须先向主办方确认的事

赛题描述存在两处歧义，**报名后立刻发邮件确认**，否则全套排序规则会做反：

1. **`score` 的方向**：题面前段说"最大化系统收益（以分数表示）"，后段又说"总分数最小化"。需要确认 `score[i,j]` 是收益还是成本。
2. **双目标的权衡方式**：是加权和、字典序（先最大化接单数再优化分数），还是 Pareto 前沿。
3. **合单的得分规则**：合单分数是各订单分数之和，还是有合并加成 / 折扣？
4. **概率独立性**：不同骑手对同一订单的接单事件是否独立？

> 在确认前，方案里所有"成本/收益"用 `score` 占位，并保留两个方向的实现开关。

### 1.2 数学模型（修正版）

**核心修正**：题目允许"一单派多骑手抢，最先接起者得到订单"，所以**期望接单数不是线性的**，必须用闭式概率：

订单 `i` 派给骑手集合 `R_i`，假设各骑手接单事件独立：

```
P(订单 i 被接起) = 1 - ∏_{j ∈ R_i} (1 - p[i,j])
E[接单数]       = Σ_i [1 - ∏_{j ∈ R_i} (1 - p[i,j])]
```

例：订单派给两个 `p=0.8` 的骑手，接单概率不是 `1.6`，而是 `1 - 0.2×0.2 = 0.96`。这是 GAP 的标准近似无法处理的非线性。

**因此 ILP 不能直接写 `Σ p[i,j] x[i,j]`**，必须改建模方式（见 § 三）。

### 1.3 把"订单-骑手分配"改成"任务选择"

老师指出的关键改造：把合单从后处理升级为一等公民。

```
原子任务 task_k = {
    orders:      [order_id1, order_id2, ...],   # 1 个或多个订单
    rider_id:    j,
    probability: p_k,                            # 该骑手接这个任务的概率
    score:       s_k,                            # 该任务的收益或成本
    feasibility: bool                            # 时间窗、距离、容量是否满足
}
```

**求解过程不再是"为订单 i 选骑手 j"，而是"在候选任务集合里选若干个互不冲突的可行任务"**。冲突约束有三类：
- 同一订单不能在两个被选中的"独占型"任务里出现（除非允许多骑手抢）
- 同一骑手在时间上不能被两个任务占满
- 合单任务的内部约束（路径顺序、配送时间）

这个抽象让后续所有求解器（Greedy / 列生成 / LNS）都能复用同一套候选集。

---

## 二、整体架构（修订版）

老师反馈最重要的一条：**LLM 不要在线参与每一轮决策**。改成离线 + 在线分离：

```
═══════════ 离线阶段（开发期 / 训练期）═══════════
LLM (ReEvo / EoH 风格)
  ↓ 生成候选启发式（排序规则、邻域算子、修复策略）
评估器在历史实例集上筛选
  ↓
固化为策略库 strategies.py
═══════════ 在线阶段（10 秒/用例 评测期）═══════════
不调用 LLM，只跑确定性策略库
  ↓
Instance Analyzer → Candidate Generator → Baseline → Improver → Evaluator → Auto Policy Controller
```

### 2.1 在线流程（这才是真正会被评测的代码）

```
输入数据
   ↓
[1] Instance Analyzer
    分析订单数、骑手数、概率矩阵稀疏度、合单密度
   ↓
[2] Candidate Generator
    生成 单订单-骑手候选 + 合单-骑手候选
   ↓
[3] Baseline Solver
    快速 Greedy，0.1–0.5 秒内保底有可行解
   ↓
[4] Improver
    LNS / 局部交换 / 删除重插入 / 多派单调整
   ↓
[5] Evaluator
    闭式期望接单数 + 分数目标 + 合法性
   ↓
[6] Auto Policy Controller
    根据剩余时间选择继续搜索 / 切换策略 / 停止
   ↓
输出最优解
```

### 2.2 Agent 自主性的三层定义（落地版）

老师指出"自主性不能停留在口号"。把它拆成三层，**正式比赛实现 L1 + L2，L3 留作展示亮点**：

| 层级 | 自主能力 | 实现方式 | 是否进比赛主流程 |
|------|---------|---------|---------------|
| L1 策略选择 | 根据实例特征选 Greedy / 列生成 / LNS | 离线训练的决策树或规则表 | ✅ 必做 |
| L2 参数调整 | 自动调 top_k、destroy_ratio、时间预算分配 | 实例特征 → 参数映射表 | ✅ 必做 |
| L3 启发式生成 | LLM 离线生成新排序规则 / 邻域算子 | ReEvo / EoH 离线进化 | 🟡 加分项，离线产出后固化 |

---

## 三、模块详细设计

### 3.1 Evaluator（最先做，最关键）

**改用闭式期望，不用蒙特卡洛**。蒙特卡洛只作为单元测试的对照工具。

```python
import numpy as np

def evaluate(solution, instance):
    """
    solution: List[Task]  被选中的任务列表
    返回: dict {
        'expected_accepts': float,
        'total_score':      float,
        'feasible':         bool,
        'violations':       list
    }
    """
    # 1. 合法性
    violations = check_conflicts(solution, instance)
    if violations:
        return {'feasible': False, 'violations': violations,
                'expected_accepts': 0, 'total_score': float('inf')}

    # 2. 按订单聚合：order_id -> [(rider, p), ...]
    order_to_assigns = {}
    for task in solution:
        for oid in task.orders:
            order_to_assigns.setdefault(oid, []).append((task.rider_id, task.probability))

    # 3. 闭式期望接单数
    expected_accepts = 0.0
    for oid, assigns in order_to_assigns.items():
        prob_not_taken = np.prod([1 - p for _, p in assigns])
        expected_accepts += 1 - prob_not_taken

    # 4. 期望分数（含被接起才计分的概率加权）
    total_score = sum(t.score * t.probability for t in solution)  # 视主办方定义调整

    return {'feasible': True, 'violations': [],
            'expected_accepts': expected_accepts,
            'total_score': total_score}
```

**性能要点**：用 numpy 向量化、numba `@jit` 装饰核心循环、概率矩阵预计算 `log(1-p)` 用加法代替乘法避免下溢。

### 3.2 Candidate Generator（合单建模的落地）

```python
def generate_candidates(instance, max_bundle_size=3):
    candidates = []

    # 单订单候选
    for i in instance.orders:
        for j in instance.riders:
            if feasible_single(i, j):
                candidates.append(Task(
                    orders=[i],
                    rider_id=j,
                    probability=instance.p[i, j],
                    score=instance.s[i, j],
                ))

    # 合单候选：先用空间聚类筛选可能合单的订单组
    bundle_groups = cluster_orders_by_proximity(
        instance.orders,
        max_size=max_bundle_size,
        max_detour=instance.max_detour,
    )
    for group in bundle_groups:
        for j in instance.riders:
            if feasible_bundle(group, j, instance):
                p_bundle, s_bundle = bundle_metrics(group, j, instance)
                candidates.append(Task(
                    orders=group,
                    rider_id=j,
                    probability=p_bundle,
                    score=s_bundle,
                ))

    return candidates
```

**关键工程细节**：
- 不要枚举所有合单组合，会爆炸（C(n,3) 在 n=50 已经 ~2 万）
- 用 KD-Tree 或网格法做空间剪枝，只保留"取餐点距离 < 阈值"且"送餐点方向一致"的组合
- `bundle_metrics` 里的合单概率，可以用主办方给的预计算分数反推，或用骑手对各单 p 的几何/算术平均

### 3.3 求解策略池（修订版）

去掉 LLM Direct，ILP 限定小规模用列选择，主力是 Greedy + LNS：

#### Strategy A：边际收益贪心（主力 baseline）

注意是**边际**，因为多派单的收益非线性：

```python
def greedy_marginal(candidates, instance, time_budget=0.5):
    selected = []
    remaining = candidates.copy()

    while remaining and within_budget(time_budget):
        # 计算每个候选任务的边际期望接单收益
        best_task, best_gain = None, -float('inf')
        for task in remaining:
            gain = marginal_gain(task, selected, instance)
            if gain > best_gain and not conflicts_with(task, selected):
                best_gain = gain
                best_task = task

        if best_task is None or best_gain <= 0:
            break
        selected.append(best_task)
        remaining = [t for t in remaining if compatible(t, best_task)]

    return selected
```

边际收益 `marginal_gain` 的计算就是利用闭式公式增量：把这个任务加入后期望接单数的提升，减去任何分数代价。

#### Strategy B：列生成 / 枚举（小规模专用）

老师的建议：把"派给某个骑手子集"作为候选列。当订单数 ≤ 30 时可用：

```python
def column_selection_solver(candidates, instance, time_limit=3):
    # 候选列 = 每个 (订单子集, 骑手) 组合
    # 决策变量 = 是否选中每个候选列
    # 约束: 每个订单至多被一个候选列覆盖（如果是独占）
    #       每个骑手的容量约束
    import pulp
    prob = pulp.LpProblem("auto_solver", pulp.LpMaximize)
    x = {k: pulp.LpVariable(f"x_{k}", cat="Binary") for k in range(len(candidates))}

    # 目标：用线性近似 - 期望接单数（先按 p[k] 一阶近似，再用增量修正）
    prob += pulp.lpSum(candidates[k].probability * x[k] for k in x)

    # 约束略
    solver = pulp.HiGHS_CMD(timeLimit=time_limit, msg=False)
    prob.solve(solver)
    return [candidates[k] for k in x if x[k].value() > 0.5]
```

> 注意：因为非线性，这只是个上界近似，**结果必须再回到闭式 evaluator 复核**。

#### Strategy C：LNS（中大规模主力）

```python
def lns_improve(initial_solution, candidates, instance, time_budget):
    current = initial_solution
    best = current
    T = 1.0  # 模拟退火温度

    while within_budget(time_budget):
        # 1. Destroy: 随机移除 ratio 比例的任务
        ratio = adaptive_destroy_ratio(instance)  # L2 自主调参点
        partial = destroy(current, ratio)

        # 2. Repair: 用边际贪心补回
        repaired = greedy_marginal_repair(partial, candidates, instance)

        # 3. Accept: 模拟退火准则
        if accept(repaired, current, T):
            current = repaired
            if better(current, best):
                best = current

        T *= 0.995

    return best
```

### 3.4 Auto Policy Controller（L1 + L2 自主性的落点）

```python
class AutoPolicyController:
    def select_strategy(self, instance, remaining_time):
        feat = instance_features(instance)
        # L1: 策略选择
        if feat.n_orders <= 25 and remaining_time > 4:
            primary = "column_selection"
        elif feat.density > 0.7:           # 概率矩阵稠密
            primary = "lns"
        else:
            primary = "greedy_marginal"

        # L2: 参数调整
        params = {
            "destroy_ratio": 0.2 + 0.3 * feat.density,
            "max_bundle_size": 3 if feat.spatial_clustering else 2,
            "time_budget": remaining_time * 0.85,
        }
        return primary, params
```

这个 Controller 的规则可以是手写决策树，也可以离线用一个小模型（XGBoost）从历史实例上学到。**两种都不调用 LLM，确保在线确定性**。

### 3.5 LLM 在哪里？（离线阶段）

参考 ReEvo 的做法，**在开发期**让 LLM 干这些事，产出固化代码：

1. **生成排序启发式**：让 LLM 提出 5–10 种边际收益排序公式（如"按 p×s 排"、"按 p×s/距离排"、"按合单潜力排"），用历史实例打分，选出 top-3 写进 `strategies.py`
2. **生成 LNS 邻域算子**：让 LLM 提出不同的 destroy/repair 策略
3. **生成实例特征 → 策略的映射规则**：让 LLM 看一批历史实例和最优策略，归纳决策规则

**关键**：这些产出是**普通 Python 函数**，比赛时直接 import，不依赖任何 LLM API。

---

## 四、技术栈（瘦身版）

| 层 | 选型 | 原因 |
|---|---|---|
| 求解器 | PuLP + HiGHS | 开源、纯 Python 安装无依赖问题 |
| 数值计算 | numpy + numba | 闭式期望评估器加速 |
| 空间索引 | scipy.spatial.KDTree | 合单候选剪枝 |
| 离线 LLM | LiteLLM + DeepSeek-V3 | 性价比最高，仅在开发期用 |
| 离线进化框架 | fork ReEvo 改造 | 仅在开发期用 |
| 配置 | 一个 yaml 文件 | 不引入 Hydra，简化 |

**已删除**：Cython（用 numba 替代，零编译麻烦）、Hydra（杀鸡用牛刀）、LLM Direct Reasoning（线上不稳）。

---

## 五、实施时间表（修订版）

### Week 1：核心三件套（必须跑通）

| Day | 任务 | 产出 |
|-----|------|------|
| 1 | 数据 schema + Instance / Task 数据类 | `models.py` |
| 1 | 给主办方发邮件确认 score 方向 | 邮件 |
| 2 | 闭式期望 Evaluator + 单元测试（用蒙特卡洛对照） | `evaluator.py` |
| 3 | Candidate Generator（含单订单 + 合单） | `candidate_gen.py` |
| 4 | 边际收益 Greedy | `solvers/greedy.py` |
| 5 | LNS（destroy + repair + 模拟退火） | `solvers/lns.py` |

### Week 2：自主性 + 调参

| Day | 任务 | 产出 |
|-----|------|------|
| 6 | Instance Analyzer + 特征提取 | `analyzer.py` |
| 7 | Auto Policy Controller（L1 + L2） | `controller.py` |
| 8 | 列生成/枚举求解器（小规模） | `solvers/column.py` |
| 9 | 集成端到端 + 时间预算管理 | `main.py` |
| 10 | 历史实例集合上调参 | 参数表 |

### Week 3：离线 LLM + 提交

| Day | 任务 | 产出 |
|-----|------|------|
| 11 | fork ReEvo，配好离线进化管道 | 离线工具 |
| 12 | LLM 生成候选启发式 + 评估器筛选 | 新策略入策略库 |
| 13 | 性能优化（numba、向量化、缓存） | 提速 |
| 14 | 文档、提交、demo 录制 | 交付 |

---

## 六、参考开源项目（修订版）

按对你的实际价值排序，**前两个是离线阶段的核心参考**，后面是设计思路启发：

| 项目 | 用途 | 何时用 |
|---|---|---|
| **ai4co/reevo** (NeurIPS 2024) | 离线进化启发式的代码骨架 | Week 3 离线阶段 |
| **FeiLiu36/EoH** (ICML 2024) | 思想 + 代码协同进化范式 | Week 3 离线阶段 |
| **OR-Tools / PyVRP** | VRP/GAP 工业级求解参考 | Week 1–2 借鉴建模 |
| **AFL** (arxiv 2510.16701) | 全自动 VRP Agent 论文 | 设计 Auto Policy Controller 时参考 |
| **HeuriGym** (ICLR 2026) | LLM agent 在 CO 的评测框架 | demo 演示时引用 |

---

## 七、容易踩的坑（老师反馈整合版）

| # | 坑 | 规避方法 |
|---|---|---------|
| 1 | score 方向理解反 | 主办方确认前，在配置里留方向开关，所有排序乘以 `±1` 通过开关切换 |
| 2 | 在线依赖 LLM 导致超时 | LLM 只在离线，正式提交是确定性代码 |
| 3 | 蒙特卡洛慢且不可复现 | 用闭式期望，蒙特卡洛仅做单元测试 |
| 4 | 合单后处理化 | 合单作为一等候选任务参与求解 |
| 5 | ILP 写成线性 GAP | 多骑手抢单非线性，用列选择/枚举 + 闭式复核 |
| 6 | 自主性流于口号 | L1/L2/L3 三层落地到具体代码模块 |
| 7 | 不知道何时停止 | 时间预算 85% 分给搜索，15% 给输出和兜底 |
| 8 | 拒单不敢用 | 拒掉低 p 低 s 订单往往让总解更优，要敢拒 |

---

## 八、立项姿态（对外讲故事的方式）

不要主打"我用了多复杂的 LLM Agent"，主打：

> **AutoSolver 是一个可自主选择策略、自动评估候选解、在 10 秒预算内持续改进的组合优化系统。**
>
> - **离线**：用 LLM 进化启发式策略，固化为策略库
> - **在线**：根据实例特征自动路由策略 + 自动调参 + 闭式期望评估 + LNS 持续改进
> - **创新点**：把"多骑手抢单"和"合单"统一抽象为候选任务，复用同一套求解框架

这样既体现 Agent 的"自主"卖点，又不把比赛分数押在 LLM 在线调用的稳定性上。

---

## 九、最小提交清单

提交时的代码结构建议：

```
autosolver/
├── main.py                    # 入口，10 秒预算管理
├── models.py                  # Instance / Task / Solution 数据类
├── analyzer.py                # 实例特征提取
├── candidate_gen.py           # 候选任务生成（含合单）
├── evaluator.py               # 闭式期望评估器
├── controller.py              # Auto Policy Controller (L1+L2)
├── solvers/
│   ├── greedy.py              # 边际收益贪心
│   ├── lns.py                 # LNS
│   └── column.py              # 小规模列选择
├── strategies.py              # 离线 LLM 产出的启发式（普通函数）
├── config.yaml                # 参数 + score 方向开关
├── tests/                     # 闭式 vs 蒙特卡洛对照、合法性测试
└── README.md                  # 系统说明 + Agent 自主性的三层论述
```

---

## 附：与原方案的主要差异对照

| 维度 | 原方案 | 修订版 |
|-----|-------|-------|
| LLM 角色 | 在线每轮决策 | 仅离线生成启发式 |
| 评估器 | 蒙特卡洛 (n=50–1000) | 闭式期望公式 |
| 合单 | 后处理 / 模糊 | 一等公民候选任务 |
| ILP | 线性 GAP | 列选择 + 闭式复核 |
| 求解策略 | 4 个并列 | 1 主 (Greedy+LNS) + 1 专 (列选择) |
| 自主性 | 口号化 | L1/L2/L3 三层落地 |
| 技术栈 | 9 个工具 | 5 个核心工具 |
| 主打卖点 | 复杂 LLM Agent | 稳健的自动化求解器 + LLM 加速开发 |
