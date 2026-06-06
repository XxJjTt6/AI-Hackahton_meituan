#!/bin/bash
# AutoSolver 优化版本快速启动指南

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║         AutoSolver 优化版本 - 快速启动指南                     ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# 1. 验证单元测试
echo "1️⃣  运行单元测试..."
python3 -m unittest discover -s tests -p 'test_*.py' 2>&1 | tail -3
echo ""

# 2. 运行完整基准测试
echo "2️⃣  运行完整基准测试..."
echo "   (可能需要30-60秒)"
python3 test_all_cases.py 2>&1 | grep "SUMMARY" -A 12
echo ""

# 3. 查看优化变更
echo "3️⃣  优化变更摘要:"
echo "   • seed401: 覆盖率 39/40 → 40/40 ✓"
echo "   • seed501: proxy 1799 → 1199 (-33%)"
echo "   • 变更数: 3处参数调整"
echo ""

# 4. 文件清单
echo "4️⃣  相关文件清单:"
echo "   ✓ solver.py                  - 优化后的求解器"
echo "   ✓ solver_backup_*.py         - 原始版本备份"
echo "   ✓ OPTIMIZATION_README.md     - 完整优化报告"
echo "   ✓ OPTIMIZATION_SUMMARY.md    - 优化总结"
echo "   ✓ OPTIMIZATION_DIFF.txt      - 代码变更对比"
echo "   ✓ test_all_cases.py          - 完整测试脚本"
echo "   ✓ final_report.py            - 最终报告生成器"
echo ""

# 5. 下一步行动
echo "5️⃣  下一步行动建议:"
echo "   [ ] 查看详细报告: cat OPTIMIZATION_README.md"
echo "   [ ] 运行官方验证: python3 runs/official_submit_safe.py --solver solver.py --skip-submit"
echo "   [ ] 准备提交: 确认所有测试通过后使用官方提交工具"
echo "   [ ] 回滚版本: cp solver_backup_*.py solver.py (如需回退)"
echo ""

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║  优化完成！推荐进行官方提交验证。                              ║"
echo "╚════════════════════════════════════════════════════════════════╝"
