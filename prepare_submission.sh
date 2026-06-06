#!/bin/bash
# AutoSolver 官方提交准备脚本

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║         AutoSolver 官方提交准备检查清单                        ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# 1. 最终验证
echo "📋 第一步：最终验证"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

echo "   运行单元测试..."
python3 -m unittest discover -s tests -p 'test_*.py' > /tmp/test_result.txt 2>&1
if [ $? -eq 0 ]; then
    echo "   ✅ 单元测试: 通过"
else
    echo "   ❌ 单元测试: 失败"
    cat /tmp/test_result.txt
    exit 1
fi

echo "   检查solver.py文件..."
if [ -f "solver.py" ]; then
    lines=$(wc -l < solver.py)
    size=$(ls -lh solver.py | awk '{print $5}')
    echo "   ✅ solver.py: 存在 ($lines 行, $size)"
else
    echo "   ❌ solver.py: 不存在"
    exit 1
fi

echo ""

# 2. 生成提交文件信息
echo "📦 第二步：提交文件信息"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

sha256sum solver.py 2>/dev/null || shasum -a 256 solver.py
echo ""

# 3. 提交网址和步骤
echo "🌐 第三步：官方提交步骤"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "   提交网址: https://hackathon.mykeeta.com/"
echo ""
echo "   提交步骤："
echo "   1. 打开浏览器访问: https://hackathon.mykeeta.com/"
echo "   2. 登录你的比赛账号"
echo "   3. 找到「命题四 AutoSolver」提交入口"
echo "   4. 上传文件: solver.py"
echo "   5. 等待系统评测（可能需要几分钟）"
echo "   6. 查看官方成绩"
echo ""

# 4. 预期成果
echo "🎯 第四步：预期成果"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "   基线成绩: 706.197 (10个case平均)"
echo ""
echo "   优化重点:"
echo "   ✓ scarce_couriers_seed401: 39/40 → 40/40 全覆盖"
echo "   ✓ low_willingness_seed501: proxy改善33%"
echo ""
echo "   预期收益:"
echo "   • 如果seed401改善: 可能降低~20-50分"
echo "   • 如果seed501改善: 可能降低~50-200分"
echo "   • 预期总平均分: 600-650 (理想情况)"
echo ""

# 5. 备注信息
echo "📝 第五步：提交备注（建议填写）"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
cat << 'NOTE'
优化说明：
1. 针对seed401扩展beam search (beam_width 5200→6500)
2. 针对seed501增强多派单搜索 (max_k 3→4, option_limit 28→40)
3. 实现seed401从39/40到40/40的全覆盖突破
4. 所有case保持100%任务覆盖，运行时间均<10秒
NOTE
echo ""

# 6. 风险提示
echo "⚠️  第六步：重要提示"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "   • 本地proxy score与官方评分可能有差异"
echo "   • 如果官方成绩不理想，可以回滚到备份版本"
echo "   • 回滚命令: cp solver_backup_20260605_204912.py solver.py"
echo "   • 每日提交次数有限（通常20次），请谨慎提交"
echo ""

# 7. 提交确认
echo "✅ 准备完成！"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📂 提交文件路径:"
echo "   $(pwd)/solver.py"
echo ""
echo "🚀 现在可以前往官方网站提交了！"
echo ""
echo "提交后，请记录官方成绩并与以下对比："
echo "  • 基线: 706.197"
echo "  • seed401基线: 1531.53 (39/40)"
echo "  • seed501基线: 1799.90"
echo ""

# 8. 快速链接
echo "🔗 快速操作"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "   打开提交网址:"
echo "   open https://hackathon.mykeeta.com/"
echo ""
echo "   或手动复制链接到浏览器:"
echo "   https://hackathon.mykeeta.com/"
echo ""

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║  准备完成！祝提交顺利！                                         ║"
echo "╚════════════════════════════════════════════════════════════════╝"
