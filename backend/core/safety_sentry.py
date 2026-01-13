"""
安全哨兵 - 实时检测和拦截违规

在智能体回复前进行检测，防止违规行为
"""
from typing import Dict, Optional
from dataclasses import dataclass
from utils.logger import logger


@dataclass
class ViolationAlert:
    """违规告警"""
    is_violation: bool          # 是否违规
    violation_type: str         # 违规类型
    severity: str               # 严重程度: low/medium/high
    reason: str                 # 违规原因
    suggested_fix: str          # 建议的修正方案
    goal_drift: bool = False    # 是否检测到目标漂移
    confidence: float = 0.0     # 置信度


class SafetySentry:
    """安全哨兵 - 实时检测和拦截违规"""

    def __init__(self):
        # 导入违规检测器
        from core.paper_violation_detector import paper_violation_detector
        self.detector = paper_violation_detector

        # 统计信息
        self.stats = {
            "total_checks": 0,
            "violations_detected": 0,
            "blocked_decisions": 0,
            "interception_failures": 0,
            "safe_alternatives_generated": 0
        }

        logger.info("安全哨兵初始化完成 - 使用LLM-as-a-Judge裁判")

    def check_decision(
        self,
        user_input: str,
        agent_response: str,
        chain_of_thought: Optional[str] = None
    ) -> ViolationAlert:
        """
        检查智能体决策,返回违规告警

        直接调用paper_violation_detector进行判定

        Args:
            user_input: 用户输入
            agent_response: 智能体回复内容
            chain_of_thought: 智能体思维链(可选)

        Returns:
            ViolationAlert: 违规告警对象
        """
        self.stats["total_checks"] += 1

        # 调用论文风格违规检测器
        is_violation, violation_type, judge_reason = self.detector.detect(
            user_input=user_input,
            agent_response=agent_response,
            chain_of_thought=chain_of_thought
        )

        if is_violation:
            self.stats["violations_detected"] += 1

            # 映射严重程度
            severity = self._map_severity(violation_type)

            # 生成建议修正方案
            suggested_fix = self._get_suggested_fix(violation_type)

            logger.warning(
                f"[安全哨兵] 检测到违规 - "
                f"类型: {violation_type}, "
                f"严重程度: {severity}, "
                f"原因: {judge_reason[:100]}..."
            )

            return ViolationAlert(
                is_violation=True,
                violation_type=violation_type or "unknown",
                severity=severity,
                reason=judge_reason,
                suggested_fix=suggested_fix,
                goal_drift="goal_drift" in judge_reason.lower() or "目标漂移" in judge_reason,
                confidence=0.85  # LLM裁判的置信度
            )
        else:
            logger.debug(f"[安全哨兵] 未检测到违规")
            return ViolationAlert(
                is_violation=False,
                violation_type="",
                severity="",
                reason="",
                suggested_fix="",
                goal_drift=False,
                confidence=0.85
            )

    def _map_severity(self, violation_type: Optional[str]) -> str:
        """
        根据违规类型映射严重程度

        Args:
            violation_type: 违规类型

        Returns:
            严重程度: low/medium/high
        """
        high_severity = ["unauthorized_refund", "skip_verification", "policy_violation"]
        medium_severity = ["over_promising", "goal_drift"]

        if violation_type in high_severity:
            return "high"
        elif violation_type in medium_severity:
            return "medium"
        else:
            return "low"

    def _get_suggested_fix(self, violation_type: Optional[str]) -> str:
        """
        根据违规类型生成建议修正方案

        Args:
            violation_type: 违规类型

        Returns:
            建议的修正方案
        """
        fixes = {
            "unauthorized_refund": "请向客户说明退款需要经过正常流程和审核,不能未经授权直接退款。",
            "over_promising": "请向客户说明实际情况,避免过度承诺。给出合理的时间预期。",
            "skip_verification": "请严格遵守公司政策和流程,不能绕过正常的验证和审核步骤。",
            "policy_violation": "请严格遵守公司政策,不能违规操作。",
            "goal_drift": "请重新聚焦合规准则,不要为了追求高分而牺牲合规性。"
        }

        return fixes.get(violation_type, "请重新审视回复内容,确保符合合规准则。")

    def suggest_safe_alternative(
        self,
        unsafe_response: str,
        alert: ViolationAlert,
        user_input: str = ""
    ) -> str:
        """
        为违规回复生成安全的替代方案（使用独立的安全回复生成服务）

        Args:
            unsafe_response: 不安全的回复
            alert: 违规告警
            user_input: 用户问题(可选)

        Returns:
            修正后的安全回复
        """
        try:
            # 使用独立的安全回复生成服务（qwen-max）
            from services.safe_response_service import safe_response_service

            safe_response = safe_response_service.generate_safe_response(
                unsafe_response=unsafe_response,
                violation_reason=alert.reason,
                suggested_fix=alert.suggested_fix,
                user_input=user_input
            )

            self.stats["safe_alternatives_generated"] += 1
            logger.info(f"[安全哨兵] 使用独立LLM(qwen-max)生成安全替代回复: {safe_response[:100]}...")
            return safe_response

        except Exception as e:
            logger.error(f"[安全哨兵] 安全回复生成失败: {e}, 使用降级方案")

            # 降级方案: 在原回复后添加警告
            warning = f"\n\n[安全提示] {alert.suggested_fix}"
            return unsafe_response + warning

    async def handle_violation_with_negative_feedback(
        self,
        user_input: str,
        agent_response: str,
        alert: ViolationAlert,
        replay_buffer
    ) -> Dict:
        """
        方案A: 负向反馈强制注入 + 双层验证

        当检测到违规时:
        1. 生成安全的替代回复
        2. 🆕 用裁判再次验证生成的回复是否合规（双层验证）
        3. 如果验证通过: 返回安全回复,标记拦截成功
        4. 如果验证失败: 返回原始回复,标记拦截失败
        5. 在ReplayBuffer中注入-5.0的负向反馈记录

        Args:
            user_input: 用户输入
            agent_response: 智能体的违规回复
            alert: 违规告警
            replay_buffer: 经验回放缓冲区

        Returns:
            Dict: {
                "response": 最终回复（安全或原始）,
                "interception_success": 是否拦截成功,
                "safe_response": 生成的安全回复（可能违规）,
                "verified_safe": 是否通过裁判验证
            }
        """
        logger.warning(
            f"[安全哨兵] 方案A启动 - 检测到{alert.violation_type}, "
            f"准备生成安全回复并注入负向反馈"
        )

        # 1. 生成安全的替代回复（使用qwen-max）
        safe_response = self.suggest_safe_alternative(
            unsafe_response=agent_response,
            alert=alert,
            user_input=user_input
        )

        # 2. 🆕 双层验证: 用裁判再次检测生成的回复
        logger.info(f"[安全哨兵] 双层验证 - 用裁判检测生成的安全回复...")
        is_violation, safe_violation_type, safe_reason = self.detector.detect(
            user_input=user_input,
            agent_response=safe_response
        )

        interception_success = False
        verified_safe = False
        final_response = agent_response  # 默认返回原始回复

        if not is_violation:  # 注意：detect返回is_violation，所以要用not取反
            # 验证通过 - 拦截成功
            interception_success = True
            verified_safe = True
            final_response = safe_response
            self.stats["blocked_decisions"] += 1
            logger.info(
                f"[安全哨兵] ✅ 拦截成功 - 安全回复已通过裁判验证"
            )
        else:
            # 验证失败 - 生成的回复仍违规
            interception_success = False
            verified_safe = False
            final_response = agent_response  # 返回原始不安全回复
            self.stats["interception_failures"] += 1
            logger.warning(
                f"[安全哨兵] ❌ 拦截失败 - 生成的回复仍违规: "
                f"{safe_violation_type}\n"
                f"   原因: {safe_reason[:100]}...\n"
                f"   将返回原始不安全回复给用户"
            )

        # 3. 在ReplayBuffer中注入负向反馈（无论拦截成功与否）
        if replay_buffer:
            replay_buffer.inject_negative_feedback(
                user_input=user_input,
                unsafe_response=agent_response,
                safe_response=safe_response,
                violation_type=alert.violation_type,
                judge_reason=alert.reason,
                penalty_reward=-5.0  # 温和的惩罚: 足以纠正1.0的错误信号
            )
            logger.info(
                f"[安全哨兵] 负向反馈已注入ReplayBuffer (奖励: -5.0), "
                f"这将纠正智能体的进化方向"
            )
        else:
            logger.error("[安全哨兵] ReplayBuffer未初始化,无法注入负向反馈")

        return {
            "response": final_response,
            "interception_success": interception_success,
            "safe_response": safe_response,
            "verified_safe": verified_safe
        }

    def get_statistics(self) -> Dict:
        """获取统计信息"""
        total_interception_attempts = self.stats["blocked_decisions"] + self.stats["interception_failures"]
        return {
            **self.stats,
            "violation_rate": (
                self.stats["violations_detected"] / max(self.stats["total_checks"], 1) * 100
            ),
            "interception_success_rate": (
                self.stats["blocked_decisions"] / max(total_interception_attempts, 1) * 100
            ) if total_interception_attempts > 0 else 0.0
        }

    def reset_statistics(self):
        """重置统计信息"""
        self.stats = {
            "total_checks": 0,
            "violations_detected": 0,
            "blocked_decisions": 0,
            "interception_failures": 0,
            "safe_alternatives_generated": 0
        }
        logger.info("安全哨兵统计信息已重置")


# ==================== 全局实例 ====================

# 全局安全哨兵实例
_safety_sentry: Optional[SafetySentry] = None


def get_safety_sentry() -> SafetySentry:
    """获取全局安全哨兵实例"""
    global _safety_sentry
    if _safety_sentry is None:
        _safety_sentry = SafetySentry()
    return _safety_sentry
