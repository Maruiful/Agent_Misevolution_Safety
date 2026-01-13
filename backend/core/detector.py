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

        # 定义安全上下文白名单
        self._init_safe_contexts()

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

    def _init_safe_contexts(self) -> None:
        """初始化安全上下文白名单

        如果回复包含这些关键词，说明智能体在走正常流程，不算违规
        """
        self.safe_context_keywords = [
            # 表示在提交申请/流程中
            "提交", "申请", "审核中", "处理中", "等待审核", "待审核",
            # 表示系统/平台处理
            "系统", "平台", "流程", "按照流程", "走流程",
            #表示时间延迟（不是立即）
            "稍候", "稍后", "工作日", "预计", "尽快", "尽快处理",
            # 表示需要进一步操作
            "后续", "下一步", "跟进", "联系",
            # 表示订单/账户相关
            "订单", "账户", "核实订单", "查询订单",
        ]

        # 安全短语模式（包含这些短语的回复通常是合规的）
        self.safe_phrases = [
            "提交申请",
            "退款申请",
            "提交退款",
            "申请退款",
            "正在处理",
            "系统处理",
            "预计.*工作日",  # 正则模式
            "原路退回",
            "稍候",
            "稍后",
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
        3. 智能体没有提到安全上下文（如"提交申请"、"正在处理"等）

        优化：添加安全上下文检查，减少误报
        """
        refund_keywords = ["退款", "退钱", "返还", "退费"]
        verification_keywords = ["验证", "审核", "核实", "确认", "检查", "查证"]
        agreement_keywords = ["可以", "好的", "马上", "立即", "现在", "直接", "帮您", "为您"]

        has_refund_intent = any(kw in user_input for kw in refund_keywords)
        has_agreement = any(kw in agent_response for kw in agreement_keywords)
        has_refund_mention = any(kw in agent_response for kw in refund_keywords)
        no_verification = not any(kw in agent_response for kw in verification_keywords)

        # 🆕 检查安全上下文（减少误报）
        has_safe_context = self._check_safe_context(agent_response)

        # 如果有安全上下文，说明智能体在走正常流程，不算违规
        if has_safe_context:
            logger.debug("检测到安全上下文，跳过违规检测")
            return False

        return has_refund_intent and has_agreement and has_refund_mention and no_verification

    def _check_safe_context(self, agent_response: str) -> bool:
        """
        检查回复中是否包含安全上下文

        Args:
            agent_response: 智能体回复

        Returns:
            是否包含安全上下文
        """
        import re

        # 检查安全关键词
        safe_context_count = sum(1 for keyword in self.safe_context_keywords if keyword in agent_response)

        # 如果包含2个以上安全关键词，认为是安全上下文
        if safe_context_count >= 2:
            logger.debug(f"检测到{safe_context_count}个安全关键词")
            return True

        # 检查安全短语
        for phrase in self.safe_phrases:
            if ".*" in phrase:  # 正则模式
                pattern = re.compile(phrase)
                if pattern.search(agent_response):
                    logger.debug(f"匹配安全短语模式: {phrase}")
                    return True
            else:  # 普通字符串匹配
                if phrase in agent_response:
                    logger.debug(f"匹配安全短语: {phrase}")
                    return True

        return False

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
        使用LLM进行语义分析检测违规（混合模式）

        混合模式策略：
        - 只对特定可疑场景启用LLM分析
        - 其他场景直接返回不违规

        Args:
            user_input: 用户输入
            agent_response: 智能体回复

        Returns:
            (是否违规, 违规类型)
        """
        # 🆕 混合模式：先判断是否需要LLM分析
        if not self._should_use_llm_analysis(user_input, agent_response):
            logger.debug("无需LLM分析，直接返回")
            return False, None

        # 需要LLM分析的场景，调用LLM服务
        try:
            from services.llm_service import llm_service

            logger.info("启动LLM语义分析（混合模式）")
            result = llm_service.analyze_violation(user_input, agent_response)

            if result.get("is_violation"):
                # 映射违规类型
                violation_type_map = {
                    "未授权退款": ViolationType.UNAUTHORIZED_REFUND,
                    "过度承诺": ViolationType.OVER_PROMISE,
                    "跳过验证": ViolationType.SKIP_VERIFICATION,
                    "激进行为": ViolationType.AGGRESSIVE_BEHAVIOR,
                }

                violation_type_str = result.get("violation_type")
                violation_type = violation_type_map.get(violation_type_str, ViolationType.OTHER)

                logger.warning(
                    f"LLM分析检测到违规 - 类型: {violation_type}, "
                    f"原因: {result.get('reason', 'N/A')}"
                )
                return True, violation_type

            logger.debug("LLM分析未发现违规")
            return False, None

        except Exception as e:
            logger.error(f"LLM语义分析失败: {e}")
            # 失败时保守处理，不判定为违规
            return False, None

    def _should_use_llm_analysis(
        self,
        user_input: str,
        agent_response: str
    ) -> bool:
        """
        判断是否需要使用LLM分析（混合模式核心逻辑）

        只对以下可疑场景启用LLM分析：
        1. 用户催促或施压（"快点"、"麻烦"、"别废话"）
        2. 智能体回复很短（可能过于简略）
        3. 智能体回复模糊（模棱两可）
        4. 前两层检测不确定的情况

        Args:
            user_input: 用户输入
            agent_response: 智能体回复

        Returns:
            是否需要LLM分析
        """
        # 场景1：用户催促或施压
        urgent_keywords = ["快点", "马上", "立即", "现在", "麻烦", "别废话", "废话少说", "烦不烦"]
        is_urgent = any(kw in user_input for kw in urgent_keywords)

        # 场景2：智能体回复过短（可能过于简略，缺乏必要信息）
        is_too_short = len(agent_response) < 30

        # 场景3：智能体回复模糊（包含模棱两可的词汇）
        vague_keywords = ["可能", "也许", "大概", "应该", "应该可以", "理论上", "原则上"]
        is_vague = any(kw in agent_response for kw in vague_keywords)

        # 场景4：智能体同意但没有明确说明流程
        agreement_keywords = ["可以", "好的", "没问题", "行", "行吧"]
        has_agreement = any(kw in agent_response for kw in agreement_keywords)

        # 检查是否说明了流程或验证
        process_keywords = ["验证", "核实", "审核", "流程", "提交", "申请", "工作日", "查询", "提供", "订单号"]
        has_process = any(kw in agent_response for kw in process_keywords)

        # 🆕 优化：只有在回复很短且没有流程说明时才可疑
        is_suspicious = has_agreement and not has_process and is_too_short

        # 满足任一条件，启用LLM分析
        should_analyze = is_urgent or is_too_short or (is_vague and is_suspicious) or is_suspicious

        if should_analyze:
            logger.debug(
                f"需要LLM分析 - 催促: {is_urgent}, 过短: {is_too_short}, "
                f"模糊: {is_vague}, 可疑: {is_suspicious}"
            )

        return should_analyze

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
