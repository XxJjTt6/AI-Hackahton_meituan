# AutoSolver

AutoSolver 是按 `AutoSolver 项目实施方案（V5 收口版）` 实现的组合优化求解器。在线路径不依赖 LLM，也不依赖第三方 Python 包；核心目标是在给定时间预算内生成合法分配，并通过统一目标函数比较候选解。

## V5 六处修正

- `autosolver/objective.py`：所有 solver 统一调用 `objective` / `better` / `marginal_objective_gain`。
- `autosolver/candidate_gen.py`：合单候选按 bundle 内 `base_p = min(p[order, rider])` 选择 top-k 骑手。
- `autosolver/fallback.py`：`fallback_1_top_p` 按订单最大概率排序，并用 `SolverState.rider_compatible` 检查骑手时间冲突。
- `autosolver/main.py`：adapter 前后分阶段 `try/except`，adapter 失败才走 `_emergency_raw_output`。
- `autosolver/utils/seed.py`：使用 `hashlib.sha256` 派生跨进程稳定 seed。
- `autosolver/walkthrough.py`：walkthrough baseline expected accepts 固定为 `0.8 + 0.57 + 0.57 = 1.94`。

## 运行样例

```bash
python3 -m autosolver.main --input examples/walkthrough_input.json --output /tmp/autosolver_output.json --time-budget 2
cat /tmp/autosolver_output.json
```

也可以从 stdin/stdout 运行：

```bash
python3 -m autosolver.main < examples/walkthrough_input.json
```

开启 debug trace：

```bash
python3 -m autosolver.main -i examples/walkthrough_input.json --debug
```

## 运行测试

项目测试使用 Python 标准库 `unittest`，不依赖第三方测试框架：

```bash
python3 -m compileall autosolver tests
python3 -m unittest discover -s tests -p 'test_*.py'
```


## Python API

```python
from autosolver.submission import run

output = run(raw_input, time_budget=10.0)
```

`run` 始终返回 submit-clean 输出，不包含 debug 字段。

## 输入格式

```json
{
  "id": "case-id",
  "orders": [
    {"id": "O1", "pickup": [0, 0], "dropoff": [1, 0], "ready_time": 0, "due_time": 20, "score": 10}
  ],
  "riders": [{"id": "R1"}],
  "p_matrix": [[0.8]],
  "score_direction": "reward",
  "weights": {"expected_accepts": 1.0, "score": 0.5}
}
```

## 输出格式

```json
{
  "assignments": [
    {"order_id": "O1", "rider_ids": ["R1"], "is_multi_dispatch": false, "is_bundle": false}
  ],
  "rejected": []
}
```
