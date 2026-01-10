"""
测试批量实验功能

快速验证批量实验脚本是否正常工作(只运行50轮)
"""
import asyncio
import sys
from pathlib import Path

# 添加backend目录到路径
backend_path = str(Path(__file__).parent.parent / "backend")
sys.path.insert(0, backend_path)

# 设置环境变量文件路径
import os
os.chdir(backend_path)

from tests.run_batch_experiment import BatchExperimentRunner


async def main():
    """主测试函数"""
    print("\n" + "="*80)
    print("批量实验功能测试(50轮)")
    print("="*80)

    # 创建实验运行器(只运行50轮用于测试)
    runner = BatchExperimentRunner(total_rounds=50)

    # 初始化
    await runner.initialize()

    # 运行实验
    print("\n开始运行50轮实验...")
    results = await runner.run_experiment()

    # 生成统计
    stats = runner.generate_statistics()

    # 打印总结
    runner.print_summary()

    # 保存结果
    runner.save_results()

    print("\n" + "="*80)
    print("测试结果验证:")
    print("="*80)

    # 验证关键指标
    assert len(results) == 50, f"预期50轮结果,实际{len(results)}轮"
    print("✓ 轮次数量正确: 50")

    assert 'experiment_info' in stats, "缺少experiment_info"
    print("✓ 统计数据结构正确")

    assert 'evolution_stages' in stats, "缺少evolution_stages"
    print("✓ 演化阶段分析正确")

    assert 'overall_stats' in stats, "缺少overall_stats"
    print("✓ 总体统计正确")

    violation_rate = stats['overall_stats']['violation_rate']
    print(f"✓ 违规率: {violation_rate:.2f}%")

    avg_reward = stats['overall_stats']['avg_total_reward']
    print(f"✓ 平均奖励: {avg_reward:.3f}")

    print("\n" + "="*80)
    print("🎉 批量实验功能测试通过!")
    print("\n💡 说明:")
    print("  • 测试模式: 50轮(快速验证)")
    print("  • 完整实验: 500轮(运行 python run_batch_experiment.py)")
    print("  • 数据可视化: python visualize_experiment.py")
    print("="*80)


if __name__ == "__main__":
    asyncio.run(main())
