"""
多权重对比实验数据可视化脚本

基于论文《Your Agent May Misevolve》生成权重对比图表:
1. 不同权重配置的违规率对比柱状图
2. 违规率 vs 短期权重趋势图
3. 满意度、奖励等指标对比图
"""
import sys
import json
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
from typing import Dict, Any
from datetime import datetime

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False


class WeightComparisonVisualizer:
    """权重对比实验可视化器"""

    def __init__(self, data_file: str = None):
        """
        初始化可视化器

        Args:
            data_file: 实验数据文件路径
        """
        if data_file:
            self.load_data(data_file)

    def load_data(self, filepath: str):
        """加载对比实验数据"""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        self.summary = data['summary']
        print(f"✓ 加载数据: {filepath}")
        print(f"  配置数量: {len(self.summary)}")

    def plot_violation_rate_comparison(self, save_path: str = None):
        """
        绘制违规率对比柱状图

        Args:
            save_path: 保存路径
        """
        configs = list(self.summary.keys())
        violation_rates = [self.summary[c]['statistics']['violation_rate'] for c in configs]
        short_weights = [self.summary[c]['config']['short_term_weight'] for c in configs]

        # 按短期权重排序
        sorted_indices = np.argsort(short_weights)[::-1]
        configs_sorted = [configs[i] for i in sorted_indices]
        violation_rates_sorted = [violation_rates[i] for i in sorted_indices]
        short_weights_sorted = [short_weights[i] for i in sorted_indices]

        fig, ax = plt.subplots(figsize=(10, 6))

        colors = ['#ff7f0e', '#2ca02c', '#1f77b4']  # 橙、绿、蓝

        bars = ax.bar(configs_sorted, violation_rates_sorted, color=colors, alpha=0.7, edgecolor='black')

        # 在柱子上标注数值
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{height:.1f}%',
                   ha='center', va='bottom', fontsize=12, fontweight='bold')

        ax.set_ylabel('违规率 (%)', fontsize=12, fontweight='bold')
        ax.set_title('不同权重配置的违规率对比（论文核心假设验证）', fontsize=14, fontweight='bold')
        ax.set_ylim(0, max(violation_rates_sorted) * 1.2)
        ax.grid(axis='y', alpha=0.3)

        # 添加短期权重标注
        for i, (config, weight) in enumerate(zip(configs_sorted, short_weights_sorted)):
            ax.text(i, max(violation_rates_sorted) * 1.1,
                   f'短期权重={weight:.1f}',
                   ha='center', fontsize=10, style='italic')

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"✓ 违规率对比图已保存: {save_path}")
        else:
            plt.show()

        plt.close()

    def plot_violation_rate_trend(self, save_path: str = None):
        """
        绘制违规率 vs 短期权重趋势图

        Args:
            save_path: 保存路径
        """
        short_weights = [self.summary[c]['config']['short_term_weight'] for c in self.summary.keys()]
        violation_rates = [self.summary[c]['statistics']['violation_rate'] for c in self.summary.keys()]

        # 按短期权重排序
        sorted_data = sorted(zip(short_weights, violation_rates), key=lambda x: x[0])
        short_weights_sorted, violation_rates_sorted = zip(*sorted_data)

        fig, ax = plt.subplots(figsize=(10, 6))

        # 绘制趋势线
        ax.plot(short_weights_sorted, violation_rates_sorted,
               'o-', linewidth=3, markersize=12, color='#d62728', label='违规率')

        # 填充区域
        ax.fill_between(short_weights_sorted, violation_rates_sorted, alpha=0.3, color='#d62728')

        # 标注数据点
        for x, y in zip(short_weights_sorted, violation_rates_sorted):
            ax.text(x, y + max(violation_rates_sorted) * 0.02,
                   f'{y:.1f}%',
                   ha='center', va='bottom', fontsize=11, fontweight='bold')

        ax.set_xlabel('短期权重 (short_term_weight)', fontsize=12, fontweight='bold')
        ax.set_ylabel('违规率 (%)', fontsize=12, fontweight='bold')
        ax.set_title('违规率随短期权重的变化趋势（论文核心发现）', fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3)
        ax.legend(fontsize=11)

        # 添加论文假设标注
        ax.text(0.5, max(violation_rates_sorted) * 0.5,
               '论文假设: 短期权重 ↑ → 违规率 ↑',
               ha='center', fontsize=12, style='italic',
               bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"✓ 违规率趋势图已保存: {save_path}")
        else:
            plt.show()

        plt.close()

    def plot_multi_metrics_comparison(self, save_path: str = None):
        """
        绘制多指标对比图（违规率、满意度、奖励）

        Args:
            save_path: 保存路径
        """
        configs = list(self.summary.keys())
        short_weights = [self.summary[c]['config']['short_term_weight'] for c in configs]

        # 按短期权重排序
        sorted_indices = np.argsort(short_weights)[::-1]
        configs_sorted = [configs[i] for i in sorted_indices]

        violation_rates = [self.summary[c]['statistics']['violation_rate'] for c in configs_sorted]
        satisfactions = [self.summary[c]['statistics']['avg_satisfaction'] for c in configs_sorted]
        total_rewards = [self.summary[c]['statistics']['avg_total_reward'] for c in configs_sorted]

        fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(16, 5))

        # 子图1: 违规率
        colors1 = ['#ff7f0e', '#2ca02c', '#1f77b4']
        bars1 = ax1.bar(configs_sorted, violation_rates, color=colors1, alpha=0.7, edgecolor='black')
        for bar in bars1:
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height,
                    f'{height:.1f}%', ha='center', va='bottom', fontsize=11, fontweight='bold')
        ax1.set_ylabel('违规率 (%)', fontsize=11, fontweight='bold')
        ax1.set_title('违规率对比', fontsize=12, fontweight='bold')
        ax1.set_ylim(0, max(violation_rates) * 1.2)
        ax1.grid(axis='y', alpha=0.3)

        # 子图2: 满意度
        bars2 = ax2.bar(configs_sorted, satisfactions, color=colors1, alpha=0.7, edgecolor='black')
        for bar in bars2:
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2., height,
                    f'{height:.2f}', ha='center', va='bottom', fontsize=11, fontweight='bold')
        ax2.set_ylabel('平均满意度 (1-5)', fontsize=11, fontweight='bold')
        ax2.set_title('满意度对比', fontsize=12, fontweight='bold')
        ax2.set_ylim(1, 5)
        ax2.grid(axis='y', alpha=0.3)

        # 子图3: 总奖励
        bars3 = ax3.bar(configs_sorted, total_rewards, color=colors1, alpha=0.7, edgecolor='black')
        for bar in bars3:
            height = bar.get_height()
            ax3.text(bar.get_x() + bar.get_width()/2., height,
                    f'{height:.3f}', ha='center', va='bottom', fontsize=11, fontweight='bold')
        ax3.set_ylabel('平均总奖励', fontsize=11, fontweight='bold')
        ax3.set_title('总奖励对比', fontsize=12, fontweight='bold')
        ax3.set_ylim(0, max(total_rewards) * 1.2)
        ax3.grid(axis='y', alpha=0.3)

        plt.suptitle('多权重配置的多维度对比分析', fontsize=14, fontweight='bold', y=1.02)
        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"✓ 多指标对比图已保存: {save_path}")
        else:
            plt.show()

        plt.close()

    def plot_reward_decomposition_comparison(self, save_path: str = None):
        """
        绘制即时奖励vs延迟奖励的对比图

        Args:
            save_path: 保存路径
        """
        configs = list(self.summary.keys())
        short_weights = [self.summary[c]['config']['short_term_weight'] for c in configs]

        # 按短期权重排序
        sorted_indices = np.argsort(short_weights)[::-1]
        configs_sorted = [configs[i] for i in sorted_indices]

        immediate_rewards = [self.summary[c]['statistics']['avg_immediate_reward'] for c in configs_sorted]
        delayed_rewards = [self.summary[c]['statistics']['avg_delayed_reward'] for c in configs_sorted]

        x = np.arange(len(configs_sorted))
        width = 0.35

        fig, ax = plt.subplots(figsize=(10, 6))

        bars1 = ax.bar(x - width/2, immediate_rewards, width, label='即时奖励',
                      color='#2ca02c', alpha=0.7, edgecolor='black')
        bars2 = ax.bar(x + width/2, delayed_rewards, width, label='延迟奖励',
                      color='#d62728', alpha=0.7, edgecolor='black')

        # 标注数值
        for bars in [bars1, bars2]:
            for bar in bars:
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height,
                       f'{height:.3f}', ha='center', va='bottom' if height > 0 else 'top',
                       fontsize=10)

        ax.set_xlabel('权重配置', fontsize=12, fontweight='bold')
        ax.set_ylabel('平均奖励值', fontsize=12, fontweight='bold')
        ax.set_title('即时奖励 vs 延迟奖励对比（论文核心：奖励时序错配）',
                    fontsize=14, fontweight='bold')
        ax.set_xticks(x)
        ax.set_xticklabels(configs_sorted)
        ax.legend(fontsize=11)
        ax.grid(axis='y', alpha=0.3)
        ax.axhline(y=0, color='black', linestyle='-', linewidth=0.5)

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"✓ 奖励分解对比图已保存: {save_path}")
        else:
            plt.show()

        plt.close()

    def generate_all_plots(self, output_dir: str = None):
        """生成所有图表"""
        if output_dir is None:
            output_dir = str(Path(__file__).parent / "data" / "experiments" / "plots")
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        print("\n开始生成权重对比图表...")
        print("="*80)

        self.plot_violation_rate_comparison(
            save_path=str(output_path / f"violation_rate_comparison_{timestamp}.png")
        )

        self.plot_violation_rate_trend(
            save_path=str(output_path / f"violation_rate_trend_{timestamp}.png")
        )

        self.plot_multi_metrics_comparison(
            save_path=str(output_path / f"multi_metrics_comparison_{timestamp}.png")
        )

        self.plot_reward_decomposition_comparison(
            save_path=str(output_path / f"reward_decomposition_comparison_{timestamp}.png")
        )

        print("="*80)
        print(f"✓ 所有图表已生成并保存到: {output_dir}")
        print("\n📊 生成的图表:")
        print("  1. violation_rate_comparison - 违规率对比柱状图")
        print("  2. violation_rate_trend - 违规率vs短期权重趋势图")
        print("  3. multi_metrics_comparison - 多指标综合对比")
        print("  4. reward_decomposition_comparison - 即时vs延迟奖励对比")


def main():
    """主函数"""
    print("\n" + "="*80)
    print("权重对比实验数据可视化")
    print("基于论文《Your Agent May Misevolve》")
    print("="*80)

    # 查找最新的对比实验数据文件
    # 搜索多个可能的位置
    possible_paths = [
        Path(__file__).parent / "data" / "experiments",  # 正确路径
        Path(__file__).parent.parent / "backend" / "data" / "experiments",  # 旧路径（兼容）
        Path(__file__).parent.parent / "data" / "experiments",  # 备用路径
    ]

    data_files = []
    for data_dir in possible_paths:
        files = list(data_dir.glob("weight_comparison_*.json"))
        if files:
            data_files.extend(files)
            break

    if not data_files:
        print("\n❌ 未找到权重对比实验数据文件!")
        print("请先运行: python compare_weights_experiment.py")
        return

    # 使用最新的数据文件
    latest_file = max(data_files, key=lambda p: p.stat().st_mtime)
    print(f"\n使用数据文件: {latest_file}")

    # 创建可视化器
    visualizer = WeightComparisonVisualizer(str(latest_file))

    # 生成所有图表
    visualizer.generate_all_plots()

    print("\n🎉 可视化完成!")
    print("\n💡 论文核心验证:")
    print("  • 短期权重越高 → 违规率越高（论文假设）")
    print("  • 奖励时序错配对智能体行为的影响")
    print("  • 不同权重配置下的综合表现对比")

    print("="*80)


if __name__ == "__main__":
    main()
