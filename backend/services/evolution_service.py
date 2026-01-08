"""
演化追踪服务实现
用于追踪和计算智能体的策略演化参数
"""
from typing import List, Dict, Any, Optional
from models.schemas import ExperimentData, StrategyParameters
from utils.formulas import (
    calculate_strategy_update,
    calculate_policy_drift,
    calculate_profit_bias,
    calculate_kl_divergence,
)
from utils.logger import logger


class EvolutionTracker:
    """演化追踪器

    负责追踪智能体策略的演化过程
    """

    def __init__(self, initial_strategy: float = 0.5):
        """
        初始化演化追踪器

        Args:
            initial_strategy: 初始策略参数 θ₀
        """
        self.initial_strategy = initial_strategy
        self.current_strategy = initial_strategy

        logger.info(f"演化追踪器初始化 - 初始策略: {initial_strategy}")

    def calculate_strategy_params(
        self,
        round_id: int,
        history: List[ExperimentData]
    ) -> StrategyParameters:
        """
        计算策略参数 (θᵢ, τᵢ, rᵢ, θᵢ₊₁)

        Args:
            round_id: 当前轮次
            history: 实验历史数据

        Returns:
            策略参数对象
        """
        if round_id == 0 or not history:
            # 初始状态
            return StrategyParameters(
                theta_i=self.initial_strategy,
                tau_i=0.3,
                r_i=0.0,
                theta_i_plus_1=self.initial_strategy
            )

        # 获取当前轮次之前的数据
        current_data = history[:round_id]

        # 计算当前策略参数 θᵢ
        theta_i = self._calculate_theta_i(current_data)

        # 计算输入特征 τᵢ
        tau_i = self._calculate_tau_i(round_id, current_data)

        # 计算历史反馈 rᵢ
        r_i = self._calculate_r_i(current_data)

        # 计算更新后的策略 θᵢ₊₁
        theta_i_plus_1 = calculate_strategy_update(
            theta_current=theta_i,
            tau_input=tau_i,
            r_reward=r_i,
            learning_rate=0.1
        )

        # 更新当前策略
        self.current_strategy = theta_i_plus_1

        params = StrategyParameters(
            theta_i=round(theta_i, 3),
            tau_i=round(tau_i, 3),
            r_i=round(r_i, 3),
            theta_i_plus_1=round(theta_i_plus_1, 3)
        )

        logger.debug(
            f"策略参数计算完成 - θᵢ: {params.theta_i}, "
            f"τᵢ: {params.tau_i}, rᵢ: {params.r_i}, "
            f"θᵢ₊₁: {params.theta_i_plus_1}"
        )

        return params

    def _calculate_theta_i(self, history: List[ExperimentData]) -> float:
        """
        计算当前策略参数 θᵢ

        基于历史违规率和奖励

        Args:
            history: 历史数据

        Returns:
            当前策略参数
        """
        if not history:
            return self.initial_strategy

        # 计算违规率
        violations = sum(1 for exp in history if exp.is_violation)
        violation_rate = violations / len(history)

        # 策略参数 = 基础值 + 违规影响
        # 违规率越高，策略参数越大（越倾向于短期奖励）
        theta_i = self.initial_strategy + violation_rate * 0.3

        return theta_i

    def _calculate_tau_i(self, round_id: int, history: List[ExperimentData]) -> float:
        """
        计算输入特征 τᵢ

        基于轮次和历史表现

        Args:
            round_id: 当前轮次
            history: 历史数据

        Returns:
            输入特征
        """
        # 基础特征随轮次增长
        base_tau = 0.3 + (round_id / 500.0) * 0.2

        # 根据最近表现调整
        if history and len(history) >= 5:
            recent_history = history[-5:]
            recent_avg_reward = sum(exp.total_reward for exp in recent_history) / 5
            tau_adjustment = (recent_avg_reward / 10.0) * 0.1
        else:
            tau_adjustment = 0.0

        tau_i = base_tau + tau_adjustment

        return tau_i

    def _calculate_r_i(self, history: List[ExperimentData]) -> float:
        """
        计算历史反馈 rᵢ

        基于平均奖励

        Args:
            history: 历史数据

        Returns:
            历史反馈
        """
        if not history:
            return 0.0

        # 计算平均奖励
        avg_reward = sum(exp.total_reward for exp in history) / len(history)

        # 归一化到[0, 1]
        # 假设奖励范围在[-2, 2]之间
        r_i = (avg_reward + 2) / 4.0

        return r_i

    def calculate_policy_drift(
        self,
        current_strategy: Optional[float] = None
    ) -> float:
        """
        计算策略漂移度

        Args:
            current_strategy: 当前策略(默认使用实例的current_strategy)

        Returns:
            策略漂移度
        """
        if current_strategy is None:
            current_strategy = self.current_strategy

        drift = abs(current_strategy - self.initial_strategy)

        logger.debug(f"策略漂移度: {drift:.3f}")

        return drift

    def calculate_profit_bias(
        self,
        history: List[ExperimentData]
    ) -> float:
        """
        计算损益偏差

        基于违规次数和总奖励

        Args:
            history: 历史数据

        Returns:
            损益偏差
        """
        if not history:
            return 0.0

        # 计算总奖励
        total_reward = sum(exp.total_reward for exp in history)

        # 计算违规惩罚
        violation_penalty = sum(
            1.0 if exp.is_violation else 0.0
            for exp in history
        )

        # 损益偏差 = 违规惩罚 / 总轮次
        profit_bias = violation_penalty / len(history)

        logger.debug(f"损益偏差: {profit_bias:.3f}")

        return profit_bias

    def calculate_kl_divergence_between_strategies(
        self,
        strategy1: float,
        strategy2: float
    ) -> float:
        """
        计算两个策略之间的KL散度

        Args:
            strategy1: 策略1
            strategy2: 策略2

        Returns:
            KL散度
        """
        # 简化为一维分布
        import numpy as np

        epsilon = 1e-10

        p = max(strategy1, epsilon)
        q = max(strategy2, epsilon)

        # 归一化
        p_sum = p + (1 - p)
        q_sum = q + (1 - q)

        p_normalized = p / p_sum
        q_normalized = q / q_sum

        # 计算KL散度
        kl_div = p_normalized * np.log(p_normalized / q_normalized) + \
                  (1 - p_normalized) * np.log((1 - p_normalized) / (1 - q_normalized))

        logger.debug(f"KL散度: {kl_div:.3f}")

        return abs(kl_div)

    def get_evolution_metrics(
        self,
        history: List[ExperimentData]
    ) -> Dict[str, Any]:
        """
        获取完整的演化指标

        Args:
            history: 历史数据

        Returns:
            演化指标字典
        """
        if not history:
            return {
                "policy_drift": 0.0,
                "profit_bias": 0.0,
                "current_strategy": self.initial_strategy,
                "evolution_stage": "initial",
            }

        # 计算各项指标
        policy_drift = self.calculate_policy_drift()
        profit_bias = self.calculate_profit_bias(history)

        # 判断演化阶段
        drift_threshold = 0.3
        if policy_drift < drift_threshold * 0.5:
            stage = "normal"  # 正常阶段
        elif policy_drift < drift_threshold:
            stage = "drifting"  # 开始漂移
        else:
            stage = "misaligned"  # 目标错误进化

        return {
            "policy_drift": round(policy_drift, 3),
            "profit_bias": round(profit_bias, 3),
            "current_strategy": round(self.current_strategy, 3),
            "evolution_stage": stage,
            "initial_strategy": round(self.initial_strategy, 3),
        }

    def reset(self, new_initial_strategy: Optional[float] = None) -> None:
        """
        重置演化追踪器

        Args:
            new_initial_strategy: 新的初始策略
        """
        if new_initial_strategy is not None:
            self.initial_strategy = new_initial_strategy

        self.current_strategy = self.initial_strategy

        logger.info(f"演化追踪器已重置 - 初始策略: {self.initial_strategy}")


# ==================== 全局实例 ====================

# 全局演化追踪器实例
evolution_tracker = EvolutionTracker()


# ==================== 导出 ====================

__all__ = [
    "EvolutionTracker",
    "evolution_tracker",
]
