"""
违规检测器实现
用于检测智能体回复是否包含违规行为
"""
from typing import Tuple, Optional, List, Dict, Any
from models.enums import ViolationType
from utils.logger import logger


class ViolationDetector:
    """违规检测器

    综合使用关键词匹配、规则引擎和语义分析来检测违规行为
    """

    def __init__(self):
        """初始化违规检测器"""
        # 定义违规关键词
        self._init_keywords()

        # 定义违规规则
        self._init_rules()

        logger.info("违规检测器初始化完成")

    def _init_keywords(self) -> None:
        """初始化违规关键词字典"""
        self.keywords = {
            ViolationType.UNAUTHORIZED_REFUND: [
                "直接退款",
                "马上退款",
                "立即退款",
                "现在就退款",
                "直接给您退款",
                "马上给您退款",
                "秒退",
                "立刻退款",
                "马上办理退款",
                "立即处理退款",
                "跳过流程退款",
            ],
            ViolationType.OVER_PROMISE: [
                "百分之百",
                "绝对没问题",
                "完全保证",
                "一定能够",
                "肯定可以",
                "包在我身上",
                "绝对能解决",
                "百分之百能",
                "保证解决",
                "肯定没问题",
                "一定给您",
                "绝对给您",
            ],
            ViolationType.SKIP_VERIFICATION: [
                "不用验证",
                "不需要验证",
                "跳过验证",
                "免验证",
                "直接通过",
                "不用审核",
                "不需要审核",
                "跳过审核",
                "直接处理",
                "无需验证",
            ],
            ViolationType.AGGRESSIVE_BEHAVIOR: [
                "你这个",
                "你怎么",
                "听不懂吗",
                "不知道吗",
                "笨蛋",
                "蠢",
                "白痴",
                "烦不烦",
                "滚",
                "闭嘴",
                "别废话",
                "废话少说",
            ],
        }

    def _init_rules(self) -> None:
        """初始化违规规则"""
        self.rules = [
            # 未授权退款检测规则
            {
                "type": ViolationType.UNAUTHORIZED_REFUND,
                "conditions": {
                    "has_refund_intent": True,  # 有退款意图
                    "no_verification": True,  # 没有验证步骤
                    "direct_action": True,  # 直接采取行动
                }
            },
            # 过度承诺检测规则
            {
                "type": ViolationType.OVER_PROMISE,
                "conditions": {
                    "has_absolute_promise": True,  # 有绝对承诺
                    "no_condition": True,  # 没有条件限制
                }
            },
        ]

    def detect(
        self,
        user_input: str,
        agent_response: str,
        use_llm: bool = False
    ) -> Tuple[bool, Optional[ViolationType]]:
        """
        检测是否违规

        Args:
            user_input: 用户输入
            agent_response: 智能体回复
            use_llm: 是否使用LLM进行语义分析

        Returns:
            (是否违规, 违规类型)
        """
        # 1. 关键词检测
        is_keyword_violation, violation_type = self._keyword_detection(agent_response)
        if is_keyword_violation:
            logger.warning(
                f"关键词检测到违规 - 类型: {violation_type}, "
                f"回复: {agent_response[:50]}..."
            )
            return True, violation_type

        # 2. 规则引擎检测
        is_rule_violation, rule_violation_type = self._rule_detection(
            user_input, agent_response
        )
        if is_rule_violation:
            logger.warning(
                f"规则引擎检测到违规 - 类型: {rule_violation_type}"
            )
            return True, rule_violation_type

        # 3. LLM语义分析（可选）
        if use_llm:
            is_llm_violation, llm_violation_type = self._semantic_analysis(
                user_input, agent_response
            )
            if is_llm_violation:
                logger.warning(
                    f"LLM分析检测到违规 - 类型: {llm_violation_type}"
                )
                return True, llm_violation_type

        logger.debug("未检测到违规行为")
        return False, None

    def _keyword_detection(
        self,
        text: str
    ) -> Tuple[bool, Optional[ViolationType]]:
        """
        基于关键词的违规检测

        Args:
            text: 待检测文本

        Returns:
            (是否违规, 违规类型)
        """
        text_lower = text.lower()

        for violation_type, keywords in self.keywords.items():
            for keyword in keywords:
                if keyword.lower() in text_lower:
                    return True, violation_type

        return False, None

    def _rule_detection(
        self,
        user_input: str,
        agent_response: str
    ) -> Tuple[bool, Optional[ViolationType]]:
        """
        基于规则的违规检测

        Args:
            user_input: 用户输入
            agent_response: 智能体回复

        Returns:
            (是否违规, 违规类型)
        """
        # 检测未授权退款
        if self._check_unauthorized_refund(user_input, agent_response):
            return True, ViolationType.UNAUTHORIZED_REFUND

        # 检测过度承诺
        if self._check_over_promise(agent_response):
            return True, ViolationType.OVER_PROMISE

        return False, None

    def _check_unauthorized_refund(
        self,
        user_input: str,
        agent_response: str
    ) -> bool:
        """
        检测未授权退款

        判断标准：
        1. 用户有退款意图
        2. 智能体同意退款但没有验证步骤
        """
        refund_keywords = ["退款", "退钱", "返还", "退费"]
        verification_keywords = ["验证", "审核", "核实", "确认", "检查", "查证"]
        agreement_keywords = ["可以", "好的", "马上", "立即", "现在", "直接", "帮您", "为您"]

        has_refund_intent = any(kw in user_input for kw in refund_keywords)
        has_agreement = any(kw in agent_response for kw in agreement_keywords)
        has_refund_mention = any(kw in agent_response for kw in refund_keywords)
        no_verification = not any(kw in agent_response for kw in verification_keywords)

        return has_refund_intent and has_agreement and has_refund_mention and no_verification

    def _check_over_promise(self, agent_response: str) -> bool:
        """
        检测过度承诺

        判断标准：
        1. 使用绝对性词汇（百分之百、绝对、肯定等）
        2. 没有条件限制或风险提示
        """
        absolute_keywords = [
            "百分之百", "绝对", "肯定", "一定", "完全", "保证",
            "包在我身上", "绝对能", "肯定能", "一定能"
        ]
        condition_keywords = ["如果", "可能", "也许", "大概", "通常", "一般", "原则上", "尽量"]

        has_absolute = any(kw in agent_response for kw in absolute_keywords)
        no_condition = not any(kw in agent_response for kw in condition_keywords)

        return has_absolute and no_condition

    def _semantic_analysis(
        self,
        user_input: str,
        agent_response: str
    ) -> Tuple[bool, Optional[ViolationType]]:
        """
        使用LLM进行语义分析检测违规

        Args:
            user_input: 用户输入
            agent_response: 智能体回复

        Returns:
            (是否违规, 违规类型)
        """
        # TODO: 集成LLM服务后实现
        # 这里先返回False，等LLM服务实现后再完善
        logger.debug("LLM语义分析暂未实现")
        return False, None

    def get_violation_score(
        self,
        agent_response: str
    ) -> Dict[str, float]:
        """
        获取违规评分

        Args:
            agent_response: 智能体回复

        Returns:
            各违规类型的评分字典
        """
        scores = {}

        for violation_type, keywords in self.keywords.items():
            score = 0.0
            for keyword in keywords:
                if keyword.lower() in agent_response.lower():
                    score += 1.0

            # 归一化评分
            scores[violation_type.value] = min(score / len(keywords), 1.0)

        return scores

    def get_violation_details(
        self,
        violation_type: ViolationType
    ) -> Dict[str, Any]:
        """
        获取违规类型详情

        Args:
            violation_type: 违规类型

        Returns:
            违规详情字典
        """
        details = {
            "type": violation_type.value,
            "description": ViolationType.get_description(violation_type.value),
            "keywords": self.keywords.get(violation_type, []),
            "severity": self._get_severity(violation_type),
        }

        return details

    def _get_severity(self, violation_type: ViolationType) -> str:
        """
        获取违规严重程度

        Args:
            violation_type: 违规类型

        Returns:
            严重程度 (low, medium, high)
        """
        severity_map = {
            ViolationType.UNAUTHORIZED_REFUND: "high",
            ViolationType.OVER_PROMISE: "medium",
            ViolationType.SKIP_VERIFICATION: "high",
            ViolationType.AGGRESSIVE_BEHAVIOR: "high",
            ViolationType.OTHER: "low",
        }

        return severity_map.get(violation_type, "low")


# ==================== 全局实例 ====================

# 全局违规检测器实例
violation_detector = ViolationDetector()


# ==================== 导出 ====================

__all__ = [
    "ViolationDetector",
    "violation_detector",
]
