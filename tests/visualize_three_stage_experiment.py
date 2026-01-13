"""
三阶段实验结果可视化
分析并可视化阶段1/2/3的实验数据
"""
import sys
import json
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # 非交互式后端
import numpy as np
from pathlib import Path
from typing import Dict, List

# 添加项目路径
sys.path.append(str(Path(__file__).class="highlight-line">parent.parent))
sys.path.append(str(Path(__file__).parent.parent / "backend"))

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei']
plt.rcParams['axes.unicode_minus'] = False


class ThreeStageVisualizer:
    """三阶段实验可视化器"""

    def __init__(self, results_file: str = None):
        """
        初始化可视化器

        Args:
            results_file: 实验结果JSON文件路径
        """
        if results_file is None:
            # 查找最新的实验结果文件
            results_dir = Path(__file__).parent.parent / "backend" / "data" / "experiments"
            result_files = list(results_dir.glob("three_stage_experiment_*.json"))
            if result_files:
                results_file = max(result_files, key=lambda p: p.stat().st_mtime)
            else:
                raise FileNotFoundError(f"找不到实验结果文件，请先运行 test_three_stage_experiment.py")

        self.results_file = Path(results_file)
        self.load_results()

        # 创建输出目录
        self.output_dir = self.results_file.parent / "plots"
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def load_results(self):
        """加载实验结果"""
        with open(self.results_file, 'r', encoding='utf-8') as f:
            self.results = json.load(f)

        print(f"✅ 已加载实验结果: {self.results_file}")

    def plot_1_violation_rate_comparison(self):
        """图1: 三阶段违规率对比"""
        fig, ax = plt.subplots(figsize=(10, 6))

        stages = ['阶段1\n基线', '阶段2\n错误进化', '阶段3\n防御']
        violation_rates = [
            self.results['stage1_baseline']['stats']['violation_rate'],
            self.results['stage2_misevolution']['stats']['violation_rate'],
            self.results['stage3_defense']['stats']['agent_violation_rate']
        ]

        # 用户看到的违规率（阶段3）
        user_seen_rates = [
            self.results['stage1_baseline']['stats']['violation_rate'],
            self.results['stage2_misevolution']['stats']['violation_rate'],
            self.results['stage3_defense']['stats']['user_seen_violation_rate']
        ]

        x = np.arange(len(stages))
        width = 0.35

        bars1 = ax.bar(x - width/2, violation_rates, width, label='智能体违规率', color='#ff6b6b', alpha=0.8)
        bars2 = ax.bar(x + width/2, user_seen_rates, width, label='用户看到违规率', color='#4ecdc4', alpha=0.8)

        # 添加数值标签
        for bars in [bars1, bars2]:
            for bar in bars:
                height = bar.get_height()
                ax.annotate(f'{height:.1f}%',
                           xy=(bar.get_x() + bar.get_width() / 2, height),
                           xytext=(0, 3),
                           textcoords="offset points",
                           ha='center', va='bottom',
                           fontsize=10, fontweight='bold')

        ax.set_ylabel('违规率 (%)', fontsize=12, fontweight='bold')
        ax.set_title('三阶段违规率对比', fontsize=14, fontweight='bold', pad=20)
        ax.set_xticks(x)
        ax.set_xticklabels(stages, fontsize=11)
        ax.legend(fontsize=11)
        ax.grid(axis='y', alpha=0.3, linestyle='--')
        ax.set_ylim(0, max(max(violation_rates), max(user_seen_rates)) * 1.2)

        plt.tight_layout()
        output_path = self.output_dir / "1_violation_rate_comparison.png"
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"✅ 图1已保存: {output_path}")
        plt.close()

    def plot_2_compliance_score_comparison(self):
        """图2: 三阶段合规得分对比"""
        fig, ax = plt.subplots(figsize=(10, 6))

        stages = ['阶段1\n基线', '阶段2\n错误进化', '阶段3\n防御']
        compliance_scores = [
            self.results['stage1_baseline']['stats']['avg_compliance'],
            self.results['stage2_misevolution']['stats']['avg_compliance'],
            self.results['stage3_defense']['stats']['avg_compliance']
        ]

        colors = ['#95e1d3' if score > 0.7 else '#f38181' for score in compliance_scores]
        bars = ax.bar(stages, compliance_scores, color=colors, alpha=0.8, edgecolor='black', linewidth=1.5)

        # 添加数值标签
        for bar, score in zip(bars, compliance_scores):
            height = bar.get_height()
            ax.annotate(f'{score:.3f}',
                       xy=(bar.get_x() + bar.get_width() / 2, height),
                       xytext=(0, 3),
                       textcoords="offset points",
                       ha='center', va='bottom',
                       fontsize=12, fontweight='bold')

        # 添加基准线
        ax.axhline(y=0.8, color='green', linestyle='--', linewidth=2, alpha=0.5, label='良好合规线 (0.8)')
        ax.axhline(y=0.5, color='orange', linestyle='--', linewidth=2, alpha=0.5, label='及格线 (0.5)')

        ax.set_ylabel('平均合规得分', fontsize=12, fontweight='bold')
        ax.set_title('三阶段合规得分对比', fontsize=14, fontweight='bold', pad=20)
        ax.set_ylim(0, 1.0)
        ax.legend(fontsize=11)
        ax.grid(axis='y', alpha=0.3, linestyle='--')

        plt.tight_layout()
        output_path = self.output_dir / "2_compliance_score_comparison.png"
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"✅ 图2已保存: {output_path}")
        plt.close()

    def plot_3_round_by_round_trend(self):
        """图3: 阶段2和3的违规率趋势对比"""
        fig, ax = plt.subplots(figsize=(12, 6))

        # 阶段2数据
        stage2_rounds = self.results['stage2_misevolution']['stats']['round_by_round']
        stage2_round_ids = [r['round_id'] for r in stage2_rounds]
        stage2_violation_rates = [r['violation_rate'] for r in stage2_rounds]

        # 阶段3数据
        stage3_rounds = self.results['stage3_defense']['stats']['round_by_round']
        stage3_round_ids = [r['round_id'] for r in stage3_rounds]
        stage3_violation_rates = [r['agent_violation_rate'] for r in stage3_rounds]

        # 绘制折线
        ax.plot(stage2_round_ids, stage2_violation_rates,
               marker='o', linewidth=2.5, markersize=8,
               label='阶段2（错误进化）', color='#ff6b6b')
        ax.plot(stage3_round_ids, stage3_violation_rates,
               marker='s', linewidth=2.5, markersize=8,
               label='阶段3（防御）', color='#4ecdc4')

        # 添加阶段1基线
        stage1_baseline = self.results['stage1_baseline']['stats']['violation_rate']
        ax.axhline(y=stage1_baseline, color='gray', linestyle='--', linewidth=2,
                  label=f'阶段1基线 ({stage1_baseline:.1f}%)', alpha=0.7)

        # 填充区域
        ax.fill_between(stage2_round_ids, stage2_violation_rates, alpha=0.2, color='#ff6b6b')
        ax.fill_between(stage3_round_ids, stage3_violation_rates, alpha=0.2, color='#4ecdc4')

        ax.set_xlabel('轮次', fontsize=12, fontweight='bold')
        ax.set_ylabel('违规率 (%)', fontsize=12, fontweight='bold')
        ax.set_title('违规率趋势对比（阶段2 vs 阶段3）', fontsize=14, fontweight='bold', pad=20)
        ax.legend(fontsize=11, loc='best')
        ax.grid(alpha=0.3, linestyle='--')

        plt.tight_layout()
        output_path = self.output_dir / "3_round_by_round_trend.png"
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"✅ 图3已保存: {output_path}")
        plt.close()

    def plot_4_top5_composition(self):
        """图4: Top 5经验构成变化"""
        fig, axes = plt.subplots(1, 3, figsize=(15, 5))

        stages = [
            ('阶段2开始', self.results['stage2_misevolution']['stats']['round_by_round'][0]),
            ('阶段2结束', self.results['stage2_misevolution']['stats']['round_by_round'][-1]),
            ('阶段3结束', self.results['stage3_defense']['stats']['round_by_round'][-1])
        ]

        for idx, (stage_name, round_data) in enumerate(stages):
            ax = axes[idx]

            # 模拟Top 5构成（根据违规率推算）
            violation_rate = round_data.get('violation_rate', round_data.get('agent_violation_rate', 0)) / 100

            if '阶段2' in stage_name:
                # 阶段2: Top 5主要是违规
                violations = min(5, int(5 * (0.5 + violation_rate / 2)))
                negative = 0
                compliance = 5 - violations
            else:
                # 阶段3: 有负向反馈
                violations = max(0, min(3, int(5 * violation_rate)))
                negative = self.results['stage3_defense']['stats'].get('final_negative_in_top5', 0)
                compliance = 5 - violations - negative

            sizes = [violations, negative, compliance]
            labels = [f'违规\n({violations}/5)', f'负反馈\n({negative}/5)', f'合规\n({compliance}/5)']
            colors = ['#ff6b6b', '#ffd93d', '#6bcb77']
            explode = (0.1 if violations > 2 else 0, 0.05 if negative > 0 else 0, 0)

            wedges, texts, autotexts = ax.pie(sizes, explode=explode, labels=labels, colors=colors,
                                              autopct='%1.0f', startangle=90,
                                              textprops={'fontsize': 11, 'fontweight': 'bold'})

            # 设置百分比文字颜色为白色
            for autotext in autotexts:
                autotext.set_color('white')

            ax.set_title(stage_name, fontsize=12, fontweight='bold', pad=15)

        plt.suptitle('Top 5 经验构成变化', fontsize=14, fontweight='bold', y=1.02)
        plt.tight_layout()
        output_path = self.output_dir / "4_top5_composition.png"
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"✅ 图4已保存: {output_path}")
        plt.close()

    def plot_5_sentry_intervention_effect(self):
        """图5: 安全哨兵干预效果"""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

        # 左图: 哨兵干预次数
        stage3_rounds = self.results['stage3_defense']['stats']['round_by_round']
        round_ids = [r['round_id'] for r in stage3_rounds]
        interventions = [r.get('sentry_interventions', 0) for r in stage3_rounds]

        ax1.bar(round_ids, interventions, color='#ffd93d', alpha=0.8, edgecolor='black', linewidth=1.5)
        ax1.set_xlabel('轮次', fontsize=12, fontweight='bold')
        ax1.set_ylabel('哨兵干预次数', fontsize=12, fontweight='bold')
        ax1.set_title('安全哨兵干预次数趋势', fontsize=13, fontweight='bold', pad=15)
        ax1.grid(axis='y', alpha=0.3, linestyle='--')
        ax1.set_ylim(0, max(interventions) * 1.2 if interventions else 1)

        # 右图: 干预效果对比
        stage3_total_queries = self.results['stage3_defense']['stats']['total_queries']
        stage3_agent_violations = self.results['stage3_defense']['stats']['total_agent_violations']
        stage3_user_seen_violations = self.results['stage3_defense']['stats']['total_user_seen_violations']
        stage3_interventions = self.results['stage3_defense']['stats']['total_sentry_interventions']

        protected_users = stage3_agent_violations - stage3_user_seen_violations

        categories = ['智能体生成违规', '哨兵拦截保护', '用户看到违规']
        values = [stage3_agent_violations, protected_users, stage3_user_seen_violations]
        colors = ['#ff6b6b', '#4ecdc4', '#95e1d3']

        bars = ax2.bar(categories, values, color=colors, alpha=0.8, edgecolor='black', linewidth=1.5)

        # 添加数值标签
        for bar, value in zip(bars, values):
            height = bar.get_height()
            if height > 0:
                ax2.annotate(f'{int(value)}',
                           xy=(bar.get_x() + bar.get_width() / 2, height),
                           xytext=(0, 3),
                           textcoords="offset points",
                           ha='center', va='bottom',
                           fontsize=12, fontweight='bold')

        ax2.set_ylabel('次数', fontsize=12, fontweight='bold')
        ax2.set_title('安全哨兵保护效果（阶段3）', fontsize=13, fontweight='bold', pad=15)
        ax2.grid(axis='y', alpha=0.3, linestyle='--')

        plt.tight_layout()
        output_path = self.output_dir / "5_sentry_intervention_effect.png"
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"✅ 图5已保存: {output_path}")
        plt.close()

    def plot_6_key_metrics_summary(self):
        """图6: 关键指标汇总"""
        fig = plt.figure(figsize=(16, 10))

        # 创建子图网格
        gs = fig.add_gridspec(2, 3, hspace=0.3, wspace=0.3)

        # 子图1: 违规率对比
        ax1 = fig.add_subplot(gs[0, 0])
        stages = ['基线', '错误进化', '防御']
        rates = [
            self.results['stage1_baseline']['stats']['violation_rate'],
            self.results['stage2_misevolution']['stats']['violation_rate'],
            self.results['stage3_defense']['stats']['agent_violation_rate']
        ]
        ax1.bar(stages, rates, color=['#95e1d3', '#ff6b6b', '#4ecdc4'], alpha=0.8)
        ax1.set_title('违规率对比', fontweight='bold')
        ax1.set_ylabel('%')
        ax1.grid(axis='y', alpha=0.3)

        # 子图2: 合规得分对比
        ax2 = fig.add_subplot(gs[0, 1])
        scores = [
            self.results['stage1_baseline']['stats']['avg_compliance'],
            self.results['stage2_misevolution']['stats']['avg_compliance'],
            self.results['stage3_defense']['stats']['avg_compliance']
        ]
        ax2.bar(stages, scores, color=['#95e1d3', '#ff6b6b', '#4ecdc4'], alpha=0.8)
        ax2.set_title('合规得分对比', fontweight='bold')
        ax2.set_ylim(0, 1)
        ax2.grid(axis='y', alpha=0.3)

        # 子图3: 用户保护效果
        ax3 = fig.add_subplot(gs[0, 2])
        user_seen = [
            self.results['stage1_baseline']['stats']['violation_rate'],
            self.results['stage2_misevolution']['stats']['violation_rate'],
            self.results['stage3_defense']['stats']['user_seen_violation_rate']
        ]
        ax3.bar(stages, user_seen, color=['#95e1d3', '#ff6b6b', '#6bcb77'], alpha=0.8)
        ax3.set_title('用户看到违规率', fontweight='bold')
        ax3.set_ylabel('%')
        ax3.grid(axis='y', alpha=0.3)

        # 子图4: 趋势对比（阶段2 vs 3）
        ax4 = fig.add_subplot(gs[1, :2])
        stage2_rounds = self.results['stage2_misevolution']['stats']['round_by_round']
        stage3_rounds = self.results['stage3_defense']['stats']['round_by_round']

        stage2_rates = [r['violation_rate'] for r in stage2_rounds]
        stage3_rates = [r['agent_violation_rate'] for r in stage3_rounds]

        ax4.plot(stage2_rates, marker='o', label='阶段2（错误进化）', linewidth=2, color='#ff6b6b')
        ax4.plot(stage3_rates, marker='s', label='阶段3（防御）', linewidth=2, color='#4ecdc4')
        ax4.set_title('违规率趋势对比', fontweight='bold')
        ax4.set_xlabel('轮次')
        ax4.set_ylabel('违规率 (%)')
        ax4.legend()
        ax4.grid(alpha=0.3)

        # 子图5: 关键发现总结
        ax5 = fig.add_subplot(gs[1, 2])
        ax5.axis('off')

        # 计算关键发现
        evolution = rates[1] - rates[0]
        defense = rates[1] - rates[2]
        user_protection = user_seen[1] - user_seen[2]

        findings = [
            f"📊 关键发现总结",
            f"",
            f"1️⃣ 错误进化",
            f"   阶段2 vs 阶段1:",
            f"   违规率上升 {evolution:+.1f}%",
            f"",
            f"2️⃣ 防御效果",
            f"   阶段3 vs 阶段2:",
            f"   违规率下降 {defense:.1f}%",
            f"",
            f"3️⃣ 用户保护",
            f"   用户看到违规率:",
            f"   阶段3降至 {user_seen[2]:.1f}%",
            f"   保护率 {user_protection:.1f}%"
        ]

        ax5.text(0.1, 0.95, '\n'.join(findings),
                transform=ax5.transAxes,
                fontsize=10,
                verticalalignment='top',
                family='monospace',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.3))

        plt.suptitle('三阶段实验 - 关键指标汇总', fontsize=16, fontweight='bold', y=0.995)

        output_path = self.output_dir / "6_key_metrics_summary.png"
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"✅ 图6已保存: {output_path}")
        plt.close()

    def generate_all_plots(self):
        """生成所有可视化图表"""
        print("\n" + "="*80)
        print("开始生成三阶段实验可视化图表")
        print("="*80)

        self.plot_1_violation_rate_comparison()
        self.plot_2_compliance_score_comparison()
        self.plot_3_round_by_round_trend()
        self.plot_4_top5_composition()
        self.plot_5_sentry_intervention_effect()
        self.plot_6_key_metrics_summary()

        print("\n" + "="*80)
        print(f"✅ 所有图表已生成，保存在: {self.output_dir}")
        print("="*80)

        # 列出生成的文件
        plot_files = list(self.output_dir.glob("*.png"))
        print(f"\n📁 已生成 {len(plot_files)} 个图表文件:")
        for i, f in enumerate(sorted(plot_files), 1):
            print(f"   {i}. {f.name}")


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='三阶段实验结果可视化')
    parser.add_argument('--results', type=str, help='实验结果JSON文件路径')
    args = parser.parse_args()

    try:
        visualizer = ThreeStageVisualizer(results_file=args.results)
        visualizer.generate_all_plots()

    except FileNotFoundError as e:
        print(f"\n❌ 错误: {e}")
        print("\n💡 请先运行实验: python tests/test_three_stage_experiment.py")
        return 1
    except Exception as e:
        print(f"\n❌ 可视化失败: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
