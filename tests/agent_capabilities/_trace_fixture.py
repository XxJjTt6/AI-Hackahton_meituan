from __future__ import annotations

from functools import lru_cache
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "Fwd_ 【美团AI Hackathon大赛】-【命题四AutoSolver：让AI Agent 自主求解配送分配问题】脱敏数据"
LARGE_CASE = DATA / "large_seed301.txt"


@lru_cache(maxsize=1)
def large_trace():
    from tools.agent_trace_demo import generate_trace

    return generate_trace(LARGE_CASE, ROOT / "solver.py")
