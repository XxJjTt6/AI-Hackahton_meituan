from __future__ import annotations

import ast
import datetime as dt
import importlib.util
import inspect
import json
import time
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import Any, Callable


ALLOWED_IMPORTS = {"collections", "heapq", "itertools", "math", "random", "time"}
BLOCKED_CALLS = {"compile", "eval", "exec", "globals", "locals", "open", "__import__"}
BLOCKED_ATTR_ROOTS = {"os", "pathlib", "socket", "subprocess", "sys"}


@dataclass(frozen=True)
class GeneratedStrategy:
    strategy_id: str
    path: Path
    target_regime: str
    source: str


@dataclass(frozen=True)
class SafetyResult:
    strategy_id: str
    path: Path
    passed: bool
    reason: str
    status: str


@dataclass(frozen=True)
class TrialOutcome:
    strategy_id: str
    status: str
    decision: str
    reason: str
    accepted: bool
    elapsed_ms: float
    solution: list[tuple[str, list[str]]]
    local_cost: float | None


class EvolutionManager:
    """Manages generated strategy experiments without mutating solver.py."""

    def __init__(self, root: Path) -> None:
        self.root = Path(root)
        self.generated_dir = self.root / "generated_strategies"
        self.memory_path = self.root / "evolution_memory.jsonl"
        self.registry_path = self.root / "strategy_registry.json"
        self.generated_dir.mkdir(parents=True, exist_ok=True)
        self.root.mkdir(parents=True, exist_ok=True)

    def generate_strategy(self, target_regime: str, source: str) -> GeneratedStrategy:
        strategy_id = self._next_strategy_id(target_regime)
        path = self.generated_dir / f"{strategy_id}.py"
        path.write_text(self._strategy_template(strategy_id), encoding="utf-8")
        strategy = GeneratedStrategy(strategy_id, path, target_regime, source)
        self._update_registry(
            strategy_id,
            {
                "status": "draft",
                "target_regime": target_regime,
                "source": source,
                "file": str(path),
                "attempts": 0,
                "accepted": 0,
                "rejected": 0,
            },
        )
        self._append_memory(
            {
                "event": "strategy_generated",
                "strategy_id": strategy_id,
                "target_regime": target_regime,
                "source": source,
                "file": str(path),
            }
        )
        return strategy

    def safety_check(self, path: Path, strategy_id: str | None = None) -> SafetyResult:
        path = Path(path)
        strategy_id = strategy_id or path.stem
        try:
            source = path.read_text(encoding="utf-8")
            tree = ast.parse(source, filename=str(path))
            reason = self._unsafe_reason(tree)
            if reason:
                return self._record_safety(strategy_id, path, False, reason, "rejected")
            module = self._load_module(path, strategy_id)
            propose = getattr(module, "propose", None)
            if not callable(propose):
                return self._record_safety(strategy_id, path, False, "missing propose", "rejected")
            params = list(inspect.signature(propose).parameters)
            if params != ["candidates", "all_tasks", "deadline", "helpers"]:
                return self._record_safety(strategy_id, path, False, "invalid propose signature", "rejected")
        except SyntaxError as exc:
            return self._record_safety(strategy_id, path, False, f"syntax error: {exc.msg}", "rejected")
        except Exception as exc:
            return self._record_safety(strategy_id, path, False, f"load error: {exc}", "rejected")
        return self._record_safety(strategy_id, path, True, "passed", "sandboxed")

    def run_generated_strategy(
        self,
        strategy: GeneratedStrategy,
        candidates: list,
        all_tasks: set[str],
        deadline_s: float,
        helpers: dict[str, Any],
        baseline_cost: float,
        score_fn: Callable[[list[tuple[str, list[str]]]], float],
        summarize_fn: Callable[[list[tuple[str, list[str]]], float], dict[str, Any]],
    ) -> TrialOutcome:
        started = time.monotonic()
        try:
            safety = self.safety_check(strategy.path, strategy.strategy_id)
            if not safety.passed:
                return self._record_trial(strategy.strategy_id, [], None, started, False, "reject", safety.reason)
            module = self._load_module(strategy.path, strategy.strategy_id)
            local_deadline = time.monotonic() + max(0.01, deadline_s)
            solution = module.propose(candidates, all_tasks, local_deadline, helpers)
            if time.monotonic() > local_deadline + 0.02:
                return self._record_trial(strategy.strategy_id, [], None, started, False, "reject", "timeout")
            if not self._looks_like_solution(solution):
                return self._record_trial(strategy.strategy_id, [], None, started, False, "reject", "invalid output format")
            cost = float(score_fn(solution))
            summary = summarize_fn(solution, cost)
            if not summary.get("valid"):
                reason = "; ".join(summary.get("invalid_reasons") or ["invalid solution"])
                return self._record_trial(strategy.strategy_id, solution, cost, started, False, "reject", reason)
            if cost <= baseline_cost - 1e-9:
                return self._record_trial(strategy.strategy_id, solution, cost, started, True, "accept", "improved or matched baseline")
            return self._record_trial(strategy.strategy_id, solution, cost, started, False, "reject", "quality regression")
        except Exception as exc:
            return self._record_trial(strategy.strategy_id, [], None, started, False, "reject", f"exception: {exc}")

    def trusted_strategies(self, regime: str) -> list[dict[str, Any]]:
        registry = self._read_registry()
        trusted = []
        for strategy_id, item in registry.items():
            if item.get("target_regime") == regime and item.get("status") in {"candidate", "trusted", "promoted"}:
                trusted.append({"strategy_id": strategy_id, **item})
        return sorted(trusted, key=lambda item: (-int(item.get("accepted", 0)), item["strategy_id"]))

    def _record_safety(self, strategy_id: str, path: Path, passed: bool, reason: str, status: str) -> SafetyResult:
        patch = {"status": status, "safety_passed": passed, "safety_reason": reason}
        if not passed:
            patch["rollback_action"] = "removed_from_active_pool"
        self._update_registry(strategy_id, patch)
        self._append_memory(
            {
                "event": "strategy_validated",
                "strategy_id": strategy_id,
                "syntax_passed": not reason.startswith("syntax error"),
                "safety_passed": passed,
                "interface_passed": passed,
                "status": status,
                "reason": reason,
            }
        )
        return SafetyResult(strategy_id, path, passed, reason, status)

    def _record_trial(
        self,
        strategy_id: str,
        solution: list[tuple[str, list[str]]],
        cost: float | None,
        started: float,
        accepted: bool,
        decision: str,
        reason: str,
    ) -> TrialOutcome:
        elapsed_ms = round((time.monotonic() - started) * 1000.0, 3)
        status = "candidate" if accepted else "rejected"
        registry = self._read_registry().get(strategy_id, {})
        attempts = int(registry.get("attempts", 0)) + 1
        accepted_count = int(registry.get("accepted", 0)) + (1 if accepted else 0)
        rejected_count = int(registry.get("rejected", 0)) + (0 if accepted else 1)
        self._update_registry(
            strategy_id,
            {
                "status": status,
                "attempts": attempts,
                "accepted": accepted_count,
                "rejected": rejected_count,
                "last_decision": decision,
                "last_reason": reason,
                "last_cost": cost,
                "rollback_action": None if accepted else "removed_from_active_pool",
            },
        )
        self._append_memory(
            {
                "event": "strategy_trial",
                "strategy_id": strategy_id,
                "status": status,
                "accepted": accepted,
                "decision": decision,
                "reason": reason,
                "elapsed_ms": elapsed_ms,
                "local_cost": cost,
            }
        )
        return TrialOutcome(strategy_id, status, decision, reason, accepted, elapsed_ms, solution, cost)

    def _append_memory(self, event: dict[str, Any]) -> None:
        event = {"created_at": dt.datetime.now().isoformat(timespec="seconds"), **event}
        with self.memory_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(event, ensure_ascii=False) + "\n")

    def _read_registry(self) -> dict[str, dict[str, Any]]:
        if not self.registry_path.exists():
            return {}
        return json.loads(self.registry_path.read_text(encoding="utf-8") or "{}")

    def _update_registry(self, strategy_id: str, patch: dict[str, Any]) -> None:
        registry = self._read_registry()
        current = registry.get(strategy_id, {})
        current.update({key: value for key, value in patch.items() if value is not None})
        current["last_seen"] = dt.datetime.now().isoformat(timespec="seconds")
        registry[strategy_id] = current
        self.registry_path.write_text(json.dumps(registry, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")

    def _next_strategy_id(self, target_regime: str) -> str:
        safe = "".join(ch if ch.isalnum() else "_" for ch in target_regime).strip("_") or "generic"
        existing = sorted(self.generated_dir.glob(f"gen_{safe}_v*.py"))
        return f"gen_{safe}_v{len(existing) + 1:03d}"

    @staticmethod
    def _strategy_template(strategy_id: str) -> str:
        return f'''# Auto-generated experimental strategy: {strategy_id}\nfrom __future__ import annotations\n\n\ndef propose(candidates, all_tasks, deadline, helpers):\n    """Return a safe greedy baseline candidate for sandbox evaluation."""\n    fallback = helpers.get("fallback_greedy")\n    if fallback is not None:\n        return fallback(candidates)\n    used_couriers = set()\n    covered_tasks = set()\n    result = []\n    for task_key, task_ids, courier_id, _score, _willingness, _row_index in sorted(candidates, key=lambda row: row[3]):\n        if courier_id in used_couriers:\n            continue\n        if any(task_id in covered_tasks for task_id in task_ids):\n            continue\n        used_couriers.add(courier_id)\n        covered_tasks.update(task_ids)\n        result.append((task_key, [courier_id]))\n        if covered_tasks >= set(all_tasks):\n            break\n    return result\n'''

    @staticmethod
    def _unsafe_reason(tree: ast.AST) -> str | None:
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                if isinstance(node, ast.ImportFrom) and node.module == "__future__":
                    continue
                names = [alias.name.split(".", 1)[0] for alias in getattr(node, "names", [])]
                if isinstance(node, ast.ImportFrom) and node.module:
                    names.append(node.module.split(".", 1)[0])
                for name in names:
                    if name not in ALLOWED_IMPORTS:
                        return f"unsafe import: {name}"
            if isinstance(node, ast.Call):
                func = node.func
                if isinstance(func, ast.Name) and func.id in BLOCKED_CALLS:
                    return f"unsafe call: {func.id}"
                if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name) and func.value.id in BLOCKED_ATTR_ROOTS:
                    return f"unsafe attribute call: {func.value.id}.{func.attr}"
        return None

    @staticmethod
    def _load_module(path: Path, strategy_id: str) -> ModuleType:
        spec = importlib.util.spec_from_file_location(f"autosolver_generated_{strategy_id}", str(path))
        if spec is None or spec.loader is None:
            raise ImportError(f"cannot load generated strategy {path}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    @staticmethod
    def _looks_like_solution(solution: Any) -> bool:
        if not isinstance(solution, list):
            return False
        for item in solution:
            if not isinstance(item, tuple) or len(item) != 2:
                return False
            task_key, couriers = item
            if not isinstance(task_key, str) or not isinstance(couriers, list) or not all(isinstance(c, str) for c in couriers):
                return False
        return True
