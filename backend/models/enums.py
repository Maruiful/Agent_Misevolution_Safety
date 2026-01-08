"""
枚举类型定义
"""
from enum import Enum


class ViolationType(str, Enum):
    """违规类型枚举"""

    UNAUTHORIZED_REFUND = "unauthorized_refund"  # 未授权退款
    OVER_PROMISE = "over_promise"  # 过度承诺
    SKIP_VERIFICATION = "skip_verification"  # 跳过验证
    AGGRESSIVE_BEHAVIOR = "aggressive_behavior"  # 激进行为
    OTHER = "other"  # 其他违规

    @classmethod
    def get_description(cls, violation_type: str) -> str:
        """获取违规类型描述"""
        descriptions = {
            "unauthorized_refund": "未授权直接退款",
            "over_promise": "过度承诺无法兑现的服务",
            "skip_verification": "跳过必要的身份验证流程",
            "aggressive_behavior": "使用激进或不当语言",
            "other": "其他违规行为",
        }
        return descriptions.get(violation_type, "未知违规类型")


class EvolutionDimension(str, Enum):
    """演化维度枚举"""

    MEMORY_ACCUMULATION = "memory_accumulation"  # 记忆累积
    WORKFLOW_OPTIMIZATION = "workflow_optimization"  # 工作流优化


class MessageRole(str, Enum):
    """消息角色枚举"""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class RewardType(str, Enum):
    """奖励类型枚举"""

    IMMEDIATE = "immediate"  # 即时奖励
    DELAYED = "delayed"  # 延迟奖励
    TOTAL = "total"  # 总奖励


# 导出枚举
__all__ = [
    "ViolationType",
    "EvolutionDimension",
    "MessageRole",
    "RewardType",
]
