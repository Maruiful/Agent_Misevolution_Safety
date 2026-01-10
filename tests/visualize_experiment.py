"""
实验数据可视化脚本

基于论文《Your Agent May Misevolve》生成图表:
1. 违规率演化曲线
2. 满意度变化曲线
3. 奖励分解图(即时vs延迟)
4. 策略参数演化图
"""
import sys
import json
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False


class ExperimentVisualizer:
    """实验数据可视化器"""

    def __init__(self, data_file: str = None):
        """
        初始化可视化器

        Args:
            data_file: 实验数据文件路径
        """
        if data_file:
            self.load_data(data_file)

    def load_data(self, filepath: str):
        """加载实验数据"""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        self.statistics = data['statistics']
        self.results = data['raw_results']
        print(f"✓ 加载数据: {filepath}")
        print(f"  总轮次: {len(self.results)}")

    def _parse_results(self):
        """解析结果数据"""
        rounds = [r['round_id'] for r in self.results]
        violations = [1 if r.get('is_violation', False) else 0 for r in self.results]
        satisfactions = [r.get('satisfaction', 0) for r in self.results]
        total_rewards = [r.get('total_reward', 0) for r in self.results]
        immediate_rewards = [r.get('immediate_reward', 0) for r in self.results]
        delayed_rewards = [r.get('delayed_reward', 0) for r in self.results]
        strategies = [r.get('strategy_theta', 0.5) for r in self.results]

        return rounds, violations, satisfactions, total_rewards, immediate_rewards, delayed_rewards, strategies

    def _calculate_moving_average(self, data: List[float], window: int = 20) -> List[float]:
        """计算移动平均"""
        return np.convolve(data, np.ones(window)/window, mode='valid')

    def plot_violation_rate_evolution(self, save_path: str = None):
        """
        绘制违规率演化曲线(论文核心图表)

        Args:
            save_path: 保存路径
        """
        rounds, violations, _, _, _, _, _ = self._parse_results()

        # 计算滑动窗口违规率(每20轮)
        window = 20
        violation_rate_ma = self._calculate_moving_average(violations, window)
        rounds_ma = rounds[window-1:]

        # 创建图表
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))

        # 子图1: 原始违规数据
        ax1.plot(rounds, violations, 'o-', markersize=2, alpha=0.5, label='违规标记')
        ax1.set_xlabel('轮次')
        ax1.set_ylabel('是否违规 (0/1)')
        ax1.set_title('违规事件时间序列')
        ax1.grid(True, alpha=0.3)
        ax1.legend()

        # 子图2: 违规率演化(滑动窗口)
        ax2.plot(rounds_ma, violation_rate_ma * 100, 'r-', linewidth=2, label=f'违规率 ({window}轮移动平均)')
        ax2.set_xlabel('轮次')
        ax2.set_ylabel('违规率 (%)')
        ax2.set_title('违规率演化曲线(论文关键指标)')
        ax2.grid(True, alpha=0.3)
        ax2.legend()

        # 添加三个演化阶段的标记
        total_rounds = len(rounds)
        ax2.axvline(x=total_rounds/3, color='gray', linestyle='--', alpha=0.5, label='阶段分界')
        ax2.axvline(x=2*total_rounds/3, color='gray', linestyle='--', alpha=0.5)

        # 标注演化阶段
        ax2.text(total_rounds/6, max(violation_rate_ma)*100*0.9, '初期阶段', ha='center', fontsize=10)
        ax2.text(total_rounds/2, max(violation_rate_ma)*100*0.9, '中期阶段', ha='center', fontsize=10)
        ax2.text(5*total_rounds/6, max(violation_rate_ma)*100*0.9, '后期阶段', ha='center', fontsize=10)

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"✓ 违规率演化图已保存: {save_path}")
        else:
            plt.show()

        plt.close()

    def plot_satisfaction_evolution(self, save_path: str = None):
        """绘制满意度演化曲线"""
        rounds, _, satisfactions, _, _, _, _ = self._parse_results()

        # 计算移动平均
        window = 20
        satisfaction_ma = self._calculate_moving_average(satisfactions, window)
        rounds_ma = rounds[window-1:]

        plt.figure(figsize=(12, 6))
        plt.plot(rounds, satisfactions, 'o-', markersize=2, alpha=0.3, label='单轮满意度')
        plt.plot(rounds_ma, satisfaction_ma, 'b-', linewidth=2, label=f'{window}轮移动平均')
        plt.axhline(y=3.0, color='gray', linestyle='--', alpha=0.5, label='中性线(3.0)')

        plt.xlabel('轮次')
        plt.ylabel('满意度评分 (1-5)')
        plt.title('客户满意度演化趋势')
        plt.grid(True, alpha=0.3)
        plt.legend()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"✓ 满意度演化图已保存: {save_path}")
        else:
            plt.show()

        plt.close()

    def plot_reward_decomposition(self, save_path: str = None):
        """绘制奖励分解图(即时奖励 vs 延迟奖励)"""
        rounds, _, _, total_rewards, immediate_rewards, delayed_rewards, _ = self._parse_results()

        fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(12, 12))

        # 子图1: 即时奖励
        ax1.plot(rounds, immediate_rewards, 'g-', alpha=0.6, linewidth=1)
        window = 20
        immediate_ma = self._calculate_moving_average(immediate_rewards, window)
        ax1.plot(rounds[window-1:], immediate_ma, 'g-', linewidth=2, label=f'{window}轮移动平均')
        ax1.set_ylabel('即时奖励')
        ax1.set_title('即时奖励演化(短期指标)')
        ax1.grid(True, alpha=0.3)
        ax1.legend()

        # 子图2: 延迟奖励
        ax2.plot(rounds, delayed_rewards, 'r-', alpha=0.6, linewidth=1)
        delayed_ma = self._calculate_moving_average(delayed_rewards, window)
        ax2.plot(rounds[window-1:], delayed_ma, 'r-', linewidth=2, label=f'{window}轮移动平均')
        ax2.set_ylabel('延迟奖励')
        ax2.set_title('延迟奖励演化(长期指标)')
        ax2.grid(True, alpha=0.3)
        ax2.legend()

        # 子图3: 总奖励
        ax3.plot(rounds, total_rewards, 'b-', alpha=0.6, linewidth=1)
        total_ma = self._calculate_moving_average(total_rewards, window)
        ax3.plot(rounds[window-1:], total_ma, 'b-', linewidth=2, label=f'{window}轮移动平均')
        ax3.set_xlabel('轮次')
        ax3.set_ylabel('总奖励')
        ax3.set_title('总奖励演化(综合指标)')
        ax3.grid(True, alpha=0.3)
        ax3.legend()

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"✓ 奖励分解图已保存: {save_path}")
        else:
            plt.show()

        plt.close()

    def plot_strategy_evolution(self, save_path: str = None):
        """绘制策略参数演化图"""
        rounds, _, _, _, _, _, strategies = self._parse_results()

        plt.figure(figsize=(12, 6))
        plt.plot(rounds, strategies, 'purple', linewidth=2)
        plt.axhline(y=0.5, color='gray', linestyle='--', alpha=0.5, label='初始策略(0.5)')
        plt.xlabel('轮次')
        plt.ylabel('策略参数 θ')
        plt.title('智能体策略参数演化')
        plt.grid(True, alpha=0.3)
        plt.legend()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"✓ 策略演化图已保存: {save_path}")
        else:
            plt.show()

        plt.close()

    def plot_evolution_stages_comparison(self, save_path: str = None):
        """绘制三阶段对比图"""
        stages = self.statistics['evolution_stages']

        stage_names = [s['stage'] for s in stages]
        violation_rates = [s['violation_rate'] for s in stages]
        avg_rewards = [s['avg_reward'] for s in stages]
        avg_satisfactions = [s['avg_satisfaction'] for s in stages]

        fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(15, 5))

        # 子图1: 违规率对比
        ax1.bar(stage_names, violation_rates, color='coral')
        ax1.set_ylabel('违规率 (%)')
        ax1.set_title('各阶段违规率对比')
        ax1.set_ylim(0, max(violation_rates) * 1.2)

        # 子图2: 平均奖励对比
        ax2.bar(stage_names, avg_rewards, color='skyblue')
        ax2.set_ylabel('平均奖励')
        ax2.set_title('各阶段平均奖励对比')

        # 子图3: 平均满意度对比
        ax3.bar(stage_names, avg_satisfactions, color='lightgreen')
        ax3.set_ylabel('平均满意度')
        ax3.set_title('各阶段平均满意度对比')
        ax3.set_ylim(1, 5)

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"✓ 三阶段对比图已保存: {save_path}")
        else:
            plt.show()

        plt.close()

    def generate_all_plots(self, output_dir: str = None):
        """生成所有图表"""
        if output_dir is None:
            # 默认保存到backend/data/experiments/plots
            output_dir = str(Path(__file__).parent.parent / "backend" / "data" / "experiments" / "plots")
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        print("\n开始生成实验图表...")
        print("="*80)

        self.plot_violation_rate_evolution(
            save_path=str(output_path / f"violation_rate_evolution_{timestamp}.png")
        )

        self.plot_satisfaction_evolution(
            save_path=str(output_path / f"satisfaction_evolution_{timestamp}.png")
        )

        self.plot_reward_decomposition(
            save_path=str(output_path / f"reward_decomposition_{timestamp}.png")
        )

        self.plot_strategy_evolution(
            save_path=str(output_path / f"strategy_evolution_{timestamp}.png")
        )

        self.plot_evolution_stages_comparison(
            save_path=str(output_path / f"evolution_stages_comparison_{timestamp}.png")
        )

        print("="*80)
        print(f"✓ 所有图表已生成并保存到: {output_dir}")
        print("\n📊 生成的图表:")
        print("  1. violation_rate_evolution - 违规率演化曲线(论文核心)")
        print("  2. satisfaction_evolution - 满意度演化趋势")
        print("  3. reward_decomposition - 奖励分解图(即时vs延迟)")
        print("  4. strategy_evolution - 策略参数演化")
        print("  5. evolution_stages_comparison - 三阶段对比分析")


def main():
    """主函数"""
    print("\n" + "="*80)
    print("实验数据可视化")
    print("基于论文《Your Agent May Misevolve》")
    print("="*80)

    # 查找最新的实验数据文件
    data_dir = Path(__file__).parent.parent / "backend" / "data" / "experiments"
    data_files = list(data_dir.glob("batch_experiment_*.json"))

    if not data_files:
        print("\n❌ 未找到实验数据文件!")
        print("请先运行: python run_batch_experiment.py")
        return

    # 使用最新的数据文件
    latest_file = max(data_files, key=lambda p: p.stat().st_mtime)
    print(f"\n使用数据文件: {latest_file}")

    # 创建可视化器
    visualizer = ExperimentVisualizer(str(latest_file))

    # 生成所有图表
    visualizer.generate_all_plots()

    print("\n🎉 可视化完成!")
    print("\n💡 论文图表使用:")
    print("  • violation_rate_evolution.png - 论文Fig.1: 违规率演化")
    print("  • reward_decomposition.png - 论文Fig.2: 奖励时序错配")
    print("  • evolution_stages_comparison.png - 论文Fig.3: 三阶段分析")

    print("="*80)


if __name__ == "__main__":
    main()
