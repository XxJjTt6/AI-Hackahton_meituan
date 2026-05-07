# Solver variants

这些文件都可以单独改名为 `solver.py` 后提交。

1. `solver_best_1_balanced.py`: 当前综合版，低意愿合单 lookahead=5，小稀缺 beam=12000。
2. `solver_best_2_safe_time.py`: 更保守的耗时版，小稀缺 beam 降到 5000。
3. `solver_best_3_conservative_low.py`: 低意愿阈值 0.22，避免误触发合单低意愿分支。
4. `solver_best_4_aggressive_low.py`: 低意愿阈值 0.29，更容易触发合单分支。
5. `solver_best_5_no_random.py`: 禁用充足骑手随机初解，速度更稳，分数略保守。

本地代理验证（`large_seed301` 派生）：

| 版本 | orig | low proxy | scarce20 proxy | 备注 |
|---|---:|---:|---:|---|
| best_1 | 657.81 | 2421.09 | 1702.47 | 首选 |
| best_2 | 657.81 | 2421.09 | 1764.32 | 稀缺更快但分数略差 |
| best_3 | 657.81 | 2421.09 | 1702.47 | 低意愿阈值更保守 |
| best_4 | 657.81 | 2421.09 | 1702.47 | 低意愿阈值更激进 |
| best_5 | 657.96 | 2421.09 | 1702.47 | 速度更稳 |
