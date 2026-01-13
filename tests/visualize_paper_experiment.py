"""
论文风格实验可视化脚本
基于《Your Agent May Misevolve》实验结果的可视化分析
"""
import json
import matplotlib
matplotlib.use('Agg')  # 使用非交互式后端
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any
import seaborn as sns
import platform

# 设置中文字体 - Windows系统
if platform.system() == 'Windows':
    # 尝试多个常见的Windows中文字体
    font_names = [
        'Microsoft YaHei',  # 微软雅黑
        'SimHei',  # 黑体
        'SimSun',  # 宋体
        'KaiTi',  # 楷体
        'FangSong',  # 仿宋
    ]

    # 找到系统中可用的中文字体
    available_fonts = [f.name for f in fm.fontManager.ttflist]
    selected_font = None

    for font_name in font_names:
        if font_name in available_fonts:
            selected_font = font_name
            print(f"使用中文字体: {font_name}")
            break

    if selected_font:
        plt.rcParams['font.sans-serif'] = [selected_font] + plt.rcParams['font.sans-serif']
    else:
        print("警告: 未找到可用的中文字体，文字可能显示为方框")
        print(f"可用字体: {available_fonts[:10]}...")  # 显示前10个字体
else:
    # 非Windows系统
    plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'DejaVu Sans']

plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题
plt.rcParams['font.size'] = 10

# 设置seaborn样式
sns.set_style("whitegrid")
plt.rcParams['figure.facecolor'] = 'white'
plt.rcParams['axes.facecolor'] = 'white'


def load_latest_experiment():
    """加载最新的实验结果"""
    # 获取脚本所在目录
    script_dir = Path(__file__).parent

    # 获取项目根目录（tests的父目录）
    project_root = script_dir.parent

    # 尝试多个可能的路径
    possible_paths = [
        script_dir / "data" / "experiments",  # tests/data/experiments
        project_root / "backend" / "tests" / "data" / "experiments",  # backend/tests/data/experiments
        project_root / "tests" / "data" / "experiments",  # tests/data/experiments (根目录下)
        Path("../backend/tests/data/experiments").resolve(),  # 相对路径
    ]

    files = []
    for exp_dir in possible_paths:
        print(f"尝试路径: {exp_dir}")
        if exp_dir.exists():
            matched_files = list(exp_dir.glob("paper_style_experiment_*.json"))
            if matched_files:
                files = matched_files
                print(f"找到 {len(files)} 个文件")
                break

    if not files:
        raise FileNotFoundError(
            f"未找到实验结果文件。\n" +
            f"脚本目录: {script_dir}\n" +
            f"项目根目录: {project_root}\n" +
            f"当前工作目录: {Path.cwd()}\n" +
            "已搜索路径：\n" +
            "\n".join(f"  - {p}" for p in possible_paths)
        )

    latest_file = max(files, key=lambda f: f.stat().st_mtime)
    print(f"加载实验结果: {latest_file}")

    with open(latest_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    return data, latest_file


def create_violation_rate_plot(evolution_data: List[Dict], save_path: str):
    """
    创建违规率折线图

    展示100轮实验中违规率的变化趋势，
    重点标注第20-30轮的策略漂移期
    """
    rounds = [r['round'] for r in evolution_data]
    violations = [1 if r['is_violation'] else 0 for r in evolution_data]

    # 计算移动平均（每10轮）
    window_size = 10
    moving_avg = []
    moving_rounds = []

    for i in range(window_size, len(violations) + 1):
        window = violations[i-window_size:i]
        moving_avg.append(sum(window) / window_size * 100)
        moving_rounds.append(rounds[i-1])

    # 创建图表
    fig, ax = plt.subplots(figsize=(14, 7))

    # 绘制原始数据（散点）
    colors = ['#e74c3c' if v else '#27ae60' for v in violations]
    ax.scatter(rounds, [v * 100 for v in violations],
              c=colors, alpha=0.3, s=30, label='单轮结果')

    # 绘制移动平均线
    ax.plot(moving_rounds, moving_avg,
           color='#e74c3c', linewidth=2.5, marker='o',
           markersize=4, label='10轮移动平均', zorder=5)

    # 标注策略漂移期（第20-30轮）
    ax.axvspan(20, 30, alpha=0.3, color='#f39c12',
              label='策略漂移期 (20-30轮)')

    # 添加关键点标注
    drift_point = moving_avg[2]  # 第30轮
    ax.annotate(f'峰值: {drift_point:.1f}%',
               xy=(30, drift_point),
               xytext=(35, drift_point + 10),
               fontsize=11, fontweight='bold',
               bbox=dict(boxstyle='round,pad=0.5',
                        facecolor='#f39c12', alpha=0.7),
               arrowprops=dict(arrowstyle='->', lw=2, color='#f39c12'))

    # 标题和标签
    ax.set_xlabel('轮次', fontsize=13, fontweight='bold')
    ax.set_ylabel('违规率 (%)', fontsize=13, fontweight='bold')
    ax.set_title('智能体进化过程中的违规率变化\n基于《Your Agent May Misevolve》论文实验',
                fontsize=15, fontweight='bold', pad=20)

    # 网格和图例
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.legend(loc='upper left', fontsize=11)

    # Y轴范围
    ax.set_ylim(-5, 105)
    ax.set_yticks(range(0, 101, 20))

    # X轴范围
    ax.set_xlim(0, 100)
    ax.set_xticks(range(0, 101, 10))

    plt.tight_layout()
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    print(f"✅ 违规率折线图已保存: {save_path}")
    plt.close()


def create_stage_comparison_chart(analysis: Dict, save_path: str):
    """
    创建阶段对比柱状图

    对比基线、早期、中期（策略漂移期）、后期的违规率
    """
    stages = ['基线\n(无记忆)',
              '早期\n(1-20轮)',
              '⚠️ 策略漂移期\n(20-30轮)',
              '后期\n(30-100轮)']

    rates = [
        analysis['baseline_violation_rate'],
        analysis['early_stage_rate'],
        analysis['mid_stage_rate'],
        analysis['late_stage_rate']
    ]

    # 颜色方案
    colors = ['#3498db', '#27ae60', '#e74c3c', '#9b59b6']

    # 创建图表
    fig, ax = plt.subplots(figsize=(12, 7))

    bars = ax.bar(stages, rates, color=colors,
                 edgecolor='white', linewidth=2, alpha=0.8)

    # 添加数值标签
    for bar, rate in zip(bars, rates):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + 1,
               f'{rate:.1f}%',
               ha='center', va='bottom',
               fontsize=12, fontweight='bold')

    # 标题和标签
    ax.set_ylabel('违规率 (%)', fontsize=13, fontweight='bold')
    ax.set_title('不同阶段的违规率对比\n策略漂移期（20-30轮）违规率最高',
                fontsize=15, fontweight='bold', pad=20)

    # 网格
    ax.grid(True, alpha=0.3, linestyle='--', axis='y')
    ax.set_axisbelow(True)

    # Y轴范围
    ax.set_ylim(0, max(rates) * 1.2)

    plt.tight_layout()
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    print(f"✅ 阶段对比图已保存: {save_path}")
    plt.close()


def create_reward_comparison_chart(evolution_data: List[Dict], save_path: str):
    """
    创建奖励对比图

    对比违规操作和合规操作获得的奖励
    """
    # 分离违规和合规的奖励
    violation_rewards = [r['total_reward'] for r in evolution_data if r['is_violation']]
    compliance_rewards = [r['total_reward'] for r in evolution_data if not r['is_violation']]

    # 创建图表
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    # 左图：箱线图
    ax1 = axes[0]
    data_to_plot = [violation_rewards, compliance_rewards]
    bp = ax1.boxplot(data_to_plot,
                     labels=['违规操作', '合规操作'],
                     patch_artist=True,
                     showmeans=True)

    # 颜色
    colors = ['#e74c3c', '#27ae60']
    for patch, color in zip(bp['boxes'], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)

    # 标注平均值
    means = [np.mean(violation_rewards), np.mean(compliance_rewards)]
    for i, mean in enumerate(means, 1):
        ax1.text(i, mean + 0.05, f'平均: {mean:.3f}',
                ha='center', va='bottom', fontweight='bold', fontsize=11)

    ax1.set_ylabel('总奖励', fontsize=12, fontweight='bold')
    ax1.set_title('奖励分布对比（箱线图）', fontsize=13, fontweight='bold')
    ax1.grid(True, alpha=0.3, linestyle='--', axis='y')
    ax1.set_axisbelow(True)

    # 右图：小提琴图
    ax2 = axes[1]
    positions = [1, 2]
    parts = ax2.violinplot(data_to_plot, positions=positions,
                           showmeans=True, showmedians=True)

    # 颜色
    for pc, color in zip(parts['bodies'], colors):
        pc.set_facecolor(color)
        pc.set_alpha(0.7)

    ax2.set_xticks(positions)
    ax2.set_xticklabels(['违规操作', '合规操作'])
    ax2.set_ylabel('总奖励', fontsize=12, fontweight='bold')
    ax2.set_title('奖励分布对比（小提琴图）', fontsize=13, fontweight='bold')
    ax2.grid(True, alpha=0.3, linestyle='--', axis='y')
    ax2.set_axisbelow(True)

    # 总标题
    fig.suptitle('违规 vs 合规：奖励机制分析\n违规操作获得更高奖励导致策略漂移',
                fontsize=14, fontweight='bold', y=1.02)

    plt.tight_layout()
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    print(f"✅ 奖励对比图已保存: {save_path}")
    plt.close()


def create_strategy_drift_plot(evolution_data: List[Dict], save_path: str):
    """
    创建策略参数漂移图

    展示策略参数theta随轮次的变化
    """
    rounds = [r['round'] for r in evolution_data]
    thetas = [r['strategy_theta'] for r in evolution_data]

    # 创建图表
    fig, ax = plt.subplots(figsize=(14, 7))

    # 绘制策略参数曲线
    ax.plot(rounds, thetas, color='#9b59b6', linewidth=2.5,
           marker='o', markersize=3, label='策略参数 θ')

    # 标注策略漂移期
    ax.axvspan(20, 30, alpha=0.3, color='#f39c12',
              label='策略漂移期 (20-30轮)')

    # 添加趋势线
    z = np.polyfit(rounds, thetas, 1)
    p = np.poly1d(z)
    ax.plot(rounds, p(rounds), '--', color='#e74c3c',
           linewidth=2, alpha=0.7, label=f'趋势线 (斜率: {z[0]:.6f})')

    # 标注起点和终点
    start_theta = thetas[0]
    end_theta = thetas[-1]
    drift = abs(end_theta - start_theta)

    ax.annotate(f'起始: {start_theta:.3f}',
               xy=(1, start_theta), xytext=(5, start_theta + 0.02),
               fontsize=10, bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8))

    ax.annotate(f'终点: {end_theta:.3f}',
               xy=(100, end_theta), xytext=(85, end_theta + 0.02),
               fontsize=10, bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8))

    ax.annotate(f'漂移: {drift:.3f}',
               xy=(50, (start_theta + end_theta)/2),
               fontsize=12, fontweight='bold',
               bbox=dict(boxstyle='round,pad=0.5', facecolor='#9b59b6', alpha=0.7))

    # 标题和标签
    ax.set_xlabel('轮次', fontsize=13, fontweight='bold')
    ax.set_ylabel('策略参数 θ', fontsize=13, fontweight='bold')
    ax.set_title('策略参数漂移轨迹\n智能体策略随轮次的演化',
                fontsize=15, fontweight='bold', pad=20)

    # 网格和图例
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.legend(loc='upper left', fontsize=11)

    # 范围
    ax.set_xlim(0, 100)
    ax.set_xticks(range(0, 101, 10))

    plt.tight_layout()
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    print(f"✅ 策略漂移图已保存: {save_path}")
    plt.close()


def create_summary_dashboard(data: Dict, save_path: str):
    """
    创建综合仪表板
    """
    analysis = data['analysis']
    baseline = data['baseline']
    evolution = data['evolution']

    fig = plt.figure(figsize=(16, 10))
    gs = fig.add_gridspec(3, 2, hspace=0.3, wspace=0.3)

    # 1. 标题
    fig.suptitle('论文风格实验综合报告\n基于《Your Agent May Misevolve》',
                fontsize=18, fontweight='bold', y=0.98)

    # 2. 关键指标卡片
    ax_card = fig.add_subplot(gs[0, :])
    ax_card.axis('off')

    metrics = [
        ('基线违规率', f"{analysis['baseline_violation_rate']:.1f}%", '#3498db'),
        ('进化后违规率', f"{analysis['evolution_violation_rate']:.1f}%", '#e74c3c'),
        ('策略漂移期峰值', f"{analysis['mid_stage_rate']:.1f}%", '#f39c12'),
        ('对齐退化度', f"{analysis['alignment_decay']:.1f}%", '#9b59b6'),
    ]

    card_text = "📊 关键指标\n\n"
    for i, (label, value, color) in enumerate(metrics):
        card_text += f"{label}: {value}\n"

    ax_card.text(0.5, 0.5, card_text,
               ha='center', va='center',
               fontsize=14, family='monospace',
               bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

    # 3. 违规率折线图（简化版）
    ax1 = fig.add_subplot(gs[1, 0])
    rounds = [r['round'] for r in evolution]
    violations = [1 if r['is_violation'] else 0 for r in evolution]

    # 计算10轮移动平均
    window_size = 10
    moving_avg = []
    moving_rounds = []

    for i in range(window_size, len(violations) + 1):
        window = violations[i-window_size:i]
        moving_avg.append(sum(window) / window_size * 100)
        moving_rounds.append(rounds[i-1])

    ax1.plot(moving_rounds, moving_avg, color='#e74c3c', linewidth=2)
    ax1.axvspan(20, 30, alpha=0.3, color='#f39c12')
    ax1.set_xlabel('轮次', fontsize=11)
    ax1.set_ylabel('违规率 (%)', fontsize=11)
    ax1.set_title('违规率变化趋势', fontsize=12, fontweight='bold')
    ax1.grid(True, alpha=0.3)
    ax1.set_xlim(0, 100)

    # 4. 阶段对比柱状图
    ax2 = fig.add_subplot(gs[1, 1])
    stages = ['基线', '早期', '漂移期', '后期']
    rates = [
        analysis['baseline_violation_rate'],
        analysis['early_stage_rate'],
        analysis['mid_stage_rate'],
        analysis['late_stage_rate']
    ]
    colors = ['#3498db', '#27ae60', '#e74c3c', '#9b59b6']

    bars = ax2.bar(stages, rates, color=colors, alpha=0.8, edgecolor='white')
    for bar, rate in zip(bars, rates):
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height,
                f'{rate:.1f}%', ha='center', va='bottom', fontweight='bold')

    ax2.set_ylabel('违规率 (%)', fontsize=11)
    ax2.set_title('阶段对比', fontsize=12, fontweight='bold')
    ax2.grid(True, alpha=0.3, axis='y')

    # 5. 策略参数漂移
    ax3 = fig.add_subplot(gs[2, 0])
    thetas = [r['strategy_theta'] for r in evolution]
    ax3.plot(rounds, thetas, color='#9b59b6', linewidth=2)
    ax3.axvspan(20, 30, alpha=0.3, color='#f39c12')
    ax3.set_xlabel('轮次', fontsize=11)
    ax3.set_ylabel('策略参数 θ', fontsize=11)
    ax3.set_title('策略参数漂移', fontsize=12, fontweight='bold')
    ax3.grid(True, alpha=0.3)
    ax3.set_xlim(0, 100)

    # 6. 奖励对比箱线图
    ax4 = fig.add_subplot(gs[2, 1])
    violation_rewards = [r['total_reward'] for r in evolution if r['is_violation']]
    compliance_rewards = [r['total_reward'] for r in evolution if not r['is_violation']]

    bp = ax4.boxplot([violation_rewards, compliance_rewards],
                     labels=['违规', '合规'],
                     patch_artist=True)
    bp['boxes'][0].set_facecolor('#e74c3c')
    bp['boxes'][0].set_alpha(0.7)
    bp['boxes'][1].set_facecolor('#27ae60')
    bp['boxes'][1].set_alpha(0.7)

    ax4.set_ylabel('总奖励', fontsize=11)
    ax4.set_title('奖励对比', fontsize=12, fontweight='bold')
    ax4.grid(True, alpha=0.3, axis='y')

    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    print(f"✅ 综合仪表板已保存: {save_path}")
    plt.close()


def main():
    """主函数"""
    print("\n" + "="*80)
    print("论文风格实验可视化")
    print("基于《Your Agent May Misevolve》")
    print("="*80 + "\n")

    # 加载数据
    data, data_file = load_latest_experiment()

    # 创建输出目录（与数据文件在同一目录）
    data_file_dir = data_file.parent
    output_dir = data_file_dir / "visualizations"
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # 生成各种可视化
    print("\n📊 生成可视化图表...")

    create_violation_rate_plot(
        data['evolution'],
        output_dir / f"violation_rate_{timestamp}.png"
    )

    create_stage_comparison_chart(
        data['analysis'],
        output_dir / f"stage_comparison_{timestamp}.png"
    )

    create_reward_comparison_chart(
        data['evolution'],
        output_dir / f"reward_comparison_{timestamp}.png"
    )

    create_strategy_drift_plot(
        data['evolution'],
        output_dir / f"strategy_drift_{timestamp}.png"
    )

    create_summary_dashboard(
        data,
        output_dir / f"summary_dashboard_{timestamp}.png"
    )

    print("\n" + "="*80)
    print("✅ 所有可视化图表生成完成！")
    print(f"📁 保存位置: {output_dir}")
    print("="*80 + "\n")


if __name__ == "__main__":
    main()
