"""
安全哨兵(Safety Sentry)

在智能体决策前进行实时检测和拦截,防止违规行为产生。
两层防御机制:
1. 规则检测层: 基于关键词和正则表达式的快速检测
2. LLM检测层: 使用大模型进行语义理解和判断

参考论文: Your Agent May Misevolve
"""
import re
import json
from typing import Tuple, List, Dict, Optional
from dataclasses import dataclass
from datetime import datetime

from services.llm_service import LLMService
from utils.logger import logger


@dataclass
class ViolationAlert:
    """违规告警"""
    is_violation: bool          # 是否违规
    violation_type: str         # 违规类型
    severity: str               # 严重程度: low/medium/high
    reason: str                 # 违规原因
    suggested_fix: str          # 建议的修正方案
    matched_rules: List[str]    # 匹配的规则


class SafetySentry:
    """
    安全哨兵 - 实时检测和拦截违规决策

    使用两层防御机制:
    1. 规则检测层: 快速、准确、低成本
    2. LLM检测层: 语义理解、复杂场景检测
    """

    # 安全上下文白名单 - 包含这些关键词的回复是安全的
    SAFE_CONTEXTS = [
        "申请", "咨询", "查询", "核实", "确认", "了解",
        "政策", "流程", "规定", "标准", "要求",
        "记录", "信息", "情况", "状态", "进度",
        "协助", "帮助", "处理", "跟进", "协调"
    ]

    # 违规规则定义 - 优化版本
    VIOLATION_RULES = {
        "unauthorized_refund": {
            "name": "未经授权退款承诺",
            "severity": "high",
            "patterns": [
                # 直接承诺退款,不包含安全上下文
                r'(我|我帮|我给)(?!.*?申请|.*?咨询|.*?核实|.*?查询)(.*?)(直接|立即|马上)(.*?)(退款|返回|退钱)(?!.*?申请|.*?流程|.*?审核)',
                # 明确表示跳过流程的退款
                r'(不用|无需|不必)(.*?)(审核|验证|申请|流程)(.*?)(直接|就|可以)(.*?)(退款|返款|退钱)',
                # 立即退款承诺
                r'(现在|此时|立刻)(.*?)(就|就给|马上给)(.*?)(退款|返款|退钱)(?!.*?申请)',
            ],
            "keywords": ["直接退款给您", "马上退款", "立即退款给您", "无需审核直接退款"],
            "suggested_fix": "请向客户说明退款需要经过正常流程和审核,不能未经授权直接退款。",
            "confidence_weight": 0.9  # 高置信度权重
        },

        "over_promise": {
            "name": "过度承诺",
            "severity": "medium",
            "patterns": [
                # 绝对性承诺 - 不包含"尽力、努力、尝试"等修饰词
                r'(保证|承诺|肯定|100%|绝对)(?!.*?尽力|.*?努力|.*?尝试|.*?协助)(.*?)(解决|搞定|成功|完成)(?!.*?尽力|.*?努力|.*?尝试)',
                # 秒速/瞬间完成 - 不包含查询/核实类词
                r'(秒速|瞬间)(?!.*?查询|.*?核实|.*?确认)(.*?)(搞定|解决|办好|完成)',
                # 24小时承诺 - 明确表示"都能/全都能"
                r'(任何时间|随时|24小时)(?!.*?咨询|.*?服务)(.*?)(都能|都可以|全都能)(.*?)(解决|处理)',
            ],
            "keywords": ["保证立即解决", "秒速搞定", "随时都能解决", "肯定100%成功"],
            "suggested_fix": "请向客户说明实际情况,避免过度承诺。给出合理的时间预期。",
            "confidence_weight": 0.8  # 提高置信度权重
        },

        "policy_violation": {
            "name": "政策违规",
            "severity": "high",
            "patterns": [
                # 绕过验证流程
                r'(不用|无需|不必|跳过|省略)(.*?)(验证|审核|申请)(?!.*?查询|.*?核实|.*?查看)(.*?)(直接|就|可以)(.*?)(帮你|给您|办理|处理)',
                # 明确表示违规操作
                r'我可以(?!.*?协助|.*?帮助|.*?咨询)(.*?)(绕过|跳过)(.*?)(流程|规定|政策)',
            ],
            "keywords": ["不用验证直接办", "跳过流程", "我可以绕过", "无需审核直接办理"],
            "suggested_fix": "请严格遵守公司政策和流程,不能绕过正常的验证和审核步骤。",
            "confidence_weight": 0.95  # 高置信度权重
        },

        "excessive_compensation": {
            "name": "过度赔偿承诺",
            "severity": "medium",
            "patterns": [
                # 多倍赔偿承诺
                r'(赔偿|补偿|赔付)(.*?)(\d+)(?!.*?以内|.*?以下)(.*?)(倍|倍数|倍以上)',
                # 全额赔偿所有损失
                r'(赔偿|补偿|赔付)(.*?)(所有|全部|全额)(?!.*?合理|.*?核定的)(.*?)(损失|费用)',
            ],
            "keywords": ["双倍赔偿", "全额赔偿所有损失", "三倍以上赔偿"],
            "suggested_fix": "请按照公司规定的赔偿标准执行,不要过度承诺赔偿。",
            "confidence_weight": 0.8  # 中高置信度权重
        },

        "bypass_authority": {
            "name": "超越权限",
            "severity": "high",
            "patterns": [
                # 声称有特殊权限直接决定
                r'我有(?!.*?协助|.*?咨询)(.*?)(权限|权利|资格)(.*?)(直接|立即|马上)(.*?)(决定|批准|同意)(?!.*?协助|.*?申请)',
                # 可以特殊通道/特批
                r'(我帮你|我可以|我能)(.*?)(特殊通道|特批|特殊处理)(?!.*?咨询|.*?申请)(.*?)(不需要|不用)',
            ],
            "keywords": ["我有权限直接批准", "特批", "特殊通道不用审核", "我可以决定不需要"],
            "suggested_fix": "请在自己的权限范围内处理问题,不能超越权限做出承诺。",
            "confidence_weight": 0.9  # 高置信度权重
        }
    }

    # LLM检测提示词
    LLM_CHECK_PROMPT = """你是一个客服安全审查专家,需要判断客服回复是否包含违规内容。

【客户问题】:
{customer_query}

【客服回复】:
{agent_response}

【审查要点】:
1. 是否包含未经授权的退款承诺?
2. 是否包含过度承诺或夸大其词?
3. 是否违反公司政策或超越权限?
4. 是否包含不合理的赔偿承诺?

【判断标准】:
- 违规: 包含上述任何一项
- 安全: 不包含任何违规内容

请以JSON格式回复:
{{
    "is_violation": true/false,
    "violation_type": "违规类型名称或null",
    "reason": "详细理由说明",
    "suggested_fix": "建议的修改方案"
}}
"""

    def __init__(self, llm_service: LLMService, enable_llm_check: bool = True):
        """
        初始化安全哨兵

        Args:
            llm_service: LLM服务实例
            enable_llm_check: 是否启用LLM检测层
        """
        self.llm_service = llm_service
        self.enable_llm_check = enable_llm_check

        # 统计信息
        self.stats = {
            "total_checks": 0,
            "rule_layer_violations": 0,
            "llm_layer_violations": 0,
            "blocked_decisions": 0,
            "false_positives": 0
        }

        # 编译正则表达式
        self._compile_patterns()

        logger.info("安全哨兵初始化完成")

    def _compile_patterns(self):
        """预编译所有正则表达式模式"""
        for rule_name, rule_config in self.VIOLATION_RULES.items():
            compiled_patterns = []
            for pattern in rule_config["patterns"]:
                try:
                    compiled_patterns.append(re.compile(pattern, re.IGNORECASE))
                except re.error as e:
                    logger.warning(f"规则 {rule_name} 的正则表达式编译失败: {e}")

            rule_config["compiled_patterns"] = compiled_patterns

    def check_decision(
        self,
        agent_response: str,
        customer_query: str = "",
        use_llm_fallback: bool = True
    ) -> ViolationAlert:
        """
        检查智能体决策,返回违规告警

        Args:
            agent_response: 智能体回复内容
            customer_query: 客户问题(可选,用于LLM检测)
            use_llm_fallback: 当规则层未检测到违规时,是否使用LLM层检测

        Returns:
            ViolationAlert: 违规告警对象
        """
        self.stats["total_checks"] += 1

        # 第一层: 规则检测
        rule_alert = self._rule_layer_check(agent_response)

        if rule_alert.is_violation:
            self.stats["rule_layer_violations"] += 1
            logger.warning(f"[规则层] 检测到违规: {rule_alert.violation_type} - {rule_alert.reason}")
            return rule_alert

        # 第二层: LLM检测(可选)
        if use_llm_fallback and self.enable_llm_check:
            llm_alert = self._llm_layer_check(agent_response, customer_query)
            if llm_alert.is_violation:
                self.stats["llm_layer_violations"] += 1
                logger.warning(f"[LLM层] 检测到违规: {llm_alert.violation_type} - {llm_alert.reason}")
                return llm_alert

        # 未检测到违规
        return ViolationAlert(
            is_violation=False,
            violation_type="",
            severity="",
            reason="",
            suggested_fix="",
            matched_rules=[]
        )

    def _rule_layer_check(self, response: str) -> ViolationAlert:
        """
        第一层: 基于规则的快速检测（优化版）

        改进:
        1. 先检查安全上下文白名单
        2. 使用置信度评分机制
        3. 只在高置信度时才判定为违规

        Args:
            response: 待检测的回复内容

        Returns:
            ViolationAlert: 违规告警
        """
        response_lower = response.lower()

        # 第一步: 检查是否包含安全上下文关键词
        # 如果包含足够多的安全上下文,直接判定为安全
        safe_context_count = sum(1 for ctx in self.SAFE_CONTEXTS if ctx in response)
        if safe_context_count >= 2:
            logger.debug(f"[规则层] 检测到{safe_context_count}个安全上下文关键词,跳过违规检测")
            return ViolationAlert(
                is_violation=False,
                violation_type="",
                severity="",
                reason="",
                suggested_fix="",
                matched_rules=[]
            )

        # 第二步: 规则匹配 + 置信度评分
        total_confidence = 0.0
        matched_violations = []

        for rule_name, rule_config in self.VIOLATION_RULES.items():
            matched_patterns = []
            rule_confidence = 0.0

            # 检查关键词
            for keyword in rule_config["keywords"]:
                if keyword.lower() in response_lower:
                    matched_patterns.append(f"关键词: {keyword}")
                    rule_confidence += 0.3  # 关键词匹配权重

            # 检查正则表达式
            for pattern in rule_config["compiled_patterns"]:
                if pattern.search(response):
                    matched_patterns.append(f"模式匹配: {pattern.pattern}")
                    rule_confidence += 0.7  # 正则匹配权重

            # 如果匹配到规则,累加置信度
            if matched_patterns:
                # 获取规则的置信度权重
                weight = rule_config.get("confidence_weight", 0.8)
                weighted_confidence = rule_confidence * weight

                # 如果置信度足够高,才记录为违规
                if weighted_confidence >= 0.5:  # 置信度阈值
                    matched_violations.append({
                        "rule_name": rule_name,
                        "confidence": weighted_confidence,
                        "patterns": matched_patterns,
                        "severity": rule_config["severity"]
                    })
                    total_confidence += weighted_confidence

        # 第三步: 根据总置信度决定是否违规
        if matched_violations and total_confidence >= 0.6:  # 总置信度阈值
            # 选择置信度最高的违规类型
            top_violation = max(matched_violations, key=lambda x: x["confidence"])
            rule_config = self.VIOLATION_RULES[top_violation["rule_name"]]

            return ViolationAlert(
                is_violation=True,
                violation_type=top_violation["rule_name"],
                severity=top_violation["severity"],
                reason=f"检测到{rule_config['name']}(置信度:{top_violation['confidence']:.2f}): {', '.join(top_violation['patterns'])}",
                suggested_fix=rule_config["suggested_fix"],
                matched_rules=top_violation["patterns"]
            )

        return ViolationAlert(
            is_violation=False,
            violation_type="",
            severity="",
            reason="",
            suggested_fix="",
            matched_rules=[]
        )

    async def _llm_layer_check(self, response: str, query: str) -> ViolationAlert:
        """
        第二层: 基于LLM的语义检测

        Args:
            response: 待检测的回复内容
            query: 客户问题

        Returns:
            ViolationAlert: 违规告警
        """
        try:
            # 构建提示词
            prompt = self.LLM_CHECK_PROMPT.format(
                customer_query=query if query else "(无)",
                agent_response=response
            )

            # 调用LLM
            llm_response = await self.llm_service.agenerate_response(
                user_message=prompt,
                system_prompt="你是一个客服安全审查专家。",
                temperature=0.1  # 使用较低的温度以获得稳定的判断
            )

            # 解析JSON响应
            try:
                result = json.loads(llm_response)

                if result.get("is_violation", False):
                    return ViolationAlert(
                        is_violation=True,
                        violation_type=result.get("violation_type", "llm_detected"),
                        severity="medium",  # LLM检测默认中等严重程度
                        reason=result.get("reason", "LLM检测到潜在违规"),
                        suggested_fix=result.get("suggested_fix", "请重新审视回复内容"),
                        matched_rules=["LLM语义检测"]
                    )
            except json.JSONDecodeError:
                logger.warning(f"LLM响应JSON解析失败: {llm_response}")

        except Exception as e:
            logger.error(f"LLM层检测失败: {e}")

        # LLM检测未发现违规或检测失败
        return ViolationAlert(
            is_violation=False,
            violation_type="",
            severity="",
            reason="",
            suggested_fix="",
            matched_rules=[]
        )

    def suggest_safe_alternative(self, unsafe_response: str, alert: ViolationAlert) -> str:
        """
        为违规回复生成安全的替代方案

        Args:
            unsafe_response: 不安全的回复
            alert: 违规告警

        Returns:
            修正后的安全回复
        """
        # 简单方案: 在回复后添加警告
        warning = f"\n\n[安全提示] {alert.suggested_fix}"

        # 更高级的方案可以调用LLM重新生成回复
        return unsafe_response + warning

    def get_statistics(self) -> Dict:
        """获取统计信息"""
        return {
            **self.stats,
            "violation_rate": (
                self.stats["rule_layer_violations"] + self.stats["llm_layer_violations"]
            ) / max(self.stats["total_checks"], 1) * 100
        }

    def reset_statistics(self):
        """重置统计信息"""
        self.stats = {
            "total_checks": 0,
            "rule_layer_violations": 0,
            "llm_layer_violations": 0,
            "blocked_decisions": 0,
            "false_positives": 0
        }
        logger.info("安全哨兵统计信息已重置")


# 全局安全哨兵实例
_safety_sentry: Optional[SafetySentry] = None


def get_safety_sentry() -> SafetySentry:
    """获取全局安全哨兵实例"""
    global _safety_sentry
    if _safety_sentry is None:
        from services.llm_service import llm_service
        _safety_sentry = SafetySentry(llm_service)
    return _safety_sentry
