"""
安全哨兵防御效果可视化

对比有/无安全哨兵的实验结果,生成可视化图表
"""
import sys
import json
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
from typing import Dict, List
from datetime import datetime

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False


class SentryDefenseVisualizer:
    """安全哨兵防御效果可视化器"""

    def __init__(self, data_file: str = None):
        """
        初始化可视化器

        Args:
            data_file: 评估数据文件路径
        """
        if data_file:
            self.load_data(data_file)

    def load_data(self, filepath: str):
        """加载评估数据"""
        with open(filepath, 'r', encoding='utf-8') as f:
            self.data = json.load(f)

        self.results_without = self.data["without_sentry"]["results"]
        self.results_with = self.data["with_sentry"]["results"]
        self.metrics_without = self.data["without_sentry"]["metrics"]
        self.metrics_with = self.data["with_sentry"]["metrics"]

        print(f"[OK] 加载数据: {filepath}")
        print(f"  测试轮次: {self.data['test_rounds']}")

    def plot_violation_rate_comparison(self, save_path: str = None):
        """
        绘制违规率对比柱状图

        Args:
            save_path: 保存路径
        """
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

        # 子图1: 违规率对比
        categories = ['无防御', '有防御']
        violation_rates = [
            self.metrics_without.get("violation_rate", 0),
            self.metrics_with.get("violation_rate", 0)
        ]
        colors = ['#e74c3c', '#2ecc71']

        bars = ax1.bar(categories, violation_rates, color=colors, alpha=0.7, edgecolor='black')
        ax1.set_ylabel('违规率 (%)', fontsize=12, fontweight='bold')
        ax1.set_title('违规率对比', fontsize=14, fontweight='bold')
        ax1.set_ylim(0, max(violation_rates) * 1.2 if max(violation_rates) > 0 else 10)
        ax1.grid(axis='y', alpha=0.3)

        # 标注数值
        for bar in bars:
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height,
                    f'{height:.1f}%', ha='center', va='bottom', fontsize=12, fontweight='bold')

        # 子图2: 改善效果
        improvement = ((violation_rates[0] - violation_rates[1]) / max(violation_rates[0], 1)) * 100

        # 使用箭头显示改善
        ax2.arrow(0.5, violation_rates[0], 0, violation_rates[1] - violation_rates[0],
                 head_width=0.05, head_length=0.5, fc='blue', ec='blue', alpha=0.7)
        ax2.plot([0.5, 0.5], [0, violation_rates[0]], 'ro', markersize=15)
        ax2.plot([0.5, 0.5], [0, violation_rates[1]], 'go', markersize=15)
        ax2.set_xlim(0, 1)
        ax2.set_ylim(0, max(violation_rates) * 1.2 if max(violation_rates) > 0 else 10)
        ax2.set_xticks([])
        ax2.set_ylabel('违规率 (%)', fontsize=12, fontweight='bold')
        ax2.set_title(f'防御效果: 降低 {improvement:.1f}%', fontsize=14, fontweight='bold')
        ax2.text(0.5, violation_rates[0], f'{violation_rates[0]:.1f}%', ha='right', va='bottom', fontsize=10)
        ax2.text(0.5, violation_rates[1], f'{violation_rates[1]:.1f}%', ha='right', va='top', fontsize=10)
        ax2.grid(axis='y', alpha=0.3)

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"[OK] 违规率对比图已保存: {save_path}")
        else:
            plt.show()

        plt.close()

    def plot_interception_statistics(self, save_path: str = None):
        """
        绘制拦截统计图

        Args:
            save_path: 保存路径
        """
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(14, 12))

        # 子图1: 拦截率 vs 违规率
        metrics = ['拦截率', '违规率']
        with_sentry_values = [
            self.metrics_with.get("block_rate", 0),
            self.metrics_with.get("violation_rate", 0)
        ]
        colors = ['#3498db', '#e74c3c']

        bars1 = ax1.bar(metrics, with_sentry_values, color=colors, alpha=0.7, edgecolor='black')
        ax1.set_ylabel('百分比 (%)', fontsize=11, fontweight='bold')
        ax1.set_title('有防御模式: 拦截率 vs 违规率', fontsize=12, fontweight='bold')
        ax1.set_ylim(0, 100)
        ax1.grid(axis='y', alpha=0.3)

        for bar in bars1:
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height,
                    f'{height:.1f}%', ha='center', va='bottom', fontsize=11, fontweight='bold')

        # 子图2: 精确率 vs 召回率
        metrics_pr = ['精确率\n(Precision)', '召回率\n(Recall)']
        pr_values = [
            self.metrics_with.get("precision", 0),
            self.metrics_with.get("recall", 0)
        ]

        bars2 = ax2.bar(metrics_pr, pr_values, color=['#9b59b6', '#1abc9c'], alpha=0.7, edgecolor='black')
        ax2.set_ylabel('百分比 (%)', fontsize=11, fontweight='bold')
        ax2.set_title('拦截性能指标', fontsize=12, fontweight='bold')
        ax2.set_ylim(0, 100)
        ax2.grid(axis='y', alpha=0.3)

        for bar in bars2:
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2., height,
                    f'{height:.1f}%', ha='center', va='bottom', fontsize=11, fontweight='bold')

        # 子图3: 拦截类型分布
        blocked_by_type = {}
        for r in self.results_with:
            if r["sentry_blocked"]:
                alert_type = r["sentry_alert_type"] or "unknown"
                blocked_by_type[alert_type] = blocked_by_type.get(alert_type, 0) + 1

        if blocked_by_type:
            types = list(blocked_by_type.keys())
            counts = list(blocked_by_type.values())

            # 按数量排序
            sorted_indices = np.argsort(counts)[::-1]
            types_sorted = [types[i] for i in sorted_indices]
            counts_sorted = [counts[i] for i in sorted_indices]

            bars3 = ax3.barh(types_sorted, counts_sorted, color='#e67e22', alpha=0.7, edgecolor='black')
            ax3.set_xlabel('拦截次数', fontsize=11, fontweight='bold')
            ax3.set_title('拦截类型分布', fontsize=12, fontweight='bold')
            ax3.grid(axis='x', alpha=0.3)

            # 标注数值
            for bar in bars3:
                width = bar.get_width()
                ax3.text(width, bar.get_y() + bar.get_height()/2.,
                        f'{int(width)}', ha='left', va='center', fontsize=10)

        # 子图4: 时间序列对比
        window = 10
        rounds = range(len(self.results_without))

        # 计算滑动窗口违规率
        def calc_ma_violation_rate(results, window):
            violation_flags = [1 if r["is_violation"] else 0 for r in results]
            ma_rates = []
            for i in range(window, len(violation_flags)):
                rate = sum(violation_flags[i-window:i]) / window * 100
                ma_rates.append(rate)
            return ma_rates

        ma_without = calc_ma_violation_rate(self.results_without, window)
        ma_with = calc_ma_violation_rate(self.results_with, window)
        x_axis = range(window, len(self.results_without))

        ax4.plot(x_axis, ma_without, 'r-', linewidth=2, label='无防御', alpha=0.7)
        ax4.plot(x_axis, ma_with, 'g-', linewidth=2, label='有防御', alpha=0.7)
        ax4.set_xlabel('轮次', fontsize=11, fontweight='bold')
        ax4.set_ylabel(f'违规率 (%)({window}轮MA)', fontsize=11, fontweight='bold')
        ax4.set_title('违规率时间演化对比', fontsize=12, fontweight='bold')
        ax4.legend(fontsize=10)
        ax4.grid(alpha=0.3)

        plt.suptitle('安全哨兵拦截统计分析', fontsize=14, fontweight='bold', y=0.995)
        plt.tight_layout(rect=[0, 0, 1, 0.99])

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"[OK] 拦截统计图已保存: {save_path}")
        else:
            plt.show()

        plt.close()

    def plot_satisfaction_reward_comparison(self, save_path: str = None):
        """
        绘制满意度和奖励对比图

        Args:
            save_path: 保存路径
        """
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

        # 子图1: 满意度对比
        categories = ['无防御', '有防御']
        satisfactions = [
            self.metrics_without.get("avg_satisfaction", 0),
            self.metrics_with.get("avg_satisfaction", 0)
        ]

        bars1 = ax1.bar(categories, satisfactions, color=['#e74c3c', '#2ecc71'], alpha=0.7, edgecolor='black')
        ax1.set_ylabel('平均满意度 (1-5分)', fontsize=12, fontweight='bold')
        ax1.set_title('客户满意度对比', fontsize=14, fontweight='bold')
        ax1.set_ylim(1, 5)
        ax1.grid(axis='y', alpha=0.3)

        for bar in bars1:
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height,
                    f'{height:.2f}', ha='center', va='bottom', fontsize=12, fontweight='bold')

        # 添加目标线
        ax1.axhline(y=3.0, color='gray', linestyle='--', alpha=0.5, label='中性线')
        ax1.legend()

        # 子图2: 平均奖励对比
        rewards = [
            self.metrics_without.get("avg_reward", 0),
            self.metrics_with.get("avg_reward", 0)
        ]

        bars2 = ax2.bar(categories, rewards, color=['#e74c3c', '#2ecc71'], alpha=0.7, edgecolor='black')
        ax2.set_ylabel('平均总奖励', fontsize=12, fontweight='bold')
        ax2.set_title('总奖励对比', fontsize=14, fontweight='bold')
        ax2.set_ylim(0, max(rewards) * 1.2 if max(rewards) > 0 else 1)
        ax2.grid(axis='y', alpha=0.3)

        for bar in bars2:
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2., height,
                    f'{height:.3f}', ha='center', va='bottom', fontsize=12, fontweight='bold')

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"[OK] 满意度奖励对比图已保存: {save_path}")
        else:
            plt.show()

        plt.close()

    def generate_summary_report(self, output_path: str = None) -> str:
        """
        生成总结报告

        Args:
            output_path: 报告保存路径

        Returns:
            报告文本
        """
        report_lines = []
        report_lines.append("="*80)
        report_lines.append("安全哨兵防御效果评估报告")
        report_lines.append("="*80)
        report_lines.append("")

        # 基本信息
        report_lines.append("【一、评估概况】")
        report_lines.append(f"测试时间: {self.data.get('timestamp', 'N/A')}")
        report_lines.append(f"测试轮次: {self.data.get('test_rounds', 0)}")
        report_lines.append("")

        # 核心指标对比
        report_lines.append("【二、核心指标对比】")
        report_lines.append(f"{'指标':<30} {'无防御':>15} {'有防御':>15} {'改善':>15}")
        report_lines.append("-"*80)

        vr_without = self.metrics_without.get("violation_rate", 0)
        vr_with = self.metrics_with.get("violation_rate", 0)
        vr_improvement = ((vr_without - vr_with) / max(vr_without, 1)) * 100
        report_lines.append(f"{'违规率 (%)':<30} {vr_without:>15.1f} {vr_with:>15.1f} {vr_improvement:>+14.1f}%")

        br = self.metrics_with.get("block_rate", 0)
        report_lines.append(f"{'拦截率 (%)':<30} {'N/A':>15} {br:>15.1f} {'':>15}")

        precision = self.metrics_with.get("precision", 0)
        recall = self.metrics_with.get("recall", 0)
        report_lines.append(f"{'精确率 (%)':<30} {'N/A':>15} {precision:>15.1f} {'':>15}")
        report_lines.append(f"{'召回率 (%)':<30} {'N/A':>15} {recall:>15.1f} {'':>15}")

        sat_without = self.metrics_without.get("avg_satisfaction", 0)
        sat_with = self.metrics_with.get("avg_satisfaction", 0)
        sat_improvement = ((sat_with - sat_without) / max(sat_without, 1)) * 100
        report_lines.append(f"{'平均满意度':<30} {sat_without:>15.2f} {sat_with:>15.2f} {sat_improvement:>+14.1f}%")

        reward_without = self.metrics_without.get("avg_reward", 0)
        reward_with = self.metrics_with.get("avg_reward", 0)
        reward_improvement = ((reward_with - reward_without) / max(abs(reward_without), 1)) * 100
        report_lines.append(f"{'平均总奖励':<30} {reward_without:>15.3f} {reward_with:>15.3f} {reward_improvement:>+14.1f}%")

        report_lines.append("")

        # 评估结论
        report_lines.append("【三、评估结论】")

        if vr_improvement > 50:
            report_lines.append("[OK] 安全哨兵防御效果显著,违规率降低超过50%")
        elif vr_improvement > 20:
            report_lines.append("[OK] 安全哨兵防御效果良好,违规率降低超过20%")
        elif vr_improvement > 0:
            report_lines.append("[!]️ 安全哨兵防御有一定效果,但仍有改进空间")
        else:
            report_lines.append("[X] 安全哨兵防御效果不明显,需要优化检测规则")

        if recall > 80:
            report_lines.append("[OK] 拦截召回率高,能有效发现违规行为")
        elif recall > 50:
            report_lines.append("[!]️ 拦截召回率中等,部分违规行为未被拦截")
        else:
            report_lines.append("[X] 拦截召回率低,需要优化检测规则")

        if precision > 80:
            report_lines.append("[OK] 拦截精确率高,误报率低")
        elif precision > 50:
            report_lines.append("[!]️ 拦截精确率中等,存在一定误报")
        else:
            report_lines.append("[X] 拦截精确率低,误报率较高")

        report_lines.append("")

        # 建议
        report_lines.append("【四、改进建议】")
        if vr_improvement < 50:
            report_lines.append("- 优化违规检测规则,提高覆盖率")
            report_lines.append("- 增加LLM层检测,提升语义理解能力")

        if recall < 80:
            report_lines.append("- 提高召回率,减少漏检")
            report_lines.append("- 分析未拦截的违规案例,补充检测规则")

        if precision < 80:
            report_lines.append("- 提高精确率,减少误报")
            report_lines.append("- 优化正则表达式,避免过度匹配")

        report_lines.append("")
        report_lines.append("="*80)
        report_lines.append(f"报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append("="*80)

        report_text = "\n".join(report_lines)

        # 保存报告
        if output_path:
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(report_text)
            print(f"[OK] 评估报告已保存: {output_path}")

        return report_text

    def generate_all_plots(self, output_dir: str = None):
        """生成所有图表"""
        if output_dir is None:
            output_dir = str(Path(__file__).parent.parent / "backend" / "data" / "experiments" / "plots")
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        print("\n开始生成防御效果图表...")
        print("="*80)

        self.plot_violation_rate_comparison(
            save_path=str(output_path / f"sentry_violation_rate_comparison_{timestamp}.png")
        )

        self.plot_interception_statistics(
            save_path=str(output_path / f"sentry_interception_stats_{timestamp}.png")
        )

        self.plot_satisfaction_reward_comparison(
            save_path=str(output_path / f"sentry_satisfaction_reward_{timestamp}.png")
        )

        # 生成报告
        report_path = output_path / f"sentry_defense_report_{timestamp}.txt"
        self.generate_summary_report(output_path=str(report_path))

        print("="*80)
        print(f"[OK] 所有图表已生成并保存到: {output_dir}")
        print("\n📊 生成的图表:")
        print("  1. sentry_violation_rate_comparison - 违规率对比")
        print("  2. sentry_interception_stats - 拦截统计分析")
        print("  3. sentry_satisfaction_reward - 满意度奖励对比")
        print("  4. sentry_defense_report - 详细评估报告")


def main():
    """主函数"""
    import glob

    print("\n" + "="*80)
    print("安全哨兵防御效果可视化")
    print("="*80)

    # 查找最新的评估数据文件
    data_dir = Path(__file__).parent.parent / "backend" / "data" / "experiments"
    data_files = list(data_dir.glob("sentry_defense_evaluation_*.json"))

    if not data_files:
        print("\n[X] 未找到评估数据文件!")
        print("请先运行: python evaluate_sentry_defense.py")
        return

    # 使用最新的数据文件
    latest_file = max(data_files, key=lambda p: p.stat().st_mtime)
    print(f"\n使用数据文件: {latest_file}")

    # 创建可视化器
    visualizer = SentryDefenseVisualizer(str(latest_file))

    # 生成所有图表
    visualizer.generate_all_plots()

    print("\n🎉 可视化完成!")
    print("="*80)


if __name__ == "__main__":
    main()
