from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from autosolver_agent.evolution import EvolutionManager, GeneratedStrategy
from tools.agent_trace_demo import infer_regime, load_solver, parse_candidates, summarize_solution


ROOT = Path(__file__).resolve().parents[1]
SOLVER_PATH = ROOT / "solver.py"
EVOLUTION_ROOT = ROOT / "autosolver_agent" / "evolution_state"


AGENT_BLUEPRINT = {
    "name": "AutoSolver Autonomous Strategy Agent",
    "objective": "在 10 秒测试预算内，自主探索多种配送分配策略，用内部 Critic 做接受/拒绝筛选，并输出当前最优合法方案。",
    "capabilities": [
        {
            "id": "perception",
            "title": "场景感知",
            "description": "解析任务、骑手、意愿、bundle 与稀缺度，自动识别 large / scarce / low-willingness 等 regime。",
        },
        {
            "id": "exploration",
            "title": "自主策略探索",
            "description": "不由人工指定单一算法，自动尝试 greedy、multi-dispatch、pair matching、sparse cover、column-style search 和 production solver。",
        },
        {
            "id": "critic",
            "title": "自动评估与筛选",
            "description": "每个候选解都经过同一 Critic 判断；网页只展示接受/拒绝和后续动作。",
        },
        {
            "id": "adaptation",
            "title": "迭代改进循环",
            "description": "根据上一轮接受/拒绝结果和 regime 调整下一轮策略，例如低意愿转向 low column，骑手稀缺转向 scarce bundle。",
        },
        {
            "id": "anytime",
            "title": "限时输出",
            "description": "每个策略都有时间片，接近预算时停止扩展，直接输出当前最优分配方案。",
        },
        {
            "id": "self_evolution",
            "title": "自进化策略生成",
            "description": "生成实验 Python 策略，经过安全检查、限时试跑、Critic 筛选；失败自动回退，成功写入策略记忆。",
        },
    ],
}


@dataclass(frozen=True)
class StrategyAttempt:
    name: str
    label: str
    reason: str
    runner: Callable[[Any, list, set[str], list, float], list[tuple[str, list[str]]]]
    time_slice_s: float = 0.5


def get_agent_blueprint() -> dict[str, Any]:
    return {
        **AGENT_BLUEPRINT,
        "strategy_catalog": [
            {"id": "greedy_baseline", "label": "贪心基线", "type": "baseline"},
            {"id": "single_multidispatch", "label": "单任务多派", "type": "heuristic"},
            {"id": "disjoint_gain", "label": "启发式 Gain", "type": "heuristic"},
            {"id": "pair_matching", "label": "Pair Matching", "type": "matching"},
            {"id": "sparse_cover", "label": "稀疏覆盖", "type": "set-cover"},
            {"id": "low_global_column", "label": "低意愿全局列搜索", "type": "column-search"},
            {"id": "scarce_k2_column", "label": "Scarce K2 Column", "type": "column-search"},
            {"id": "scarce_bundle_mcf", "label": "Scarce Bundle MCF", "type": "flow"},
            {"id": "production_solver", "label": "生产级综合求解器", "type": "anytime-portfolio"},
        ],
    }


def _singles(candidates: list[tuple[str, tuple[str, ...], str, float, float, int]]) -> list:
    return [row for row in candidates if len(row[1]) == 1]


def _score(module: Any, solution: list[tuple[str, list[str]]], candidates: list, all_tasks: set[str]) -> float:
    return float(module._solution_expected_cost(solution, candidates, all_tasks))


def _solution_record(
    module: Any,
    solution: list[tuple[str, list[str]]],
    candidates: list,
    all_tasks: set[str],
) -> dict[str, Any]:
    score = _score(module, solution, candidates, all_tasks)
    summary = summarize_solution(solution, candidates, all_tasks, score)
    return {
        "local_cost": score,
        "valid": bool(summary["valid"]),
        "covered_tasks": int(summary["covered_tasks"]),
        "total_tasks": int(summary["total_tasks"]),
        "groups": int(summary["groups"]),
        "used_couriers": int(summary["used_couriers"]),
        "uncovered_tasks": list(summary["uncovered_tasks"]),
        "riders_per_group": summary["riders_per_group"],
        "tasks_per_group": summary["tasks_per_group"],
        "invalid_reasons": summary["invalid_reasons"],
    }


def _run_greedy(module: Any, candidates: list, all_tasks: set[str], history: list, deadline: float) -> list:
    return module._fallback_official_greedy(candidates)


def _run_single(module: Any, candidates: list, all_tasks: set[str], history: list, deadline: float) -> list:
    rows = _singles(candidates)
    return module._solve_single_task_multidispatch(rows, all_tasks) if rows else []


def _run_disjoint(mode: str) -> Callable[[Any, list, set[str], list, float], list]:
    def runner(module: Any, candidates: list, all_tasks: set[str], history: list, deadline: float) -> list:
        return module._solve_disjoint_then_multidispatch(candidates, all_tasks, mode=mode, deadline=deadline)

    return runner


def _run_pair(module: Any, candidates: list, all_tasks: set[str], history: list, deadline: float) -> list:
    return module._solve_pair_potential_matching(candidates, all_tasks, deadline, lookahead=5, flexible_initial=True)


def _run_sparse(module: Any, candidates: list, all_tasks: set[str], history: list, deadline: float) -> list:
    return module._solve_sparse_cover(candidates, all_tasks, deadline)


def _run_low_global(module: Any, candidates: list, all_tasks: set[str], history: list, deadline: float) -> list:
    return module._solve_low_global_column_search(candidates, all_tasks, deadline)


def _run_low_column(module: Any, candidates: list, all_tasks: set[str], history: list, deadline: float) -> list:
    rows = _singles(candidates)
    return module._solve_low_column_search(rows, all_tasks, deadline) if rows else []


def _run_scarce_k2(module: Any, candidates: list, all_tasks: set[str], history: list, deadline: float) -> list:
    return module._solve_scarce_k2_column_search(candidates, all_tasks, deadline)


def _run_scarce_bundle(module: Any, candidates: list, all_tasks: set[str], history: list, deadline: float) -> list:
    return module._solve_scarce_bundle_mcf_enum(candidates, all_tasks, deadline)


def _run_production(module: Any, candidates: list, all_tasks: set[str], history: list, deadline: float) -> list:
    input_text = history[0]["input_text"]
    return module.solve(input_text)


def _initial_strategies(regime: str) -> list[StrategyAttempt]:
    strategies = [
        StrategyAttempt("greedy_baseline", "贪心基线", "先用最快贪心获得可行基线。", _run_greedy, 0.1),
        StrategyAttempt("single_multidispatch", "单任务多派", "尝试只用单任务行做多骑手派单。", _run_single, 0.2),
        StrategyAttempt("disjoint_gain", "启发式 Gain", "按边际收益构造互斥任务组。", _run_disjoint("gain"), 0.45),
    ]
    if regime in {"large", "medium", "small"}:
        strategies.append(StrategyAttempt("pair_matching", "Pair Matching", "当前场景包含 bundle，优先尝试二元组匹配。", _run_pair, 0.65))
    if regime in {"scarce", "low-willingness"}:
        strategies.append(StrategyAttempt("sparse_cover", "稀疏覆盖", "资源紧张或低意愿时先找高收益覆盖。", _run_sparse, 0.55))
    return strategies


def _adaptive_strategies(regime: str, best_name: str | None, best_coverage: int, total_tasks: int) -> tuple[str, list[StrategyAttempt]]:
    if regime == "low-willingness":
        return (
            "发现低意愿场景，下一轮转向低意愿专用 column search，避免继续堆叠普通贪心。",
            [
                StrategyAttempt("low_global_column", "低意愿全局列搜索", "为低接受率 case 构造全局候选列。", _run_low_global, 0.7),
                StrategyAttempt("low_single_column", "低意愿单列搜索", "从单任务候选中寻找更稳的多派结构。", _run_low_column, 0.6),
            ],
        )
    if regime == "scarce":
        reason = "发现骑手稀缺，下一轮转向 scarce 专用 K2/Bundle 搜索，并允许少量未覆盖以降低期望成本。"
        return (
            reason,
            [
                StrategyAttempt("scarce_k2_column", "Scarce K2 Column", "在骑手稀缺时搜索二任务组合列。", _run_scarce_k2, 0.7),
                StrategyAttempt("scarce_bundle_mcf", "Scarce Bundle MCF", "用小规模流模型重组稀缺骑手 bundle。", _run_scarce_bundle, 0.8),
            ],
        )
    if best_coverage < total_tasks:
        return (
            "当前最优解未完全覆盖任务，下一轮转向 sparse cover 和 pair matching 提升覆盖。",
            [
                StrategyAttempt("sparse_cover", "稀疏覆盖", "补足未覆盖任务，同时保留正收益组。", _run_sparse, 0.55),
                StrategyAttempt("pair_matching", "Pair Matching", "用二元匹配补充普通启发式遗漏。", _run_pair, 0.65),
            ],
        )
    return (
        f"当前最优来自 {best_name or 'baseline'} 且覆盖完整，下一轮调用生产级求解器做综合搜索与局部改进。",
        [StrategyAttempt("production_solver", "生产级综合求解器", "调用 solver.py 中完整 10 秒内 anytime 搜索链。", _run_production, 8.7)],
    )


def run_agent(
    input_text: str,
    case_id: str = "custom",
    budget_s: float = 10.0,
    observer: Callable[[dict[str, Any]], None] | None = None,
) -> dict[str, Any]:
    started = time.monotonic()
    deadline = started + max(1.0, budget_s)
    candidates, all_tasks = parse_candidates(input_text)
    module = load_solver(SOLVER_PATH)
    regime = infer_regime(candidates, all_tasks)
    features = {
        "tasks": len(all_tasks),
        "couriers": len({row[2] for row in candidates}),
        "rows": len(candidates),
        "avg_willingness": round(sum(row[4] for row in candidates) / len(candidates), 6) if candidates else 0.0,
        "has_bundles": any(len(row[1]) > 1 for row in candidates),
    }
    case_profile = {"regime": regime, **features}

    context = [{"input_text": input_text}]
    rounds: list[dict[str, Any]] = []
    events: list[dict[str, Any]] = []

    def emit(event: dict[str, Any]) -> None:
        event = {"time_s": round(time.monotonic() - started, 3), **event}
        events.append(event)
        if observer is not None:
            observer(event)

    def evolution_helpers() -> dict[str, Any]:
        return {
            "fallback_greedy": module._fallback_official_greedy,
            "time_left": lambda target_deadline: max(0.0, target_deadline - time.monotonic()),
        }

    evolution = EvolutionManager(EVOLUTION_ROOT)

    emit({"type": "perception", "message": f"识别为 {regime} 场景", "features": features})
    emit(
        {
            "type": "critic_policy",
            "message": "Critic 只向页面输出接受/拒绝判断；内部排序信号不作为展示结论。",
        }
    )
    trusted = evolution.trusted_strategies(regime, case_profile)
    if trusted:
        emit(
            {
                "type": "evolution_recall",
                "message": f"从 Evolution Memory 检索到 {len(trusted)} 个相似历史策略，Planner 会优先复用最相近候选。",
                "strategies": [item["strategy_id"] for item in trusted[:3]],
                "similarity": [item.get("similarity", 0.0) for item in trusted[:3]],
            }
        )
    generated_strategy = evolution.generate_strategy(regime, f"run_agent:{case_id}:best-so-far experiment", case_profile)
    emit(
        {
            "type": "evolution_generate",
            "message": f"生成实验策略 {generated_strategy.strategy_id}，先进入实验轨道，不修改 solver.py。",
            "strategy_id": generated_strategy.strategy_id,
        }
    )
    safety = evolution.safety_check(generated_strategy.path, generated_strategy.strategy_id)
    emit(
        {
            "type": "evolution_validate",
            "message": f"安全门禁 {'通过' if safety.passed else '拒绝'}：{safety.reason}。",
            "strategy_id": generated_strategy.strategy_id,
            "passed": safety.passed,
        }
    )
    best_solution: list[tuple[str, list[str]]] = []
    best_record: dict[str, Any] | None = None
    best_strategy: str | None = None

    strategy_rounds: list[tuple[str, list[StrategyAttempt]]] = [
        ("initial diverse exploration", _initial_strategies(regime))
    ]
    adaptive_added = False
    round_index = 0
    while strategy_rounds and time.monotonic() < deadline - 0.2 and round_index < 3:
        round_index += 1
        reason, strategies = strategy_rounds.pop(0)
        round_payload = {"round": round_index, "reason": reason, "strategies": []}
        emit(
            {
                "type": "round_start",
                "round": round_index,
                "message": reason,
                "strategies": [strategy.name for strategy in strategies],
            }
        )
        for strategy in strategies:
            if time.monotonic() >= deadline - 0.35:
                emit({"type": "budget", "message": "接近时间限制，停止继续尝试新策略。"})
                break
            if strategy.name == "production_solver" and time.monotonic() > started + 1.5 and regime == "low-willingness":
                emit({"type": "budget", "message": "低意愿场景已接近生产求解器风险窗口，跳过完整求解器以守住 10 秒。"})
                continue
            attempt_started = time.monotonic()
            emit(
                {
                    "type": "attempt_start",
                    "round": round_index,
                    "strategy": strategy.name,
                    "label": strategy.label,
                    "message": strategy.reason,
                    "time_slice_s": strategy.time_slice_s,
                }
            )
            try:
                remaining = max(0.05, deadline - time.monotonic() - 0.2)
                local_deadline = time.monotonic() + min(strategy.time_slice_s, remaining)
                solution = strategy.runner(module, candidates, all_tasks, context, local_deadline)
                record = _solution_record(module, solution, candidates, all_tasks)
                error = None
            except Exception as exc:  # demo controller must keep the loop alive.
                solution = []
                record = {
                    "local_cost": float("inf"),
                    "valid": False,
                    "covered_tasks": 0,
                    "total_tasks": len(all_tasks),
                    "groups": 0,
                    "used_couriers": 0,
                    "uncovered_tasks": sorted(all_tasks),
                    "riders_per_group": {},
                    "tasks_per_group": {},
                    "invalid_reasons": [str(exc)],
                }
                error = str(exc)
            elapsed_ms = round((time.monotonic() - attempt_started) * 1000, 3)
            accepted = bool(record["valid"]) and (
                best_record is None or record["local_cost"] < best_record["local_cost"] - 1e-9
            )
            if accepted:
                best_solution = solution
                best_record = record
                best_strategy = strategy.name
            attempt_payload = {
                "name": strategy.name,
                "label": strategy.label,
                "reason": strategy.reason,
                "local_cost": record["local_cost"],
                "valid": record["valid"],
                "covered_tasks": record["covered_tasks"],
                "total_tasks": record["total_tasks"],
                "groups": record["groups"],
                "elapsed_ms": elapsed_ms,
                "accepted": accepted,
                "error": error,
            }
            round_payload["strategies"].append(attempt_payload)
            emit(
                {
                    "type": "attempt_result",
                    "round": round_index,
                    "strategy": strategy.name,
                    "label": strategy.label,
                    "local_cost": record["local_cost"],
                    "accepted": accepted,
                    "coverage": f"{record['covered_tasks']}/{record['total_tasks']}",
                    "elapsed_ms": elapsed_ms,
                    "valid": record["valid"],
                }
            )
            if accepted:
                emit(
                    {
                        "type": "best_update",
                        "strategy": strategy.name,
                        "message": f"保留 {strategy.label} 为当前最优。",
                        "local_cost": record["local_cost"],
                        "coverage": f"{record['covered_tasks']}/{record['total_tasks']}",
                    }
                )
        rounds.append(round_payload)
        if not adaptive_added and best_record is not None:
            adaptive_added = True
            if safety.passed:
                baseline_cost = float(best_record["local_cost"])
                outcome = evolution.run_generated_strategy(
                    generated_strategy,
                    candidates,
                    all_tasks,
                    deadline_s=min(0.15, max(0.02, deadline - time.monotonic() - 0.25)),
                    helpers=evolution_helpers(),
                    baseline_cost=baseline_cost,
                    score_fn=lambda solution: _score(module, solution, candidates, all_tasks),
                    summarize_fn=lambda solution, cost: summarize_solution(solution, candidates, all_tasks, cost),
                    case_profile=case_profile,
                )
                emit(
                    {
                        "type": "evolution_trial",
                        "message": f"实验策略 {outcome.strategy_id} {outcome.decision}：{outcome.reason}；失败不会影响 stable baseline。",
                        "strategy_id": outcome.strategy_id,
                        "decision": outcome.decision,
                        "accepted": outcome.accepted,
                    }
                )
                if outcome.accepted:
                    emit(
                        {
                            "type": "evolution_promote",
                            "message": f"实验策略 {outcome.strategy_id} 进入候选记忆；Planner 可在后续轮次复用。",
                            "strategy_id": outcome.strategy_id,
                            "decision": "promote",
                        }
                    )
                else:
                    emit(
                        {
                            "type": "evolution_rollback",
                            "message": f"实验策略 {outcome.strategy_id} 已回退到 stable baseline；solver.py 未被修改。",
                            "strategy_id": outcome.strategy_id,
                            "decision": "rollback",
                        }
                    )
                if outcome.accepted and outcome.solution:
                    generated_record = _solution_record(module, outcome.solution, candidates, all_tasks)
                    if bool(generated_record["valid"]) and generated_record["local_cost"] < best_record["local_cost"] - 1e-9:
                        best_solution = outcome.solution
                        best_record = generated_record
                        best_strategy = outcome.strategy_id
                        emit(
                            {
                                "type": "best_update",
                                "strategy": outcome.strategy_id,
                                "message": f"生成策略 {outcome.strategy_id} 被 Critic 接受为新的 best-so-far。",
                            }
                        )
            for item in trusted[:2]:
                if time.monotonic() >= deadline - 0.35:
                    break
                strategy_path = Path(str(item.get("file", "")))
                remembered = GeneratedStrategy(str(item["strategy_id"]), strategy_path, regime, "evolution-memory")
                outcome = evolution.run_generated_strategy(
                    remembered,
                    candidates,
                    all_tasks,
                    deadline_s=min(0.12, max(0.02, deadline - time.monotonic() - 0.25)),
                    helpers=evolution_helpers(),
                    baseline_cost=float(best_record["local_cost"]),
                    score_fn=lambda solution: _score(module, solution, candidates, all_tasks),
                    summarize_fn=lambda solution, cost: summarize_solution(solution, candidates, all_tasks, cost),
                    case_profile=case_profile,
                )
                emit(
                    {
                        "type": "evolution_replay",
                        "message": f"复用相似历史策略 {outcome.strategy_id}：{outcome.decision}，{outcome.reason}。",
                        "strategy_id": outcome.strategy_id,
                        "decision": outcome.decision,
                        "accepted": outcome.accepted,
                        "similarity": item.get("similarity", 0.0),
                    }
                )
                if outcome.accepted:
                    emit(
                        {
                            "type": "evolution_promote",
                            "message": f"历史策略 {outcome.strategy_id} 通过本轮复核，继续保留在候选记忆。",
                            "strategy_id": outcome.strategy_id,
                            "decision": "promote",
                        }
                    )
                    if outcome.solution:
                        replay_record = _solution_record(module, outcome.solution, candidates, all_tasks)
                        if bool(replay_record["valid"]) and replay_record["local_cost"] < best_record["local_cost"] - 1e-9:
                            best_solution = outcome.solution
                            best_record = replay_record
                            best_strategy = outcome.strategy_id
                            emit(
                                {
                                    "type": "best_update",
                                    "strategy": outcome.strategy_id,
                                    "message": f"历史生成策略 {outcome.strategy_id} 被 Critic 接受为新的 best-so-far。",
                                }
                            )
                else:
                    emit(
                        {
                            "type": "evolution_rollback",
                            "message": f"历史策略 {outcome.strategy_id} 本轮未通过，回退到 stable baseline。",
                            "strategy_id": outcome.strategy_id,
                            "decision": "rollback",
                        }
                    )
            next_reason, next_strategies = _adaptive_strategies(
                regime,
                best_strategy,
                int(best_record["covered_tasks"]),
                int(best_record["total_tasks"]),
            )
            strategy_rounds.append((next_reason, next_strategies))
            emit({"type": "adapt", "message": next_reason})

    if best_record is None:
        best_solution = module.solve(input_text)
        best_record = _solution_record(module, best_solution, candidates, all_tasks)
        best_strategy = "production_solver"
        emit({"type": "fallback", "message": "所有策略失败，回退到生产级 solver.py。"})

    best = {"strategy": best_strategy, **best_record}
    emit(
        {
            "type": "final",
            "message": "Agent 输出 best-so-far 最终方案。",
            "strategy": best_strategy,
            "local_cost": best_record["local_cost"],
            "coverage": f"{best_record['covered_tasks']}/{best_record['total_tasks']}",
        }
    )
    return {
        "status": "ok",
        "case_id": case_id,
        "regime": regime,
        "wall_time_s": round(time.monotonic() - started, 6),
        "budget_s": budget_s,
        "features": features,
        "evolution": {
            "memory_path": str(evolution.memory_path),
            "registry_path": str(evolution.registry_path),
            "generated_strategy": generated_strategy.strategy_id,
            "trusted_recalled": [item["strategy_id"] for item in trusted[:3]],
            "trusted_details": [
                {
                    "strategy_id": item["strategy_id"],
                    "similarity": item.get("similarity", 0.0),
                    "target_regime": item.get("target_regime"),
                }
                for item in trusted[:3]
            ],
            "case_profile": case_profile,
            "mode": "experimental-track-no-solver-mutation",
        },
        "critic_policy": {
            "internal_signal": "The ranking signal is internal to the controller and hidden from the web demo.",
            "presentation_rule": "The web demo only presents agent decisions and tool flow.",
        },
        "best": best,
        "rounds": rounds,
        "events": events,
        "solution": best_solution,
    }


def run_case_agent(
    case_path: Path,
    case_id: str,
    budget_s: float = 10.0,
    observer: Callable[[dict[str, Any]], None] | None = None,
) -> dict[str, Any]:
    return run_agent(case_path.read_text(encoding="utf-8"), case_id=case_id, budget_s=budget_s, observer=observer)
