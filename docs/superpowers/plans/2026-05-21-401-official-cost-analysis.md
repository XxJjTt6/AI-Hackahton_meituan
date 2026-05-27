# 401 Official Cost Analysis Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build an offline 401 analysis tool that extracts official observed row costs and searches safe local alternatives without changing `solver.py`.

**Architecture:** Keep production solver frozen. Add a standalone script under `runs/` that reads historical official logs and current solver cache, builds a known official-cost table, then runs exact set-packing over known rows and reports only evidence-backed candidates.

**Tech Stack:** Python standard library, existing `solver.py` helpers when importable, JSON/Markdown run artifacts.

---

### Task 1: Create Analyzer Skeleton

**Files:**
- Create: `runs/analyze_401_official_costs.py`
- Output: `runs/401_official_cost_analysis_latest.md`

- [ ] **Step 1:** Parse `runs/official_submit_20260521_*.json` and collect any scarce/401 result details.
- [ ] **Step 2:** Parse current `solver.py` hard-cache solution using `solve()` against available 401 data if present.
- [ ] **Step 3:** Build a known row table keyed by `(task_key, courier_tuple)`.
- [ ] **Step 4:** Run exact set-packing over known rows with task/courier conflict constraints.
- [ ] **Step 5:** Write a Markdown report comparing best known reconstruction against `1531.5317`.

### Task 2: Run Analyzer

**Files:**
- Read: `runs/analyze_401_official_costs.py`
- Output: `runs/401_official_cost_analysis_latest.md`

- [ ] **Step 1:** Run `python3 runs/analyze_401_official_costs.py`.
- [ ] **Step 2:** Inspect whether any known official-cost solution beats `1531.5317`.
- [ ] **Step 3:** If no safe improvement exists, identify missing high-value row costs to probe later.

### Task 3: Decide Solver Integration

**Files:**
- Optional Modify: `solver.py`

- [ ] **Step 1:** Only modify `solver.py` if the report finds an evidence-backed improvement.
- [ ] **Step 2:** Otherwise leave `solver.py` unchanged and preserve submissions.
