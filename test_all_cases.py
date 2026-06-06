#!/usr/bin/env python3
"""测试所有case的优化效果"""
import time
from pathlib import Path
from solver import solve, _solution_expected_cost

def parse_input(text):
    lines = text.strip().splitlines()
    if lines and lines[0].startswith("task_id"):
        lines = lines[1:]
    cands = []
    all_tasks = set()
    for ln in lines:
        parts = ln.split("\t")
        if len(parts) < 4:
            continue
        task_str = parts[0]
        task_list = tuple(x.strip() for x in task_str.replace("[", "").replace("]", "").split(",") if x.strip())
        courier = parts[1].strip()
        score = float(parts[2])
        will = float(parts[3])
        cands.append((task_str, list(task_list), courier, score, will, len(cands)))
        for t in task_list:
            all_tasks.add(t)
    return cands, sorted(all_tasks)

def test_case(case_name, file_path):
    print(f"\n{'='*60}")
    print(f"Testing: {case_name}")
    print('='*60)

    with open(file_path) as f:
        text = f.read()

    cands, all_tasks = parse_input(text)

    start = time.time()
    result = solve(text)
    elapsed = time.time() - start

    # 计算覆盖率
    lut = {(c[0], c[2]): c for c in cands}
    covered = set()
    for task_str, couriers in result:
        for cid in couriers:
            r = lut.get((task_str, cid))
            if r is not None:
                covered.update(r[1])
                break

    # 计算proxy score
    try:
        proxy_score = _solution_expected_cost(result, cands, all_tasks)
    except:
        proxy_score = None

    print(f"Time: {elapsed:.2f}s")
    print(f"Groups: {len(result)}")
    print(f"Coverage: {len(covered)}/{len(all_tasks)}")
    if proxy_score:
        print(f"Proxy Score: {proxy_score:.4f}")

    return {
        'case': case_name,
        'time': elapsed,
        'groups': len(result),
        'coverage': f"{len(covered)}/{len(all_tasks)}",
        'proxy_score': proxy_score
    }

if __name__ == '__main__':
    test_cases = [
        ('tiny_seed42', 'web_agent_demo/generated_cases/tiny_seed42.txt'),
        ('small_seed100', 'web_agent_demo/generated_cases/small_seed100.txt'),
        ('medium_seed201', 'web_agent_demo/generated_cases/medium_seed201.txt'),
        ('medium_seed202', 'web_agent_demo/generated_cases/medium_seed202.txt'),
        ('medium_seed203', 'web_agent_demo/generated_cases/medium_seed203.txt'),
        ('high_noise_seed601', 'web_agent_demo/generated_cases/high_noise_seed601.txt'),
        ('scarce_couriers_seed401', 'runs/tmp_scarce_proxy.txt'),
        ('low_willingness_seed501', 'runs/official_calibrated_low_synth.txt'),
        ('large_seed301', 'Fwd_ 【美团AI Hackathon大赛】-【命题四AutoSolver：让AI Agent 自主求解配送分配问题】脱敏数据/large_seed301.txt'),
    ]

    results = []
    for case_name, file_path in test_cases:
        if Path(file_path).exists():
            result = test_case(case_name, file_path)
            results.append(result)
        else:
            print(f"\nSkipping {case_name} - file not found: {file_path}")

    print(f"\n{'='*60}")
    print("SUMMARY")
    print('='*60)
    print(f"{'Case':<30} {'Time':>8} {'Coverage':>12} {'Proxy Score':>12}")
    print('-'*60)
    for r in results:
        score_str = f"{r['proxy_score']:.2f}" if r['proxy_score'] else "N/A"
        print(f"{r['case']:<30} {r['time']:>7.2f}s {r['coverage']:>12} {score_str:>12}")
