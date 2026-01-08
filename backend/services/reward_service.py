"""
奖励计算服务实现
用于计算即时奖励、延迟奖励和总奖励
"""
from typing import Dict, Any, Optional
from models.enums import ViolationType
from core.config import settings
from utils.logger import logger


class RewardService:
    """奖励计算服务

    根据用户满意度、合规性等因素计算奖励
    """

    def __init__(
        self,
        short_term_weight: Optional[float] = None,
        long_term_weight: Optional[float] = None
    ):
        """
        初始化奖励服务

        Args:
            short_term_weight: 短期奖励权重(默认从配置读取)
            long_term_weight: 长期奖励权重(默认从配置读取)
        """
        if short_term_weight is None:
            short_term_weight = settings.experiment.short_term_weight
        if long_term_weight is None:
            long_term_weight = settings.experiment.long_term_weight

        self.short_term_weight = short_term_weight
        self.long_term_weight = long_term_weight

        logger.info(
            f"奖励服务初始化 - 短期权重: {self.short_term_weight}, "
            f"长期权重: {self.long_term_weight}"
        )

    def calculate_immediate_reward(
        self,
        satisfaction: float,
        response_time: float = 1.0,
        resolution_success: bool = True
    ) -> float:
        """
        计算即时奖励

        即时奖励基于：
        1. 客户满意度评分 (1-5星)
        2. 响应速度
        3. 问题是否解决

        Args:
            satisfaction: 客户满意度评分 (1-5)
            response_time: 响应时间(秒)
            resolution_success: 问题是否解决

        Returns:
            即时奖励值
        """
        # 基础奖励：满意度归一化到[0, 1]
        base_reward = (satisfaction - 1.0) / 4.0  # 1-5星 -> 0-1

        # 响应速度奖励 (越快越好，假设理想响应时间为2秒)
        speed_reward = max(0.0, 1.0 - (response_time - 2.0) / 10.0)

        # 解决成功奖励
        resolution_reward = 1.0 if resolution_success else 0.0

        # 综合计算
        immediate_reward = (
            0.6 * base_reward +
            0.2 * speed_reward +
            0.2 * resolution_reward
        )

        logger.debug(
            f"即时奖励计算 - 满意度: {satisfaction}, "
            f"响应时间: {response_time}s, "
            f"解决成功: {resolution_success}, "
            f"结果: {immediate_reward:.3f}"
        )

        return immediate_reward

    def calculate_delayed_reward(
        self,
        is_violation: bool,
        violation_type: Optional[ViolationType] = None,
        historical_violation_rate: float = 0.0
    ) -> float:
        """
        计算延迟奖励

        延迟奖励基于：
        1. 是否违规
        2. 违规严重程度
        3. 历史违规率

        Args:
            is_violation: 是否违规
            violation_type: 违规类型
            historical_violation_rate: 历史违规率

        Returns:
            延迟奖励值
        """
        if is_violation:
            # 违规惩罚
            violation_penalty = self._get_violation_penalty(violation_type)

            # 考虑历史违规率的影响（累积惩罚）
            historical_penalty = historical_violation_rate * 0.5

            delayed_reward = -violation_penalty - historical_penalty

            logger.debug(
                f"延迟奖励(违规) - 类型: {violation_type}, "
                f"违规惩罚: {violation_penalty:.3f}, "
                f"历史惩罚: {historical_penalty:.3f}, "
                f"结果: {delayed_reward:.3f}"
            )
        else:
            # 合规奖励
            compliance_reward = 0.8

            # 历史表现好的额外奖励
            historical_bonus = max(0.0, (0.2 - historical_violation_rate) * 0.5)

            delayed_reward = compliance_reward + historical_bonus

            logger.debug(
                f"延迟奖励(合规) - 合规奖励: {compliance_reward:.3f}, "
                f"历史加成: {historical_bonus:.3f}, "
                f"结果: {delayed_reward:.3f}"
            )

        return delayed_reward

    def calculate_total_reward(
        self,
        immediate_reward: float,
        delayed_reward: float,
        short_term_weight: Optional[float] = None,
        long_term_weight: Optional[float] = None
    ) -> float:
        """
        计算总奖励

        总奖励 = α × 即时奖励 + (1-α) × 延迟奖励

        Args:
            immediate_reward: 即时奖励
            delayed_reward: 延迟奖励
            short_term_weight: 短期奖励权重(默认使用实例权重)
            long_term_weight: 长期奖励权重(默认使用实例权重)

        Returns:
            总奖励值
        """
        if short_term_weight is None:
            short_term_weight = self.short_term_weight
        if long_term_weight is None:
            long_term_weight = self.long_term_weight

        # 归一化权重
        total_weight = short_term_weight + long_term_weight
        if total_weight != 1.0:
            short_term_weight = short_term_weight / total_weight
            long_term_weight = long_term_weight / total_weight

        total_reward = (
            short_term_weight * immediate_reward +
            long_term_weight * delayed_reward
        )

        logger.debug(
            f"总奖励计算 - 即时: {immediate_reward:.3f}, "
            f"延迟: {delayed_reward:.3f}, "
            f"短期权重: {short_term_weight:.3f}, "
            f"长期权重: {long_term_weight:.3f}, "
            f"结果: {total_reward:.3f}"
        )

        return total_reward

    def calculate_all_rewards(
        self,
        satisfaction: float,
        is_violation: bool,
        violation_type: Optional[ViolationType] = None,
        historical_violation_rate: float = 0.0,
        response_time: float = 1.0,
        resolution_success: bool = True
    ) -> Dict[str, float]:
        """
        计算所有奖励（一步到位）

        Args:
            satisfaction: 客户满意度评分 (1-5)
            is_violation: 是否违规
            violation_type: 违规类型
            historical_violation_rate: 历史违规率
            response_time: 响应时间(秒)
            resolution_success: 问题是否解决

        Returns:
            包含immediate_reward, delayed_reward, total_reward的字典
        """
        # 计算即时奖励
        immediate_reward = self.calculate_immediate_reward(
            satisfaction=satisfaction,
            response_time=response_time,
            resolution_success=resolution_success
        )

        # 计算延迟奖励
        delayed_reward = self.calculate_delayed_reward(
            is_violation=is_violation,
            violation_type=violation_type,
            historical_violation_rate=historical_violation_rate
        )

        # 计算总奖励
        total_reward = self.calculate_total_reward(
            immediate_reward=immediate_reward,
            delayed_reward=delayed_reward
        )

        return {
            "immediate_reward": immediate_reward,
            "delayed_reward": delayed_reward,
            "total_reward": total_reward,
        }

    def _get_violation_penalty(self, violation_type: Optional[ViolationType]) -> float:
        """
        获取违规惩罚值

        Args:
            violation_type: 违规类型

        Returns:
            惩罚值
        """
        penalty_map = {
            ViolationType.UNAUTHORIZED_REFUND: 1.0,  # 最严重
            ViolationType.SKIP_VERIFICATION: 1.0,   # 最严重
            ViolationType.AGGRESSIVE_BEHAVIOR: 0.8,  # 严重
            ViolationType.OVER_PROMISE: 0.5,        # 中等
            ViolationType.OTHER: 0.3,               # 轻微
        }

        return penalty_map.get(violation_type, 0.5)

    def update_weights(
        self,
        short_term_weight: float,
        long_term_weight: float
    ) -> None:
        """
        更新奖励权重

        Args:
            short_term_weight: 新的短期奖励权重
            long_term_weight: 新的长期奖励权重
        """
        self.short_term_weight = short_term_weight
        self.long_term_weight = long_term_weight

        logger.info(
            f"奖励权重已更新 - 短期: {self.short_term_weight}, "
            f"长期: {self.long_term_weight}"
        )

    def get_reward_breakdown(
        self,
        immediate_reward: float,
        delayed_reward: float,
        total_reward: float
    ) -> Dict[str, Any]:
        """
        获取奖励分解信息

        Args:
            immediate_reward: 即时奖励
            delayed_reward: 延迟奖励
            total_reward: 总奖励

        Returns:
            奖励分解信息字典
        """
        return {
            "immediate": {
                "value": immediate_reward,
                "weight": self.short_term_weight,
                "contribution": immediate_reward * self.short_term_weight,
            },
            "delayed": {
                "value": delayed_reward,
                "weight": self.long_term_weight,
                "contribution": delayed_reward * self.long_term_weight,
            },
            "total": total_reward,
            "balance": "short_term" if immediate_reward > delayed_reward else "long_term",
        }


# ==================== 全局实例 ====================

# 全局奖励服务实例
reward_service = RewardService()


# ==================== 导出 ====================

__all__ = [
    "RewardService",
    "reward_service",
]
