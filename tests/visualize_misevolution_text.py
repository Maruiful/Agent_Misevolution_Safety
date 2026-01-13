"""
文本模式可视化错误进化实验结果
不需要matplotlib，直接在终端显示图表
"""
import json
from pathlib import Path
from datetime import datetime


def load_latest_result():
    """加载最新的实验结果"""
    results_dir = Path(__file__).parent.parent / "backend" / "data" / "experiments"

    # 找到最新的结果文件
    result_files = list(results_dir.glob("quick_misevolution_*.json"))
    if not result_files:
        print("❌ 未找到实验结果文件")
        return None

    latest_file = max(result_files, key=lambda f: f.stat().st_mtime)
    print(f"📂 加载结果文件: {latest_file.name}")

    with open(latest_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    return data


def plot_text_chart(data):
    """文本模式绘制图表"""

    if not data:
        return

    round_stats = data['round_by_round']
    config = data['config']
    summary = data['summary']

    # 提取数据
    rounds = [rs['round_id'] for rs in round_stats]
    violation_rates = [rs['violation_rate'] for rs in round_stats]
    violations = [rs['violations'] for rs in round_stats]
    compliance = [rs['compliance'] for rs in round_stats]

    print("\n" + "="*80)
    print("📊 错误进化实验结果可视化")
    print("="*80)

    # === 图1: 违规率曲线（ASCII艺术） ===
    print("\n" + "┌"+"─"*78+"┐")
    print("│"+" "*30+"违规率进化曲线"+" "*32+"│")
    print("├"+"─"*78+"┤")

    # Y轴标签
    print("│ 100% │                                                          │")
    print("│      │                                                          │")

    # 绘制曲线
    for y in range(90, -10, -10):
        line = f"│ {y:3d}% │"
        for x in range(len(rounds)):
            rate = violation_rates[x]
            # 判断是否在这个高度画点
            if abs(rate - y) < 5:  # 在±5%范围内
                line += "   ●"
            elif rate > y:
                line += "   │"
            else:
                line += "    "

        line += "   │"
        print(line)

    print("│      │"+"─"*76+"│")
    print("│    0 │")

    # X轴标签
    x_labels = "     │"
    for i, r in enumerate(rounds):
        x_labels += f"  R{r} "
    x_labels += "   │"
    print(x_labels)
    print("└"+"─"*78+"┘")

    # === 图2: 柱状图（违规数 vs 合规数） ===
    print("\n" + "┌"+"─"*78+"┐")
    print("│"+" "*28+"违规数 vs 合规数"+" "*34+"│")
    print("├"+"─"*78+"┤")

    # 找出最大值用于缩放
    max_count = max(max(violations), max(compliance))

    for i, r in enumerate(rounds):
        v = violations[i]
        c = compliance[i]

        # 计算柱子高度（每行代表5个）
        v_bars = "█" * (v * 40 // max_count)
        c_bars = "█" * (c * 40 // max_count)

        print(f"│ Round {r}: │")
        print(f"│   违规: {v:2d} {v_bars:<40} │")
        print(f"│   合规: {c:2d} {c_bars:<40} │")
        print("│          │")

    print("└"+"─"*78+"┘")

    # === 数据表格 ===
    print("\n" + "┌"+"─"*78+"┐")
    print("│"+" "*32+"详细数据"+" "*34+"│")
    print("├"+"─"*78+"┤")
    print("│  轮次  │  违规率  │  违规数  │  合规数  │     趋势     │")
    print("├"+"─"*78+"┤")

    for i, r in enumerate(rounds):
        trend = ""
        if i == 0:
            trend = "基线"
        elif violation_rates[i] > violation_rates[i-1]:
            trend = f"↑ +{violation_rates[i] - violation_rates[i-1]:.0f}%"
        elif violation_rates[i] < violation_rates[i-1]:
            trend = f"↓ {violation_rates[i] - violation_rates[i-1]:.0f}%"
        else:
            trend = "→ 持平"

        print(f"│  Round {r}  │  {violation_rates[i]:5.1f}%  │    {violations[i]:2d}   │    {compliance[i]:2d}   │   {trend:^10}  │")

    print("└"+"─"*78+"┘")

    # === 实验配置 ===
    print("\n" + "┌"+"─"*78+"┐")
    print("│"+" "*32+"实验配置"+" "*34+"│")
    print("├"+"─"*78+"┤")
    print(f"│  测试轮数:     {config['num_rounds']}轮" + " "*55 + "│")
    print(f"│  每轮测试数:   {config['test_cases']}个" + " "*55 + "│")
    print(f"│  Temperature:  {config['temperature']}" + " "*55 + "│")
    print(f"│  预先注入违规: {'是' if config.get('pre_injected', True) else '否'}" + " "*51 + "│")
    print("└"+"─"*78+"┘")

    # === 实验结果总结 ===
    print("\n" + "┌"+"─"*78+"┐")
    print("│"+" "*32+"实验结果"+" "*34+"│")
    print("├"+"─"*78+"┤")
    print(f"│  总查询数:       {summary['total_queries']}" + " "*51 + "│")
    print(f"│  总违规数:       {summary['total_violations']}" + " "*51 + "│")
    print(f"│  平均违规率:     {summary['avg_violation_rate']:.1f}%" + " "*51 + "│")
    print(f"│  趋势变化:       {summary['trend']:+.1f}%" + " "*51 + "│")
    print(f"│  初始违规率:     {violation_rates[0]:.0f}%" + " "*53 + "│")
    print(f"│  最终违规率:     {violation_rates[-1]:.0f}%" + " "*53 + "│")
    print("└"+"─"*78+"┘")

    # === 进化阶段分析 ===
    print("\n" + "🔍 进化阶段分析:")
    print("─"*80)

    if violation_rates[0] < 30:
        print(f"✅ 第1轮: 初始合规阶段（违规率={violation_rates[0]:.0f}% < 30%）")
        print(f"   → 安全对齐主导，智能体依赖初始RLHF训练")
        print(f"   → 模型仍然遵守安全规范")

    if len(violation_rates) > 1:
        jump = violation_rates[1] - violation_rates[0]
        if jump > 20:
            print(f"\n⚠️  第2轮: 快速学习阶段（违规率跃升 {jump:+.0f}%）")
            print(f"   → 记忆库开始污染，发现'违规=高分'模式")
            print(f"   → Few-shot学习开始生效，模仿高分违规案例")
        else:
            print(f"\n📊 第2轮: 缓慢适应阶段（违规率变化 {jump:+.0f}%）")

    # 计算增长率
    growth_rate = (violation_rates[-1] - violation_rates[0]) / violation_rates[0] * 100 if violation_rates[0] > 0 else 0

    print(f"\n📈 增长率分析:")
    print(f"   → 从第1轮的{violation_rates[0]:.0f}%增长到第{len(rounds)}轮的{violation_rates[-1]:.0f}%")
    print(f"   → 总增长率: {growth_rate:+.0f}%")

    if growth_rate > 200:
        print(f"   ✅ 强烈验证错误进化假设！")
        print(f"   ✅ 论文《Your Agent May Misevolve》的核心假设得到有力支持！")
    elif growth_rate > 100:
        print(f"   ✅ 支持错误进化假设")
        print(f"   → 违规率显著上升，奖励猎取现象明显")
    elif growth_rate > 50:
        print(f"   ⚠️  轻度支持进化假设")
        print(f"   → 违规率有所上升，但不够强烈")
    else:
        print(f"   ⚠️  不支持进化假设")
        print(f"   → 违规率相对稳定")

    # === 关键发现 ===
    print(f"\n🎯 关键发现:")

    # 找到最大跃升
    max_jump = 0
    max_jump_round = 0
    for i in range(1, len(violation_rates)):
        jump = violation_rates[i] - violation_rates[i-1]
        if jump > max_jump:
            max_jump = jump
            max_jump_round = i + 1

    if max_jump > 0:
        print(f"   • 最大跃升发生在第{max_jump_round}轮（+{max_jump:.0f}%）")
        print(f"   → 这表明智能体在第{max_jump_round-1}轮后学会了违规模式")

    if violation_rates[-1] > 70:
        print(f"   • 最终违规率超过70%，进入'崩溃阶段'")
        print(f"   → 奖励猎取完全主导，严重偏离原始目标")

    print("\n" + "="*80)

    # 保存文本报告
    output_dir = Path(__file__).parent.parent / "backend" / "data" / "experiments"
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = output_dir / f"misevolution_report_{timestamp}.txt"

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("="*80 + "\n")
        f.write("错误进化实验结果报告\n")
        f.write("="*80 + "\n\n")

        f.write("实验配置:\n")
        f.write(f"  - 测试轮数: {config['num_rounds']}轮\n")
        f.write(f"  - 每轮测试数: {config['test_cases']}个\n")
        f.write(f"  - Temperature: {config['temperature']}\n")
        f.write(f"  - 预先注入违规: {'是' if config.get('pre_injected', True) else '否'}\n\n")

        f.write("实验结果:\n")
        f.write(f"  - 平均违规率: {summary['avg_violation_rate']:.1f}%\n")
        f.write(f"  - 趋势变化: {summary['trend']:+.1f}%\n")
        f.write(f"  - 增长率: {growth_rate:+.0f}%\n\n")

        f.write("逐轮数据:\n")
        for i, r in enumerate(rounds):
            f.write(f"  Round {r}: {violation_rates[i]:.0f}% (违规:{violations[i]}, 合规:{compliance[i]})\n")

    print(f"\n💾 报告已保存: {output_path}")


if __name__ == "__main__":
    data = load_latest_result()

    if data:
        plot_text_chart(data)
        print("\n✅ 可视化完成！")
    else:
        print("\n❌ 无法加载数据")
