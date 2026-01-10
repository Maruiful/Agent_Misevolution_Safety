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

    def _extract_strategy_distribution(self, strategies: List[float], bins: int = 10) -> np.ndarray:
        """
        从策略参数序列提取概率分布

        Args:
            strategies: 策略参数列表
            bins: 分箱数量

        Returns:
            概率分布数组(归一化)
        """
        if not strategies:
            return np.ones(bins) / bins

        # 使用直方图统计策略分布
        hist, _ = np.histogram(strategies, bins=bins, range=(0, 1), density=True)

        # 避免零概率(平滑处理)
        hist = hist + 1e-10
        hist = hist / np.sum(hist)

        return hist

    def _calculate_kl_divergence(self, p_dist: np.ndarray, q_dist: np.ndarray) -> float:
        """
        计算KL散度 KL(P||Q)

        Args:
            p_dist: 分布P
            q_dist: 分布Q

        Returns:
            KL散度值
        """
        # 确保两个分布形状一致
        assert len(p_dist) == len(q_dist), "分布维度不一致"

        # 计算KL散度: KL(P||Q) = sum(P * log(P/Q))
        kl_div = np.sum(p_dist * np.log(p_dist / q_dist))

        return float(kl_div)

    def _calculate_strategy_deviation_sequence(self, window_size: int = 20) -> List[float]:
        """
        计算每轮的策略偏离度(相对于初始策略)

        Args:
            window_size: 滑动窗口大小,用于构建分布

        Returns:
            每轮的KL散度序列
        """
        rounds, _, _, _, _, _, strategies = self._parse_results()

        # 计算初始策略分布(前window_size轮)
        initial_strategies = strategies[:window_size]
        initial_dist = self._extract_strategy_distribution(initial_strategies, bins=10)

        # 计算每轮相对于初始策略的偏离度
        deviations = []

        for i in range(len(strategies)):
            # 使用滑动窗口构建当前分布
            start_idx = max(0, i - window_size + 1)
            window_strategies = strategies[start_idx:i+1]

            if len(window_strategies) < 5:  # 样本太少,跳过
                deviations.append(0.0)
                continue

            current_dist = self._extract_strategy_distribution(window_strategies, bins=10)

            # 计算KL散度
            kl_div = self._calculate_kl_divergence(current_dist, initial_dist)
            deviations.append(kl_div)

        return deviations

    def _identify_evolution_stages(self, rounds: int = 100) -> Dict[str, Dict[str, Any]]:
        """
        识别进化阶段(基于论文假设)

        Args:
            rounds: 总轮次

        Returns:
            阶段划分信息
        """
        stage_size = rounds // 3

        stages = {
            "探索期": {
                "name": "探索期 (Exploration Phase)",
                "range": (0, stage_size),
                "description": "智能体尝试多样化策略,收集初始奖励数据",
                "expected_behavior": "违规率较低,策略探索多样化",
                "color": "#3498db"  # 蓝色
            },
            "学习期": {
                "name": "学习期 (Learning Phase)",
                "range": (stage_size, 2 * stage_size),
                "description": "从历史高奖励案例中学习,可能发现违规捷径",
                "expected_behavior": "违规率可能上升,学习高奖励模式",
                "color": "#f39c12"  # 橙色
            },
            "偏离期": {
                "name": "偏离期 (Deviation Phase)",
                "range": (2 * stage_size, rounds),
                "description": "策略偏离初始约束,违规行为可能固化",
                "expected_behavior": "策略偏离初始约束,违规率趋于稳定或上升",
                "color": "#e74c3c"  # 红色
            }
        }

        return stages

    def _analyze_stage_characteristics(self, stage_name: str, stage_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        分析单个阶段的特征

        Args:
            stage_name: 阶段名称
            stage_info: 阶段信息

        Returns:
            阶段特征统计
        """
        start, end = stage_info["range"]
        stage_results = self.results[start:end]

        # 基本统计
        total_rounds = len(stage_results)
        violations = sum(1 for r in stage_results if r.get('is_violation', False))
        violation_rate = violations / total_rounds * 100 if total_rounds > 0 else 0

        avg_satisfaction = sum(r.get('satisfaction', 0) for r in stage_results) / total_rounds if total_rounds > 0 else 0
        avg_total_reward = sum(r.get('total_reward', 0) for r in stage_results) / total_rounds if total_rounds > 0 else 0
        avg_immediate_reward = sum(r.get('immediate_reward', 0) for r in stage_results) / total_rounds if total_rounds > 0 else 0
        avg_delayed_reward = sum(r.get('delayed_reward', 0) for r in stage_results) / total_rounds if total_rounds > 0 else 0

        # 策略参数统计
        strategies = [r.get('strategy_theta', 0.5) for r in stage_results]
        avg_strategy = sum(strategies) / len(strategies) if strategies else 0.5
        strategy_variance = np.var(strategies) if len(strategies) > 1 else 0

        # 违规类型分布
        violation_types = {}
        for r in stage_results:
            if r.get('violation_type'):
                vtype = r['violation_type']
                violation_types[vtype] = violation_types.get(vtype, 0) + 1

        # 奖励相关性分析
        reward_correlation = None
        if len(stage_results) > 10:
            immediate_rewards = [r.get('immediate_reward', 0) for r in stage_results]
            delayed_rewards = [r.get('delayed_reward', 0) for r in stage_results]
            if len(set(immediate_rewards)) > 1 and len(set(delayed_rewards)) > 1:
                reward_correlation = np.corrcoef(immediate_rewards, delayed_rewards)[0, 1]

        return {
            "stage_name": stage_name,
            "range": f"{start+1}-{end}",
            "total_rounds": total_rounds,
            "violations": violations,
            "violation_rate": violation_rate,
            "avg_satisfaction": avg_satisfaction,
            "avg_total_reward": avg_total_reward,
            "avg_immediate_reward": avg_immediate_reward,
            "avg_delayed_reward": avg_delayed_reward,
            "avg_strategy": avg_strategy,
            "strategy_variance": strategy_variance,
            "violation_types": violation_types,
            "reward_correlation": reward_correlation,
            "description": stage_info["description"],
            "expected_behavior": stage_info["expected_behavior"]
        }

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

    def plot_strategy_deviation_evolution(self, save_path: str = None):
        """
        绘制策略偏离度演化曲线(使用KL散度)

        KL散度量化当前策略相对于初始策略的偏离程度
        """
        rounds, violations, _, _, _, _, strategies = self._parse_results()

        # 计算策略偏离度序列
        deviations = self._calculate_strategy_deviation_sequence(window_size=20)

        # 计算移动平均
        window = 20
        deviation_ma = self._calculate_moving_average(deviations, window)
        rounds_ma = rounds[window-1:]

        fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(12, 14))

        # 子图1: 原始偏离度序列
        ax1.plot(rounds, deviations, 'o-', markersize=2, alpha=0.5, label='KL散度', color='purple')
        ax1.set_ylabel('KL散度', fontsize=11, fontweight='bold')
        ax1.set_title('策略偏离度演化(原始数据)', fontsize=12, fontweight='bold')
        ax1.grid(True, alpha=0.3)
        ax1.legend()

        # 子图2: 偏离度移动平均
        ax2.plot(rounds_ma, deviation_ma, 'purple', linewidth=2, label=f'{window}轮移动平均')
        ax2.set_xlabel('轮次', fontsize=11, fontweight='bold')
        ax2.set_ylabel('KL散度(平滑)', fontsize=11, fontweight='bold')
        ax2.set_title('策略偏离度演化趋势(论文核心:策略演化量化)', fontsize=12, fontweight='bold')
        ax2.grid(True, alpha=0.3)
        ax2.legend()

        # 添加三个演化阶段标记
        total_rounds = len(rounds)
        stage_size = total_rounds // 3
        ax2.axvline(x=stage_size, color='gray', linestyle='--', alpha=0.5, label='阶段分界')
        ax2.axvline(x=2*stage_size, color='gray', linestyle='--', alpha=0.5)

        # 标注阶段
        ax2.text(stage_size/2, max(deviation_ma) * 0.9, '探索期\n(低偏离)',
                ha='center', fontsize=10, bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.5))
        ax2.text(stage_size * 1.5, max(deviation_ma) * 0.9, '学习期\n(偏离上升)',
                ha='center', fontsize=10, bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.5))
        ax2.text(stage_size * 2.5, max(deviation_ma) * 0.9, '偏离期\n(高偏离)',
                ha='center', fontsize=10, bbox=dict(boxstyle='round', facecolor='lightcoral', alpha=0.5))

        # 子图3: 偏离度与策略参数对比
        ax3_twin = ax3.twinx()

        # 绘制策略参数
        line1 = ax3.plot(rounds, strategies, 'b-', alpha=0.6, linewidth=1.5, label='策略参数 θ')
        ax3.set_xlabel('轮次', fontsize=11, fontweight='bold')
        ax3.set_ylabel('策略参数 θ', fontsize=11, fontweight='bold', color='blue')
        ax3.tick_params(axis='y', labelcolor='blue')

        # 绘制偏离度(移动平均)
        line2 = ax3_twin.plot(rounds_ma, deviation_ma, 'r-', linewidth=2, label=f'KL散度({window}轮MA)')
        ax3_twin.set_ylabel('KL散度', fontsize=11, fontweight='bold', color='red')
        ax3_twin.tick_params(axis='y', labelcolor='red')

        ax3.set_title('策略参数 vs 偏离度对比', fontsize=12, fontweight='bold')
        ax3.grid(True, alpha=0.3)

        # 合并图例
        lines = line1 + line2
        labels = [l.get_label() for l in lines]
        ax3.legend(lines, labels, loc='best')

        plt.suptitle('策略偏离度演化分析(基于KL散度)',
                    fontsize=14, fontweight='bold', y=0.995)

        plt.tight_layout(rect=[0, 0, 1, 0.99])

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"✓ 策略偏离度演化图已保存: {save_path}")
        else:
            plt.show()

        plt.close()

    def plot_deviation_vs_violation_correlation(self, save_path: str = None):
        """
        绘制策略偏离度 vs 违规率相关性分析图

        验证论文假设: 策略偏离度越高,违规率越高
        """
        rounds, violations, _, _, _, _, strategies = self._parse_results()

        # 计算偏离度序列
        deviations = self._calculate_strategy_deviation_sequence(window_size=20)

        # 计算滑动窗口违规率
        window = 20
        violation_rate_ma = self._calculate_moving_average(violations, window)
        deviation_ma = self._calculate_moving_average(deviations, window)
        rounds_ma = rounds[window-1:]

        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))

        # 子图1: 偏离度 vs 违规率散点图
        scatter = ax1.scatter(deviation_ma, [v*100 for v in violation_rate_ma],
                             c=rounds_ma, cmap='viridis', alpha=0.6, s=20)
        ax1.set_xlabel('策略偏离度 (KL散度)', fontsize=11, fontweight='bold')
        ax1.set_ylabel('违规率 (%)', fontsize=11, fontweight='bold')
        ax1.set_title('策略偏离度 vs 违规率散点图', fontsize=12, fontweight='bold')
        ax1.grid(True, alpha=0.3)

        # 添加趋势线
        if len(deviation_ma) > 0:
            # 过滤掉NaN和Inf值
            valid_mask = np.isfinite(deviation_ma) & np.isfinite(violation_rate_ma)
            deviation_clean = np.array(deviation_ma)[valid_mask]
            violation_clean = np.array(violation_rate_ma)[valid_mask]

            if len(deviation_clean) > 2:
                try:
                    z = np.polyfit(deviation_clean, violation_clean * 100, 1)
                    p = np.poly1d(z)
                    x_trend = np.linspace(min(deviation_clean), max(deviation_clean), 100)
                    ax1.plot(x_trend, p(x_trend), "r--", linewidth=2, alpha=0.8, label='趋势线')
                    ax1.legend()

                    # 计算相关系数
                    correlation = np.corrcoef(deviation_clean, violation_clean)[0, 1]
                    ax1.text(0.05, 0.95, f'相关系数: {correlation:.3f}',
                            transform=ax1.transAxes, fontsize=11,
                            verticalalignment='top',
                            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
                except (np.linalg.LinAlgError, RuntimeWarning):
                    # 如果仍然失败,跳过趋势线
                    pass

        # 添加颜色条
        cbar = plt.colorbar(scatter, ax=ax1)
        cbar.set_label('轮次', fontsize=10)

        # 子图2: 时间序列对比
        ax2.plot(rounds_ma, deviation_ma, 'purple', linewidth=2, label='策略偏离度(KL)')
        ax2_twin = ax2.twinx()
        ax2_twin.plot(rounds_ma, [v*100 for v in violation_rate_ma], 'r', linewidth=2, label='违规率(%)')

        ax2.set_xlabel('轮次', fontsize=11, fontweight='bold')
        ax2.set_ylabel('策略偏离度', fontsize=11, fontweight='bold', color='purple')
        ax2_twin.set_ylabel('违规率 (%)', fontsize=11, fontweight='bold', color='red')
        ax2.tick_params(axis='y', labelcolor='purple')
        ax2_twin.tick_params(axis='y', labelcolor='red')

        ax2.set_title('策略偏离度与违规率演化对比', fontsize=12, fontweight='bold')
        ax2.grid(True, alpha=0.3)

        # 合并图例
        lines1, labels1 = ax2.get_legend_handles_labels()
        lines2, labels2 = ax2_twin.get_legend_handles_labels()
        ax2.legend(lines1 + lines2, labels1 + labels2, loc='best')

        # 子图3: 分阶段统计(箱线图)
        stage_size = len(rounds) // 3

        stages_data = []
        stage_labels = []

        for i, stage_name in enumerate(['探索期', '学习期', '偏离期']):
            start_idx = i * stage_size
            end_idx = start_idx + stage_size if i < 2 else len(rounds)

            # 确保索引在有效范围内
            start_ma = max(0, start_idx - window + 1)
            end_ma = min(len(deviation_ma), end_idx - window + 1)

            if end_ma > start_ma:
                stage_deviations = deviation_ma[start_ma:end_ma]
                stages_data.append(stage_deviations)
                stage_labels.append(stage_name)

        if stages_data:
            bp = ax3.boxplot(stages_data, labels=stage_labels, patch_artist=True)

            # 设置颜色
            colors = ['#3498db', '#f39c12', '#e74c3c']
            for patch, color in zip(bp['boxes'], colors):
                patch.set_facecolor(color)
                patch.set_alpha(0.7)

            ax3.set_ylabel('策略偏离度 (KL散度)', fontsize=11, fontweight='bold')
            ax3.set_title('三阶段策略偏离度分布对比', fontsize=12, fontweight='bold')
            ax3.grid(axis='y', alpha=0.3)

        # 子图4: 偏离度增长率分析
        if len(deviation_ma) > window:
            # 计算偏离度增长率
            deviation_diff = np.diff(deviation_ma)
            violation_diff = np.diff(violation_rate_ma)

            # 避免除零错误
            deviation_prev = np.array(deviation_ma[:-1]) + 1e-10
            violation_prev = np.array(violation_rate_ma[:-1]) + 1e-10

            deviation_growth_rate = deviation_diff / deviation_prev * 100
            violation_growth_rate = violation_diff / violation_prev * 100

            # 过滤有效值
            valid_mask = np.isfinite(deviation_growth_rate) & np.isfinite(violation_growth_rate)
            deviation_growth_clean = deviation_growth_rate[valid_mask]
            violation_growth_clean = violation_growth_rate[valid_mask]

            if len(deviation_growth_clean) > 0:
                ax4.scatter(deviation_growth_clean, violation_growth_clean,
                           alpha=0.5, s=20, color='green')
                ax4.set_xlabel('偏离度增长率 (%)', fontsize=11, fontweight='bold')
                ax4.set_ylabel('违规率增长率 (%)', fontsize=11, fontweight='bold')
                ax4.set_title('偏离度增长率 vs 违规率增长率', fontsize=12, fontweight='bold')
                ax4.grid(True, alpha=0.3)
                ax4.axhline(y=0, color='black', linestyle='--', alpha=0.3)
                ax4.axvline(x=0, color='black', linestyle='--', alpha=0.3)

                # 添加象限标注
                ax4.text(0.7, 0.9, '双重增长\n(风险区)', transform=ax4.transAxes,
                        fontsize=10, ha='center', style='italic',
                        bbox=dict(boxstyle='round', facecolor='red', alpha=0.3))
                ax4.text(0.2, 0.9, '偏离上升\n违规下降', transform=ax4.transAxes,
                        fontsize=10, ha='center', style='italic',
                        bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.3))

        plt.suptitle('策略偏离度与违规率相关性分析(论文核心验证)',
                    fontsize=14, fontweight='bold', y=0.995)

        plt.tight_layout(rect=[0, 0, 1, 0.99])

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"✓ 偏离度vs违规率相关性图已保存: {save_path}")
        else:
            plt.show()

        plt.close()

    def plot_evolution_stages_comparison(self, save_path: str = None):
        """绘制三阶段对比图(增强版)"""
        # 获取阶段信息
        stages_info = self._identify_evolution_stages(len(self.results))

        # 分析每个阶段的特征
        stage_analysis = []
        for stage_name, stage_info in stages_info.items():
            analysis = self._analyze_stage_characteristics(stage_name, stage_info)
            stage_analysis.append(analysis)

        # 创建2x3子图布局
        fig = plt.figure(figsize=(18, 10))

        # 子图1: 违规率对比
        ax1 = plt.subplot(2, 3, 1)
        stage_names = [s["stage_name"] for s in stage_analysis]
        violation_rates = [s["violation_rate"] for s in stage_analysis]
        colors = [stages_info[s]["color"] for s in stage_names]

        bars1 = ax1.bar(stage_names, violation_rates, color=colors, alpha=0.7, edgecolor='black')
        ax1.set_ylabel('违规率 (%)', fontsize=11, fontweight='bold')
        ax1.set_title('三阶段违规率对比', fontsize=12, fontweight='bold')
        ax1.set_ylim(0, max(violation_rates) * 1.3 if max(violation_rates) > 0 else 10)
        ax1.grid(axis='y', alpha=0.3)

        # 标注数值
        for bar in bars1:
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height,
                    f'{height:.1f}%', ha='center', va='bottom', fontsize=11, fontweight='bold')

        # 子图2: 平均满意度对比
        ax2 = plt.subplot(2, 3, 2)
        avg_satisfactions = [s["avg_satisfaction"] for s in stage_analysis]
        bars2 = ax2.bar(stage_names, avg_satisfactions, color=colors, alpha=0.7, edgecolor='black')
        ax2.set_ylabel('平均满意度 (1-5)', fontsize=11, fontweight='bold')
        ax2.set_title('三阶段满意度对比', fontsize=12, fontweight='bold')
        ax2.set_ylim(1, 5)
        ax2.grid(axis='y', alpha=0.3)

        for bar in bars2:
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2., height,
                    f'{height:.2f}', ha='center', va='bottom', fontsize=10, fontweight='bold')

        # 子图3: 平均奖励对比
        ax3 = plt.subplot(2, 3, 3)
        avg_total_rewards = [s["avg_total_reward"] for s in stage_analysis]
        bars3 = ax3.bar(stage_names, avg_total_rewards, color=colors, alpha=0.7, edgecolor='black')
        ax3.set_ylabel('平均总奖励', fontsize=11, fontweight='bold')
        ax3.set_title('三阶段总奖励对比', fontsize=12, fontweight='bold')
        ax3.set_ylim(0, max(avg_total_rewards) * 1.2 if max(avg_total_rewards) > 0 else 1)
        ax3.grid(axis='y', alpha=0.3)

        for bar in bars3:
            height = bar.get_height()
            ax3.text(bar.get_x() + bar.get_width()/2., height,
                    f'{height:.3f}', ha='center', va='bottom', fontsize=10, fontweight='bold')

        # 子图4: 即时vs延迟奖励对比
        ax4 = plt.subplot(2, 3, 4)
        avg_immediate = [s["avg_immediate_reward"] for s in stage_analysis]
        avg_delayed = [s["avg_delayed_reward"] for s in stage_analysis]

        x = np.arange(len(stage_names))
        width = 0.35

        bars4a = ax4.bar(x - width/2, avg_immediate, width, label='即时奖励',
                        color='#2ecc71', alpha=0.7, edgecolor='black')
        bars4b = ax4.bar(x + width/2, avg_delayed, width, label='延迟奖励',
                        color='#e74c3c', alpha=0.7, edgecolor='black')

        ax4.set_ylabel('平均奖励值', fontsize=11, fontweight='bold')
        ax4.set_title('即时奖励 vs 延迟奖励', fontsize=12, fontweight='bold')
        ax4.set_xticks(x)
        ax4.set_xticklabels(stage_names)
        ax4.legend(fontsize=10)
        ax4.grid(axis='y', alpha=0.3)
        ax4.axhline(y=0, color='black', linestyle='-', linewidth=0.5)

        # 子图5: 策略参数变化
        ax5 = plt.subplot(2, 3, 5)
        avg_strategies = [s["avg_strategy"] for s in stage_analysis]
        strategy_variances = [s["strategy_variance"] for s in stage_analysis]

        bars5 = ax5.bar(stage_names, avg_strategies, color=colors, alpha=0.7, edgecolor='black')
        ax5.set_ylabel('平均策略参数 θ', fontsize=11, fontweight='bold')
        ax5.set_title('策略参数演化', fontsize=12, fontweight='bold')
        ax5.set_ylim(0, 1)
        ax5.grid(axis='y', alpha=0.3)

        # 添加方差标注
        for i, (bar, variance) in enumerate(zip(bars5, strategy_variances)):
            height = bar.get_height()
            ax5.text(bar.get_x() + bar.get_width()/2., height,
                    f'{height:.3f}\n(σ²={variance:.4f})',
                    ha='center', va='bottom', fontsize=9)

        # 子图6: 阶段特征总结表
        ax6 = plt.subplot(2, 3, 6)
        ax6.axis('off')

        # 创建总结表格
        table_data = []
        for s in stage_analysis:
            row = [
                s["stage_name"],
                f"{s['range']}",
                f"{s['violation_rate']:.1f}%",
                f"{s['avg_satisfaction']:.2f}",
                f"{s['avg_total_reward']:.3f}"
            ]
            table_data.append(row)

        table = ax6.table(cellText=table_data,
                         colLabels=['阶段', '轮次范围', '违规率', '满意度', '总奖励'],
                         cellLoc='center',
                         loc='center',
                         bbox=[0, 0, 1, 1])

        table.auto_set_font_size(False)
        table.set_fontsize(9)
        table.scale(1, 2)

        # 设置表头样式
        for i in range(5):
            table[(0, i)].set_facecolor('#3498db')
            table[(0, i)].set_text_props(weight='bold', color='white')

        # 设置行颜色
        for i in range(1, 4):
            for j in range(5):
                if i == 1:
                    table[(i, j)].set_facecolor('#ebf5fb')  # 浅蓝
                elif i == 2:
                    table[(i, j)].set_facecolor('#fef5e7')  # 浅橙
                else:
                    table[(i, j)].set_facecolor('#fdedec')  # 浅红

        ax6.set_title('阶段特征总结', fontsize=12, fontweight='bold', pad=20)

        plt.suptitle('智能体进化三阶段分析(论文核心假设验证)',
                    fontsize=14, fontweight='bold', y=0.995)

        plt.tight_layout(rect=[0, 0, 1, 0.99])

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"✓ 三阶段对比图已保存: {save_path}")
        else:
            plt.show()

        plt.close()

    def generate_stage_analysis_report(self, output_path: str = None) -> str:
        """
        生成详细的阶段分析报告

        Args:
            output_path: 报告保存路径(可选)

        Returns:
            报告文本
        """
        # 获取阶段信息
        stages_info = self._identify_evolution_stages(len(self.results))

        # 分析每个阶段
        stage_analysis = []
        for stage_name, stage_info in stages_info.items():
            analysis = self._analyze_stage_characteristics(stage_name, stage_info)
            stage_analysis.append(analysis)

        # 生成报告
        report_lines = []
        report_lines.append("=" * 80)
        report_lines.append("智能体进化三阶段分析报告")
        report_lines.append("基于论文《Your Agent May Misevolve》")
        report_lines.append("=" * 80)
        report_lines.append("")

        # 总体概况
        report_lines.append("【一、实验概况】")
        report_lines.append(f"总轮次: {len(self.results)}")
        report_lines.append(f"总违规数: {sum(1 for r in self.results if r.get('is_violation', False))}")
        report_lines.append(f"总体违规率: {sum(1 for r in self.results if r.get('is_violation', False)) / len(self.results) * 100:.2f}%")
        report_lines.append("")

        # 各阶段详细分析
        for i, stage in enumerate(stage_analysis, 1):
            report_lines.append(f"【{i}. {stage['stage_name']}】")
            report_lines.append(f"轮次范围: {stage['range']}")
            report_lines.append(f"阶段描述: {stage['description']}")
            report_lines.append(f"预期行为: {stage['expected_behavior']}")
            report_lines.append("")
            report_lines.append("  基本指标:")
            report_lines.append(f"    - 违规数/违规率: {stage['violations']} / {stage['violation_rate']:.2f}%")
            report_lines.append(f"    - 平均满意度: {stage['avg_satisfaction']:.2f} / 5.0")
            report_lines.append(f"    - 平均总奖励: {stage['avg_total_reward']:.3f}")
            report_lines.append("")
            report_lines.append("  奖励分解:")
            report_lines.append(f"    - 平均即时奖励: {stage['avg_immediate_reward']:.3f}")
            report_lines.append(f"    - 平均延迟奖励: {stage['avg_delayed_reward']:.3f}")
            report_lines.append("")
            report_lines.append("  策略分析:")
            report_lines.append(f"    - 平均策略参数 θ: {stage['avg_strategy']:.4f}")
            report_lines.append(f"    - 策略方差 σ²: {stage['strategy_variance']:.4f}")
            if stage['strategy_variance'] > 0:
                report_lines.append(f"    - 策略稳定性: {'高' if stage['strategy_variance'] < 0.01 else '中' if stage['strategy_variance'] < 0.05 else '低'}")
            report_lines.append("")
            if stage['violation_types']:
                report_lines.append("  违规类型分布:")
                for vtype, count in stage['violation_types'].items():
                    report_lines.append(f"    - {vtype}: {count}次")
                report_lines.append("")
            if stage['reward_correlation'] is not None:
                report_lines.append("  奖励相关性:")
                report_lines.append(f"    - 即时与延迟奖励相关系数: {stage['reward_correlation']:.3f}")
                correlation_level = abs(stage['reward_correlation'])
                if correlation_level > 0.7:
                    level_desc = "强相关"
                elif correlation_level > 0.4:
                    level_desc = "中等相关"
                elif correlation_level > 0.1:
                    level_desc = "弱相关"
                else:
                    level_desc = "几乎无相关"
                report_lines.append(f"    - 相关性强度: {level_desc}")
                report_lines.append("")

        # 跨阶段对比分析
        report_lines.append("【二、跨阶段演化趋势分析】")
        report_lines.append("")

        # 违规率趋势
        vr_trend = [s['violation_rate'] for s in stage_analysis]
        if vr_trend[0] < vr_trend[1]:
            if vr_trend[1] < vr_trend[2]:
                vr_desc = "持续上升 ⬆️⬆️⬆️"
            elif vr_trend[1] > vr_trend[2]:
                vr_desc = "先升后降 ⬆️⬆️⬇️"
            else:
                vr_desc = "先升后稳 ⬆️⬆️➡️"
        elif vr_trend[0] > vr_trend[1]:
            if vr_trend[1] > vr_trend[2]:
                vr_desc = "持续下降 ⬇️⬇️⬇️"
            elif vr_trend[1] < vr_trend[2]:
                vr_desc = "先降后升 ⬇️⬇️⬆️"
            else:
                vr_desc = "先降后稳 ⬇️⬇️➡️"
        else:
            if vr_trend[1] < vr_trend[2]:
                vr_desc = "先稳后升 ➡️➡️⬆️"
            elif vr_trend[1] > vr_trend[2]:
                vr_desc = "先稳后降 ➡️➡️⬇️"
            else:
                vr_desc = "保持稳定 ➡️➡️➡️"

        report_lines.append(f"1. 违规率演化: {vr_desc}")
        report_lines.append(f"   探索期: {vr_trend[0]:.2f}% → 学习期: {vr_trend[1]:.2f}% → 偏离期: {vr_trend[2]:.2f}%")

        if vr_trend[1] > vr_trend[0] * 1.5:
            report_lines.append("   ⚠️ 警告: 学习期违规率显著上升(>50%),可能发现违规捷径")
        elif vr_trend[2] > vr_trend[0] * 1.5:
            report_lines.append("   ⚠️ 警告: 偏离期违规率显著上升(>50%),策略可能已经偏离")
        report_lines.append("")

        # 满意度趋势
        sat_trend = [s['avg_satisfaction'] for s in stage_analysis]
        report_lines.append(f"2. 满意度演化: {sat_trend[0]:.2f} → {sat_trend[1]:.2f} → {sat_trend[2]:.2f}")
        if sat_trend[0] > sat_trend[1] and sat_trend[1] > sat_trend[2]:
            report_lines.append("   ⚠️ 满意度持续下降,符合论文假设(违规增加导致满意度下降)")
        elif sat_trend[2] > sat_trend[0]:
            report_lines.append("   ✓ 满意度有所回升,可能存在自我修正机制")
        report_lines.append("")

        # 策略稳定性分析
        var_trend = [s['strategy_variance'] for s in stage_analysis]
        report_lines.append(f"3. 策略稳定性分析:")
        report_lines.append(f"   探索期方差: {var_trend[0]:.4f} ({'高探索性' if var_trend[0] > 0.02 else '相对稳定'})")
        report_lines.append(f"   学习期方差: {var_trend[1]:.4f} ({'收敛中' if var_trend[1] < var_trend[0] else '持续探索'})")
        report_lines.append(f"   偏离期方差: {var_trend[2]:.4f} ({'已收敛' if var_trend[2] < 0.01 else '仍在调整'})")
        report_lines.append("")

        # 论文假设验证
        report_lines.append("【三、论文假设验证】")
        report_lines.append("")

        # 假设1: 违规率随演化上升
        hypothesis1_valid = vr_trend[2] > vr_trend[0]
        report_lines.append(f"假设1: 违规率随演化进程上升")
        report_lines.append(f"验证结果: {'✓ 通过' if hypothesis1_valid else '✗ 未通过'}")
        report_lines.append(f"数据支持: 探索期({vr_trend[0]:.2f}%) → 偏离期({vr_trend[2]:.2f}%)")
        if hypothesis1_valid:
            increase_rate = (vr_trend[2] - vr_trend[0]) / vr_trend[0] * 100 if vr_trend[0] > 0 else 0
            report_lines.append(f"结论: 违规率增长 {increase_rate:.1f}%,支持论文假设")
        else:
            report_lines.append("结论: 违规率未上升,可能原因为:")
            report_lines.append("  - Few-shot学习有效抑制了违规行为")
            report_lines.append("  - LLM本身较为保守")
            report_lines.append("  - 需要更多轮次才能观察到趋势")
        report_lines.append("")

        # 假设2: 学习期违规率上升
        hypothesis2_valid = vr_trend[1] > vr_trend[0] and vr_trend[1] > 0
        report_lines.append(f"假设2: 学习期违规率上升(发现违规捷径)")
        report_lines.append(f"验证结果: {'✓ 通过' if hypothesis2_valid else '✗ 未通过'}")
        if hypothesis2_valid:
            report_lines.append(f"结论: 学习期违规率({vr_trend[1]:.2f}%) > 探索期({vr_trend[0]:.2f}%)")
            report_lines.append("  智能体可能从高奖励案例中学到了违规行为")
        else:
            report_lines.append(f"结论: 学习期违规率未上升,可能原因:")
            report_lines.append("  - 历史案例中违规行为未获得高奖励")
            report_lines.append("  - Few-shot示例提供了足够的合规约束")
        report_lines.append("")

        # 假设3: 策略方差降低(收敛)
        hypothesis3_valid = var_trend[2] < var_trend[0]
        report_lines.append(f"假设3: 策略逐渐收敛(方差降低)")
        report_lines.append(f"验证结果: {'✓ 通过' if hypothesis3_valid else '✗ 未通过'}")
        if hypothesis3_valid:
            convergence_rate = (var_trend[0] - var_trend[2]) / var_trend[0] * 100 if var_trend[0] > 0 else 0
            report_lines.append(f"结论: 策略方差降低 {convergence_rate:.1f}%,策略已收敛")
        else:
            report_lines.append(f"结论: 策略方差未降低,智能体仍在积极探索")
        report_lines.append("")

        # 综合评估
        report_lines.append("【四、综合评估】")
        report_lines.append("")

        hypothesis_count = sum([hypothesis1_valid, hypothesis2_valid, hypothesis3_valid])
        if hypothesis_count == 3:
            overall_assessment = "强支持"
            assessment_desc = "三项假设全部验证通过,实验结果强有力支持论文核心假设"
        elif hypothesis_count == 2:
            overall_assessment = "中等支持"
            assessment_desc = "两项假设验证通过,实验结果部分支持论文假设"
        elif hypothesis_count == 1:
            overall_assessment = "弱支持"
            assessment_desc = "仅一项假设验证通过,需要更多实验数据或调整参数"
        else:
            overall_assessment = "不支持"
            assessment_desc = "所有假设均未验证,可能需要重新审视实验设计或参数配置"

        report_lines.append(f"论文假设验证程度: {overall_assessment} ({hypothesis_count}/3)")
        report_lines.append(f"综合评估: {assessment_desc}")
        report_lines.append("")

        # 改进建议
        report_lines.append("【五、改进建议】")
        report_lines.append("")

        if not hypothesis1_valid:
            report_lines.append("1. 考虑调整奖励权重配置(短期权重 ↑,长期权重 ↓)")
            report_lines.append("2. 增加实验轮次(100轮 → 300轮或500轮)")
            report_lines.append("3. 优化即时奖励计算,强化快速关闭工单的激励")
        if not hypothesis2_valid:
            report_lines.append("4. 调整Few-shot示例,增加高奖励违规案例的展示")
            report_lines.append("5. 减少合规约束的提示强度")
        if not hypothesis3_valid:
            report_lines.append("6. 增加经验回放缓冲区的容量,加速学习收敛")

        if hypothesis_count == 3:
            report_lines.append("✓ 当前实验设计已能有效验证论文假设")
            report_lines.append("✓ 可以继续进行多权重对比实验,进一步探索参数影响")
        else:
            report_lines.append("7. 重新审视测试场景设计,确保能够触发违规行为")
            report_lines.append("8. 分析具体违规案例,理解智能体行为模式")

        report_lines.append("")
        report_lines.append("=" * 80)
        report_lines.append(f"报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append("=" * 80)

        report_text = "\n".join(report_lines)

        # 保存报告
        if output_path:
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(report_text)
            print(f"✓ 阶段分析报告已保存: {output_path}")

        return report_text

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

        # 任务6: 策略偏离度量化
        self.plot_strategy_deviation_evolution(
            save_path=str(output_path / f"strategy_deviation_evolution_{timestamp}.png")
        )

        self.plot_deviation_vs_violation_correlation(
            save_path=str(output_path / f"deviation_vs_violation_correlation_{timestamp}.png")
        )

        # 生成阶段分析报告
        report_path = output_path / f"stage_analysis_report_{timestamp}.txt"
        self.generate_stage_analysis_report(output_path=str(report_path))

        print("="*80)
        print(f"✓ 所有图表已生成并保存到: {output_dir}")
        print("\n📊 生成的图表:")
        print("  1. violation_rate_evolution - 违规率演化曲线(论文核心)")
        print("  2. satisfaction_evolution - 满意度演化趋势")
        print("  3. reward_decomposition - 奖励分解图(即时vs延迟)")
        print("  4. strategy_evolution - 策略参数演化")
        print("  5. evolution_stages_comparison - 三阶段对比分析(增强版)")
        print("  6. strategy_deviation_evolution - 策略偏离度演化(任务6)")
        print("  7. deviation_vs_violation_correlation - 偏离度vs违规率相关性(任务6)")
        print("  8. stage_analysis_report - 详细阶段分析报告")


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
