from __future__ import annotations

import argparse
import json
import sys
import traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from autosolver_agent.system import get_agent_blueprint, run_case_agent as _run_case_agent

try:
    from web_agent_demo.sample_cases import ensure_sample_cases
except ImportError:  # The demo can still run before optional synthetic cases are generated.
    ensure_sample_cases = None


DATA_DIR = ROOT / "Fwd_ 【美团AI Hackathon大赛】-【命题四AutoSolver：让AI Agent 自主求解配送分配问题】脱敏数据"
GENERATED_CASE_DIR = ROOT / "web_agent_demo" / "generated_cases"
CASE_FILES = {
    "large_seed301": DATA_DIR / "large_seed301.txt",
}


def _case_files() -> dict[str, Path]:
    files = dict(CASE_FILES)
    if ensure_sample_cases is not None:
        files.update(ensure_sample_cases(ROOT))
    return files


def list_cases() -> list[dict[str, object]]:
    cases = []
    for case_id, path in _case_files().items():
        if not path.exists():
            continue
        lines = path.read_text(encoding="utf-8").strip().splitlines()
        row_count = max(0, len(lines) - (1 if lines and lines[0].startswith("task_id_list") else 0))
        case_type = "real provided case" if case_id == "large_seed301" else "synthetic demo case"
        cases.append({"id": case_id, "name": case_id, "rows": row_count, "type": case_type})
    return cases


def run_case_agent(case_id: str, budget_s: float = 10.0, observer=None) -> dict[str, object]:
    path = _case_files().get(case_id)
    if path is None or not path.exists():
        raise ValueError(f"unknown case: {case_id}")
    return _run_case_agent(path, case_id=case_id, budget_s=budget_s, observer=observer)


def build_agent_payload(case_id: str, budget_s: float = 10.0) -> dict[str, object]:
    return {"status": "ok", "report": run_case_agent(case_id, budget_s=budget_s)}


def _sse(event: str, data: dict[str, object]) -> bytes:
    payload = json.dumps(data, ensure_ascii=False)
    return f"event: {event}\ndata: {payload}\n\n".encode("utf-8")


def render_index() -> str:
    return """<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>AutoSolver Agent System</title>
  <style>
    :root {
      --ink: #16211e;
      --muted: #66736e;
      --leaf: #236a43;
      --leaf-2: #123f2a;
      --gold: #d8b14a;
      --sand: #f4ead6;
      --clay: #c9714a;
      --blue: #2e5f73;
      --paper: rgba(255, 253, 246, .82);
      --card: rgba(255, 255, 255, .72);
      --line: rgba(22, 33, 30, .14);
      --shadow: 0 24px 80px rgba(31, 46, 38, .16);
      --mono: "SFMono-Regular", "Cascadia Code", Consolas, monospace;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      color: var(--ink);
      font-family: "Avenir Next", "PingFang SC", "Hiragino Sans GB", sans-serif;
      background:
        linear-gradient(90deg, rgba(22,33,30,.055) 1px, transparent 1px),
        linear-gradient(180deg, rgba(22,33,30,.045) 1px, transparent 1px),
        radial-gradient(circle at 8% 12%, rgba(216,177,74,.34), transparent 22rem),
        radial-gradient(circle at 88% 4%, rgba(46,95,115,.25), transparent 28rem),
        radial-gradient(circle at 80% 92%, rgba(35,106,67,.22), transparent 24rem),
        linear-gradient(135deg, #f8efd9 0%, #eef0df 44%, #d9e8df 100%);
      background-size: 42px 42px, 42px 42px, auto, auto, auto, auto;
      min-height: 100vh;
    }
    main { width: min(1440px, calc(100vw - 32px)); margin: 0 auto; padding: 26px 0 46px; }
    .panel {
      background: var(--paper);
      border: 1px solid var(--line);
      border-radius: 26px;
      box-shadow: var(--shadow);
      backdrop-filter: blur(18px);
    }
    .topbar {
      display: grid;
      grid-template-columns: minmax(340px, 1.1fr) minmax(360px, .9fr);
      gap: 18px;
      align-items: stretch;
      margin-bottom: 18px;
    }
    .hero { padding: 28px; position: relative; overflow: hidden; }
    .hero:after {
      content: "AGENT LOOP";
      position: absolute;
      right: -18px;
      bottom: -8px;
      color: rgba(22,33,30,.055);
      font-weight: 900;
      font-size: clamp(54px, 10vw, 148px);
      letter-spacing: -.08em;
      pointer-events: none;
    }
    .eyebrow { color: var(--leaf); font-weight: 900; letter-spacing: .16em; text-transform: uppercase; font-size: 12px; }
    h1 { font-size: clamp(32px, 4.3vw, 58px); line-height: .96; margin: 12px 0 14px; letter-spacing: -0.06em; max-width: 880px; }
    h2 { margin: 0; font-size: 22px; letter-spacing: -0.035em; }
    .lead { color: var(--muted); font-size: 17px; line-height: 1.75; max-width: 790px; position: relative; z-index: 1; }
    .controls { padding: 22px; display: grid; gap: 12px; }
    .control-row { display: grid; grid-template-columns: 1fr 130px; gap: 10px; }
    label { color: var(--muted); font-size: 13px; font-weight: 800; display: grid; gap: 7px; }
    select, input, button {
      width: 100%;
      border: 1px solid var(--line);
      border-radius: 16px;
      padding: 13px 14px;
      font-size: 16px;
      background: rgba(255,255,255,.88);
      color: var(--ink);
    }
    button {
      cursor: pointer;
      border: none;
      color: white;
      font-weight: 900;
      background: linear-gradient(135deg, var(--leaf), var(--leaf-2));
      box-shadow: 0 14px 34px rgba(35,106,67,.26);
    }
    button.secondary { background: linear-gradient(135deg, var(--blue), #183247); }
    button:disabled { cursor: wait; opacity: .6; }
    .status-pill {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      width: fit-content;
      border-radius: 999px;
      padding: 8px 11px;
      background: rgba(255,255,255,.62);
      color: var(--muted);
      font-weight: 800;
      font-size: 12px;
    }
    .status-pill:before { content: ""; width: 8px; height: 8px; border-radius: 50%; background: var(--gold); box-shadow: 0 0 0 4px rgba(216,177,74,.18); }
    .status-pill.running:before { background: var(--leaf); animation: pulse 1.1s infinite; }
    @keyframes pulse { 50% { transform: scale(1.4); opacity: .55; } }
    .workbench {
      display: grid;
      grid-template-columns: 280px minmax(0, 1fr) 340px;
      gap: 18px;
      align-items: start;
    }
    .rail, .timeline-panel, .inspector, .table-panel, .evolution-panel { padding: 20px; }
    .rail { position: sticky; top: 18px; }
    .objective {
      margin: 14px 0 18px;
      color: var(--muted);
      line-height: 1.65;
      font-size: 14px;
    }
    .stage-list { display: grid; gap: 10px; }
    .stage {
      display: grid;
      grid-template-columns: 36px 1fr;
      gap: 10px;
      padding: 12px;
      border-radius: 18px;
      background: var(--card);
      border: 1px solid var(--line);
      transition: border-color .2s ease, transform .2s ease, background .2s ease;
    }
    .stage.active { border-color: rgba(35,106,67,.62); background: rgba(239, 248, 228, .86); transform: translateX(4px); }
    .stage.done { border-color: rgba(216,177,74,.45); }
    .stage-index {
      width: 34px;
      height: 34px;
      display: grid;
      place-items: center;
      border-radius: 12px;
      background: rgba(22,33,30,.08);
      font-weight: 900;
      color: var(--leaf-2);
    }
    .stage b { display: block; margin-bottom: 4px; }
    .stage span { display: block; color: var(--muted); font-size: 12px; line-height: 1.45; }
    .timeline-toolbar {
      display: grid;
      grid-template-columns: 1fr auto auto;
      gap: 10px;
      align-items: center;
      margin: 14px 0;
    }
    .filters { display: flex; flex-wrap: wrap; gap: 7px; }
    .filter {
      border: 1px solid var(--line);
      border-radius: 999px;
      padding: 8px 10px;
      background: rgba(255,255,255,.66);
      color: var(--muted);
      font-size: 12px;
      font-weight: 900;
      cursor: pointer;
      user-select: none;
    }
    .filter.active { color: white; background: var(--leaf); border-color: transparent; }
    .toggle {
      border: 1px solid var(--line);
      border-radius: 999px;
      padding: 8px 11px;
      background: rgba(255,255,255,.66);
      font-size: 12px;
      font-weight: 900;
      color: var(--muted);
      cursor: pointer;
      user-select: none;
      white-space: nowrap;
    }
    .toggle.on { color: white; background: var(--blue); border-color: transparent; }
    .timeline {
      height: 620px;
      overflow: auto;
      padding-right: 6px;
      display: grid;
      align-content: start;
      gap: 10px;
    }
    .event {
      position: relative;
      display: grid;
      grid-template-columns: 90px 1fr;
      gap: 12px;
      padding: 14px;
      border-radius: 18px;
      background: rgba(255,255,255,.70);
      border: 1px solid var(--line);
    }
    .event.accepted { border-color: rgba(35,106,67,.55); background: rgba(239,248,228,.82); }
    .event.rejected { border-color: rgba(201,113,74,.42); }
    .time {
      font-family: var(--mono);
      font-size: 12px;
      color: var(--muted);
      white-space: nowrap;
    }
    .event-type {
      display: inline-block;
      border-radius: 999px;
      padding: 4px 8px;
      margin-bottom: 7px;
      background: rgba(46,95,115,.12);
      color: var(--blue);
      font-size: 11px;
      font-weight: 900;
      letter-spacing: .06em;
      text-transform: uppercase;
    }
    .event.accepted .event-type { background: rgba(35,106,67,.14); color: var(--leaf); }
    .event.rejected .event-type { background: rgba(201,113,74,.14); color: var(--clay); }
    .event-title { font-weight: 900; letter-spacing: -.02em; }
    .event-body { color: var(--muted); line-height: 1.55; margin-top: 5px; font-size: 14px; }
    .event-meta { display: flex; gap: 8px; flex-wrap: wrap; margin-top: 9px; }
    .chip {
      border-radius: 999px;
      padding: 4px 8px;
      background: rgba(22,33,30,.07);
      color: var(--muted);
      font-size: 11px;
      font-weight: 800;
    }
    .inspector { position: sticky; top: 18px; display: grid; gap: 14px; }
    .inspect-card {
      padding: 15px;
      border-radius: 18px;
      background: var(--card);
      border: 1px solid var(--line);
    }
    .inspect-card b { display: block; margin-bottom: 8px; }
    .inspect-card div { color: var(--muted); line-height: 1.55; font-size: 14px; }
    .metrics { display: grid; grid-template-columns: repeat(3, 1fr); gap: 9px; }
    .metric {
      padding: 12px;
      border-radius: 16px;
      background: rgba(255,255,255,.68);
      border: 1px solid var(--line);
    }
    .metric strong { display: block; font-size: 21px; letter-spacing: -.04em; }
    .metric span { color: var(--muted); font-size: 11px; font-weight: 900; text-transform: uppercase; }
    .evolution-panel { margin-top: 18px; overflow: hidden; }
    .evolution-head {
      display: grid;
      grid-template-columns: minmax(0, 1fr) auto;
      gap: 18px;
      align-items: center;
      margin-bottom: 16px;
    }
    .evolution-head p {
      margin: 7px 0 0;
      color: var(--muted);
      line-height: 1.6;
      max-width: 840px;
    }
    .loop-badge {
      border-radius: 999px;
      padding: 9px 12px;
      background: rgba(35,106,67,.12);
      color: var(--leaf);
      font-weight: 900;
      font-size: 12px;
      white-space: nowrap;
    }
    .code-loop {
      display: grid;
      grid-template-columns: repeat(6, minmax(0, 1fr));
      gap: 10px;
      align-items: stretch;
    }
    .loop-step {
      position: relative;
      min-height: 128px;
      padding: 14px;
      border-radius: 19px;
      border: 1px solid var(--line);
      background:
        radial-gradient(circle at 12% 14%, rgba(216,177,74,.18), transparent 5.2rem),
        rgba(255,255,255,.66);
    }
    .loop-step:after {
      content: ">";
      position: absolute;
      right: -10px;
      top: 45%;
      color: rgba(22,33,30,.28);
      font-weight: 900;
    }
    .loop-step:last-child:after { content: ""; }
    .loop-tag {
      display: inline-flex;
      border-radius: 999px;
      padding: 5px 8px;
      margin-bottom: 10px;
      background: rgba(46,95,115,.12);
      color: var(--blue);
      font-weight: 900;
      font-size: 11px;
      letter-spacing: .04em;
      text-transform: uppercase;
    }
    .loop-step b { display: block; margin-bottom: 7px; }
    .loop-step span:last-child { color: var(--muted); line-height: 1.45; font-size: 13px; }
    .table-panel { margin-top: 18px; }
    .attempt-grid { display: grid; gap: 10px; margin-top: 14px; }
    .attempt {
      display: grid;
      grid-template-columns: 150px 1fr 120px 90px;
      gap: 12px;
      align-items: center;
      padding: 13px 14px;
      border-radius: 17px;
      background: rgba(255,255,255,.70);
      border: 1px solid var(--line);
    }
    .attempt.accepted { border-color: rgba(35,106,67,.55); background: rgba(239,248,228,.82); }
    .attempt.rejected { border-color: rgba(201,113,74,.38); }
    .attempt .name { font-weight: 900; }
    .attempt .why { color: var(--muted); font-size: 13px; line-height: 1.45; }
    .verdict {
      border-radius: 999px;
      padding: 7px 9px;
      text-align: center;
      font-size: 12px;
      font-weight: 900;
      background: rgba(22,33,30,.08);
      color: var(--muted);
    }
    .attempt.accepted .verdict { color: white; background: var(--leaf); }
    .attempt.rejected .verdict { color: white; background: var(--clay); }
    .muted { color: var(--muted); }
    .empty {
      min-height: 170px;
      display: grid;
      place-items: center;
      text-align: center;
      color: var(--muted);
      border: 1px dashed var(--line);
      border-radius: 18px;
      background: rgba(255,255,255,.42);
      line-height: 1.7;
    }
    @media (max-width: 1100px) {
      .workbench, .topbar { grid-template-columns: 1fr; }
      .code-loop { grid-template-columns: repeat(2, minmax(0, 1fr)); }
      .rail, .inspector { position: static; }
      .timeline { height: 460px; }
    }
    @media (max-width: 760px) {
      main { width: min(100vw - 20px, 1180px); padding-top: 16px; }
      .control-row, .timeline-toolbar, .attempt, .code-loop, .evolution-head { grid-template-columns: 1fr; }
      .event { grid-template-columns: 1fr; }
      .metrics { grid-template-columns: 1fr; }
    }
  </style>
</head>
<body>
<main>
  <div class="topbar">
    <section class="hero panel">
      <div class="eyebrow">Live Agent Workbench</div>
      <h1>看见 Agent 如何一步步求解</h1>
      <p class="lead">页面重点展示运行过程，而不是静态成绩。启动后可以从阶段轨道、实时事件流、右侧检查器和候选表里看到 Planner 提案、Executor 调用、Critic 接受/拒绝、Controller 调整、Memory 保留 best-so-far，以及 Evolution 生成实验策略并按门禁回退或晋升。</p>
    </section>
    <section class="controls panel">
      <div class="control-row">
        <label>测试用例<select id="case-select"></select></label>
        <label>预算秒数<input id="budget" type="number" min="1" max="10" step="0.5" value="10"></label>
      </div>
      <button id="run-agent">启动 Agent 求解</button>
      <button id="reload-cases" class="secondary">刷新用例和能力</button>
      <div id="status" class="status-pill">等待启动</div>
    </section>
  </div>

  <section class="workbench">
    <aside class="rail panel">
      <h2>Agent 阶段</h2>
      <div id="objective" class="objective">加载 Agent 目标中。</div>
      <div class="stage-list" id="stages"></div>
    </aside>

    <section class="timeline-panel panel">
      <h2>实时事件流</h2>
      <div class="timeline-toolbar">
        <div class="filters" id="filters"></div>
        <div class="toggle on" id="autoscroll">自动滚动</div>
        <div class="toggle" id="compact">紧凑视图</div>
      </div>
      <div class="timeline" id="events"><div class="empty">启动后这里会按时间顺序显示每个 Agent 动作。<br>可以筛选 Planner、Executor、Critic、Controller、Memory、Evolution。</div></div>
    </section>

    <aside class="inspector panel">
      <h2>当前检查器</h2>
      <div class="metrics">
        <div class="metric"><strong id="metric-events">0</strong><span>Events</span></div>
        <div class="metric"><strong id="metric-accepted">0</strong><span>Memory</span></div>
        <div class="metric"><strong id="metric-round">0</strong><span>Round</span></div>
      </div>
      <div class="inspect-card"><b>当前阶段</b><div id="current-stage">等待启动。</div></div>
      <div class="inspect-card"><b>当前动作</b><div id="current-action">还没有工具调用。</div></div>
      <div class="inspect-card"><b>Controller 解释</b><div id="controller-note">等待第一轮规划。</div></div>
        <div class="inspect-card"><b>Self-Evolving Code Loop</b><div id="evolution-note">等待生成实验策略。</div></div>
      <div class="inspect-card"><b>Case Profile</b><div id="case-profile">选择用例后会展示任务数、骑手数、候选行和 regime。</div></div>
    </aside>
  </section>

  <section class="evolution-panel panel">
    <div class="evolution-head">
      <div>
        <h2>Self-Evolving Code Loop</h2>
        <p>这个区域展示 Agent 如何生成实验 Python 策略，并在隔离的实验轨道里完成验证、试跑、回退或晋升。正式 `solver.py` 始终作为 stable baseline，不被网页实验直接改写。</p>
      </div>
      <div class="loop-badge">Experimental Track</div>
    </div>
    <div class="code-loop">
      <div class="loop-step"><span class="loop-tag">Generate</span><b>生成策略草稿</b><span>Planner 根据 regime 和历史记忆产生候选 Python 策略。</span></div>
      <div class="loop-step"><span class="loop-tag">Safety Gate</span><b>代码门禁</b><span>AST 检查导入、危险调用和 propose 接口。</span></div>
      <div class="loop-step"><span class="loop-tag">Sandbox Execute</span><b>限时试跑</b><span>Executor 只给短时间片，失败不会进入主方案。</span></div>
      <div class="loop-step"><span class="loop-tag">Critic Decision</span><b>质量裁决</b><span>Critic 用内部信号判断接受、拒绝或继续搜索。</span></div>
      <div class="loop-step"><span class="loop-tag">Rollback</span><b>安全回退</b><span>未通过验证或效果变差时回到 stable baseline。</span></div>
      <div class="loop-step"><span class="loop-tag">Evolution Memory</span><b>写入记忆</b><span>成功或失败都会记录，影响下一轮 Planner。</span></div>
    </div>
  </section>

  <section class="table-panel panel">
    <h2>策略候选表</h2>
    <div id="rounds" class="attempt-grid"><div class="empty">候选表会在每轮运行后更新：展示每个策略的用途、耗时、以及是否进入 Memory。</div></div>
  </section>
</main>
<script>
const $ = (id) => document.getElementById(id);
let currentRun = null;
let events = [];
let attempts = [];
let activeFilter = 'all';
let autoScroll = true;
let compactView = false;
let acceptedCount = 0;
const stages = [
  ['perception', 'Perception', '读取 case，识别任务、骑手、bundle 和意愿分布。'],
  ['planner', 'Planner', '提出本轮策略批次，并说明尝试原因。'],
  ['executor', 'Executor', '实际调用候选生成或生产级 solver。'],
  ['critic', 'Critic', '判断候选是否有效，是否进入 Memory。'],
  ['controller', 'Controller', '根据结果决定下一轮方向和预算处理。'],
  ['memory', 'Memory', '保留 best-so-far，最终输出方案。'],
  ['evolution', 'Evolution', 'Self-Evolving Code Loop：生成实验 Python 策略，经过 Safety Gate 和 Sandbox Execute 后接受、回退或写入记忆。'],
];
const filterItems = [
  ['all', '全部'],
  ['planner', 'Planner'],
  ['executor', 'Executor'],
  ['critic', 'Critic'],
  ['controller', 'Controller'],
  ['memory', 'Memory'],
  ['evolution', 'Evolution'],
];
function safe(text) {
  return String(text ?? '').replace(/[&<>"']/g, ch => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]));
}
function paintBlueprint(data) {
  $('objective').textContent = data.objective;
  $('stages').innerHTML = stages.map(([id, title, desc], index) => `
    <div class="stage" data-stage="${id}">
      <div class="stage-index">${index + 1}</div>
      <div><b>${title}</b><span>${desc}</span></div>
    </div>`).join('');
  $('filters').innerHTML = filterItems.map(([id, label]) => `<div class="filter ${id === 'all' ? 'active' : ''}" data-filter="${id}">${label}</div>`).join('');
  document.querySelectorAll('.filter').forEach(node => node.addEventListener('click', () => {
    activeFilter = node.dataset.filter;
    document.querySelectorAll('.filter').forEach(item => item.classList.toggle('active', item.dataset.filter === activeFilter));
    paintEvents();
  }));
}
async function loadCases() {
  const [casesRes, blueprintRes] = await Promise.all([fetch('/api/cases'), fetch('/api/blueprint')]);
  const payload = await casesRes.json();
  const blueprint = await blueprintRes.json();
  paintBlueprint(blueprint.blueprint);
  $('case-select').innerHTML = payload.cases.map(c => `<option value="${safe(c.id)}">${safe(c.name)} · ${safe(c.type)}</option>`).join('');
  $('case-profile').textContent = '已加载用例列表。启动后会展示本次 case 的结构画像。';
}
function stageForType(type) {
  if (type === 'perception' || type === 'critic_policy') return 'perception';
  if (type === 'round_start') return 'planner';
  if (type === 'attempt_start') return 'executor';
  if (type === 'attempt_result') return 'critic';
  if (type === 'adapt' || type === 'budget' || type === 'fallback') return 'controller';
  if (type === 'best_update' || type === 'final' || type === 'result') return 'memory';
  if (type.startsWith('evolution_')) return 'evolution';
  return 'controller';
}
function readableType(type) {
  return ({
    perception: 'Perception',
    critic_policy: 'Policy',
    round_start: 'Planner',
    attempt_start: 'Executor',
    attempt_result: 'Critic',
    best_update: 'Memory',
    adapt: 'Controller',
    budget: 'Budget',
    fallback: 'Fallback',
    evolution_recall: 'Recall',
    evolution_generate: 'Generate',
    evolution_validate: 'Gate',
    evolution_trial: 'Trial',
    evolution_rollback: 'Rollback',
    final: 'Final',
  })[type] || type;
}
function titleFor(e) {
  if (e.type === 'attempt_start') return `调用 ${e.label || e.strategy}`;
  if (e.type === 'attempt_result') return `${e.label || e.strategy}：${e.accepted ? '进入 Memory' : '暂不采用'}`;
  if (e.type === 'best_update') return 'Memory 更新 best-so-far';
  if (e.type === 'round_start') return `第 ${e.round} 轮策略规划`;
  if (e.type === 'adapt') return 'Controller 调整下一轮';
  if (e.type === 'evolution_recall') return '读取历史生成策略';
  if (e.type === 'evolution_generate') return '生成实验 Python 策略';
  if (e.type === 'evolution_validate') return `安全门禁：${e.passed ? '通过' : '拒绝'}`;
  if (e.type === 'evolution_trial') return `实验策略：${e.accepted ? '接受/晋升' : '回退/拒绝'}`;
  if (e.type === 'evolution_rollback') return '生成策略回退到 stable baseline';
  if (e.type === 'final') return '输出最终 best-so-far';
  return e.message || readableType(e.type);
}
function bodyFor(e) {
  if (e.type === 'attempt_result') {
    return e.accepted ? 'Critic 判断这个候选比当前 Memory 更适合，已保留为新的上下文。' : 'Critic 没有把这个候选作为当前最优，但它仍保留在候选表里便于对比。';
  }
  return e.message || '';
}
function metaFor(e) {
  const meta = [];
  if (e.round) meta.push(`round ${e.round}`);
  if (e.strategy) meta.push(e.strategy);
  if (e.elapsed_ms !== undefined) meta.push(`${Math.round(e.elapsed_ms)} ms`);
  if (e.valid !== undefined) meta.push(e.valid ? 'valid candidate' : 'invalid candidate');
  if (e.time_slice_s !== undefined) meta.push(`slice ${e.time_slice_s}s`);
  if (e.strategy_id) meta.push(e.strategy_id);
  if (e.decision) meta.push(e.decision);
  return meta;
}
function setStage(id, text) {
  document.querySelectorAll('.stage').forEach(node => {
    const isActive = node.dataset.stage === id;
    node.classList.toggle('active', isActive);
    if (isActive) node.classList.add('done');
  });
  $('current-stage').textContent = text;
}
function addEvent(payload) {
  const stage = stageForType(payload.type);
  events.push({...payload, stage});
  $('metric-events').textContent = events.length;
  if (payload.round) $('metric-round').textContent = payload.round;
  if (payload.type === 'attempt_result' && payload.accepted) {
    acceptedCount += 1;
    $('metric-accepted').textContent = acceptedCount;
  }
  paintEvents();
}
function paintEvents() {
  const visible = events.filter(e => activeFilter === 'all' || e.stage === activeFilter);
  if (!visible.length) {
    $('events').innerHTML = '<div class="empty">当前筛选条件下还没有事件。</div>';
    return;
  }
  $('events').innerHTML = visible.map(e => {
    const klass = e.type === 'attempt_result' ? (e.accepted ? 'accepted' : 'rejected') : '';
    const meta = metaFor(e).map(item => `<span class="chip">${safe(item)}</span>`).join('');
    return `<div class="event ${klass}">
      <div class="time">+${safe(e.time_s ?? '0.000')}s</div>
      <div>
        <span class="event-type">${safe(readableType(e.type))}</span>
        <div class="event-title">${safe(titleFor(e))}</div>
        ${compactView ? '' : `<div class="event-body">${safe(bodyFor(e))}</div>`}
        ${meta ? `<div class="event-meta">${meta}</div>` : ''}
      </div>
    </div>`;
  }).join('');
  if (autoScroll) $('events').scrollTop = $('events').scrollHeight;
}
function paintAttempts(report) {
  attempts = report.rounds.flatMap(round => round.strategies.map(s => ({...s, round: round.round})));
  if (!attempts.length) {
    $('rounds').innerHTML = '<div class="empty">这次运行没有记录到候选策略。</div>';
    return;
  }
  $('rounds').innerHTML = attempts.map(s => `
    <div class="attempt ${s.accepted ? 'accepted' : 'rejected'}">
      <div class="name">${safe(s.label || s.name)}</div>
      <div class="why">${safe(s.reason || '策略执行记录')}</div>
      <div class="muted">${Math.round(s.elapsed_ms || 0)} ms · round ${safe(s.round)}</div>
      <div class="verdict">${s.accepted ? 'Memory' : 'Reference'}</div>
    </div>`).join('');
}
function render(report) {
  $('case-profile').textContent = `${report.case_id} · regime ${report.regime} · tasks ${report.features.tasks} · couriers ${report.features.couriers} · rows ${report.features.rows}`;
  $('current-action').textContent = '运行结束，Memory 已输出 best-so-far。';
  setStage('memory', `Agent session finished for ${report.case_id}.`);
  if (report.evolution) {
    $('evolution-note').textContent = `实验策略 ${report.evolution.generated_strategy} 已写入 Evolution Memory；模式 ${report.evolution.mode}。`;
  }
  paintAttempts(report);
}
function resetRun() {
  events = [];
  attempts = [];
  acceptedCount = 0;
  $('metric-events').textContent = '0';
  $('metric-accepted').textContent = '0';
  $('metric-round').textContent = '0';
  $('rounds').innerHTML = '<div class="empty">候选表会在每轮运行后更新：展示每个策略的用途、耗时、以及是否进入 Memory。</div>';
  $('events').innerHTML = '<div class="empty">启动后这里会按时间顺序显示每个 Agent 动作。</div>';
  $('current-stage').textContent = '等待启动。';
  $('current-action').textContent = '还没有工具调用。';
  $('controller-note').textContent = '等待第一轮规划。';
  $('evolution-note').textContent = '等待生成实验策略。';
  document.querySelectorAll('.stage').forEach(node => node.classList.remove('active', 'done'));
}
async function streamRun() {
  if (currentRun) currentRun.close();
  resetRun();
  const button = $('run-agent');
  button.disabled = true;
  $('status').textContent = '运行中';
  $('status').classList.add('running');
  const qs = new URLSearchParams({ case: $('case-select').value, budget: $('budget').value });
  currentRun = new EventSource('/api/stream?' + qs.toString());
  currentRun.addEventListener('start', (ev) => {
    const payload = JSON.parse(ev.data);
    setStage('controller', 'Controller 打开新的 Agent session。');
    $('current-action').textContent = payload.message;
  });
  currentRun.addEventListener('perception', (ev) => {
    const payload = JSON.parse(ev.data);
    addEvent(payload);
    setStage('perception', payload.message);
    const f = payload.features || {};
    $('case-profile').textContent = `tasks ${f.tasks} · couriers ${f.couriers} · rows ${f.rows} · avg willingness ${f.avg_willingness} · bundles ${f.has_bundles ? 'yes' : 'no'}`;
    $('current-action').textContent = '已完成 case 画像，准备规划策略。';
  });
  currentRun.addEventListener('critic_policy', (ev) => {
    const payload = JSON.parse(ev.data);
    addEvent(payload);
    $('current-action').textContent = payload.message;
  });
  currentRun.addEventListener('round_start', (ev) => {
    const payload = JSON.parse(ev.data);
    addEvent(payload);
    setStage('planner', payload.message);
    $('current-action').textContent = `本轮将尝试 ${payload.strategies.length} 个策略。`;
  });
  ['evolution_recall', 'evolution_generate', 'evolution_validate', 'evolution_trial', 'evolution_rollback'].forEach(type => {
    currentRun.addEventListener(type, (ev) => {
      const payload = JSON.parse(ev.data);
      addEvent(payload);
      setStage('evolution', payload.message);
      $('evolution-note').textContent = payload.message;
      $('current-action').textContent = payload.message;
    });
  });
  currentRun.addEventListener('attempt_start', (ev) => {
    const payload = JSON.parse(ev.data);
    addEvent(payload);
    setStage('executor', `${payload.label}: ${payload.message}`);
    $('current-action').textContent = `Executor 正在调用 ${payload.strategy}。`;
  });
  currentRun.addEventListener('attempt_result', (ev) => {
    const payload = JSON.parse(ev.data);
    addEvent(payload);
    setStage('critic', `${payload.label || payload.strategy}: ${payload.accepted ? '进入 Memory' : '暂不采用'}`);
    $('current-action').textContent = payload.accepted ? 'Critic 接受候选，Memory 将更新。' : 'Critic 保留候选作为参考，继续搜索。';
  });
  currentRun.addEventListener('best_update', (ev) => {
    const payload = JSON.parse(ev.data);
    addEvent(payload);
    setStage('memory', payload.message);
    $('current-action').textContent = 'Memory 已保存新的 best-so-far。';
  });
  currentRun.addEventListener('adapt', (ev) => {
    const payload = JSON.parse(ev.data);
    addEvent(payload);
    setStage('controller', payload.message);
    $('controller-note').textContent = payload.message;
  });
  currentRun.addEventListener('budget', (ev) => {
    const payload = JSON.parse(ev.data);
    addEvent(payload);
    setStage('controller', payload.message);
    $('controller-note').textContent = payload.message;
  });
  currentRun.addEventListener('final', (ev) => {
    const payload = JSON.parse(ev.data);
    addEvent(payload);
    setStage('memory', payload.message);
    $('current-action').textContent = payload.message;
  });
  currentRun.addEventListener('result', (ev) => {
    const payload = JSON.parse(ev.data);
    render(payload.report);
    $('status').textContent = '运行完成';
    $('status').classList.remove('running');
    button.disabled = false;
    currentRun.close();
  });
  currentRun.addEventListener('error', () => {
    $('status').textContent = '实时流中断';
    $('status').classList.remove('running');
    button.disabled = false;
  });
}
$('autoscroll').addEventListener('click', () => {
  autoScroll = !autoScroll;
  $('autoscroll').classList.toggle('on', autoScroll);
});
$('compact').addEventListener('click', () => {
  compactView = !compactView;
  $('compact').classList.toggle('on', compactView);
  paintEvents();
});
$('run-agent').addEventListener('click', streamRun);
$('reload-cases').addEventListener('click', loadCases);
loadCases();
</script>
</body>
</html>"""


class AgentRequestHandler(BaseHTTPRequestHandler):
    def _send_json(self, payload: dict[str, object], status: int = 200) -> None:
        raw = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def _send_html(self, html: str) -> None:
        raw = html.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self) -> None:  # noqa: N802 - stdlib handler API.
        parsed = urlparse(self.path)
        try:
            if parsed.path == "/":
                self._send_html(render_index())
                return
            if parsed.path == "/api/blueprint":
                self._send_json({"status": "ok", "blueprint": get_agent_blueprint()})
                return
            if parsed.path == "/api/cases":
                self._send_json({"status": "ok", "cases": list_cases()})
                return
            if parsed.path == "/api/run":
                qs = parse_qs(parsed.query)
                case_id = qs.get("case", ["large_seed301"])[0]
                budget_s = float(qs.get("budget", ["10"])[0])
                self._send_json(build_agent_payload(case_id, budget_s=budget_s))
                return
            if parsed.path == "/api/stream":
                qs = parse_qs(parsed.query)
                case_id = qs.get("case", ["large_seed301"])[0]
                budget_s = float(qs.get("budget", ["10"])[0])
                self.send_response(200)
                self.send_header("Content-Type", "text/event-stream; charset=utf-8")
                self.send_header("Cache-Control", "no-cache")
                self.send_header("Connection", "close")
                self.end_headers()
                self.wfile.write(_sse("start", {"message": f"starting agent session for {case_id}"}))
                self.wfile.flush()

                def observer(event: dict[str, object]) -> None:
                    self.wfile.write(_sse(event["type"], event))
                    self.wfile.flush()

                report = run_case_agent(case_id, budget_s=budget_s, observer=observer)
                self.wfile.write(_sse("result", {"report": report}))
                self.wfile.write(_sse("done", {"message": "stream complete"}))
                self.wfile.flush()
                self.close_connection = True
                return
            self._send_json({"status": "error", "error": "not found"}, status=404)
        except Exception as exc:
            self._send_json(
                {"status": "error", "error": str(exc), "traceback": traceback.format_exc()},
                status=500,
            )

    def log_message(self, format: str, *args: object) -> None:
        print(f"[web-agent] {self.address_string()} - {format % args}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the local AutoSolver Agent web demo.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args(argv)
    server = ThreadingHTTPServer((args.host, args.port), AgentRequestHandler)
    print(f"AutoSolver Agent System running at http://{args.host}:{args.port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down.")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
