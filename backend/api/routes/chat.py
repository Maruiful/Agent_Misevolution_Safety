"""
对话API接口
处理用户对话请求
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from models.schemas import (
    ChatRequest,
    ChatResponse,
    Message,
    SessionContext,
)
from core.agent import agent_manager
from core.config import settings
from utils.logger import logger


router = APIRouter(
    prefix="/api/chat",
    tags=["对话"]
)


@router.post("", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    发送消息并获取回复（统一使用论文方法）

    Args:
        request: 对话请求

    Returns:
        对话响应（包含论文风格的违规检测和安全哨兵拦截）
    """
    try:
        logger.info(
            f"收到对话请求 - 会话: {request.session_id}, "
            f"轮次: {request.round_id}, 消息: {request.message[:50]}..."
        )

        # 获取或创建智能体
        agent = agent_manager.get_or_create_agent(request.session_id)

        # 处理消息（启用Few-shot学习以符合论文方法）
        response = await agent.process_message(
            user_input=request.message,
            round_id=request.round_id,
            use_fewshot=True  # ✅ 启用Few-shot学习，从历史经验中学习
        )

        # 🆕 使用论文风格的违规检测（LLM-as-a-Judge）
        from core.paper_violation_detector import paper_violation_detector

        is_violation, violation_type, judge_reason = paper_violation_detector.detect(
            user_input=request.message,
            agent_response=response.response,
            chain_of_thought=getattr(response, 'chain_of_thought', None)
        )

        # 🆕 安全哨兵拦截（根据前端传来的参数决定是否启用）
        sentry_blocked = False
        sentry_alert_type = None
        sentry_severity = None

        # 🆕 优先使用前端传来的enable_safety_sentry参数，而不是配置文件
        enable_sentry = request.enable_safety_sentry  # 从前端获取开关状态

        if is_violation and enable_sentry:
            logger.info(f"[安全哨兵] 检测到违规,启用方案A: 负向反馈强制注入 (前端控制: {enable_sentry})")

            # 导入安全哨兵
            from core.safety_sentry import SafetySentry

            # 创建安全哨兵实例（已复用paper_violation_detector,不会重复检测）
            sentry = SafetySentry()

            # 构造ViolationAlert（复用已判定的结果）
            from core.safety_sentry import ViolationAlert
            alert = ViolationAlert(
                is_violation=True,
                violation_type=violation_type or "unknown",
                severity=sentry._map_severity(violation_type),
                reason=judge_reason,
                suggested_fix=sentry._get_suggested_fix(violation_type),
                confidence=0.85
            )

            # 方案A: 负向反馈强制注入
            safe_response = await sentry.handle_violation_with_negative_feedback(
                user_input=request.message,
                agent_response=response.response,
                alert=alert,
                replay_buffer=agent.replay_buffer
            )

            # 替换为安全回复
            original_response = response.response
            response.response = safe_response

            # 标记哨兵拦截信息
            sentry_blocked = True
            sentry_alert_type = alert.violation_type
            sentry_severity = alert.severity

            logger.warning(
                f"[安全哨兵] 已拦截违规 - 类型: {alert.violation_type}, "
                f"原回复: {original_response[:50]}..., "
                f"安全回复: {safe_response[:50]}..."
            )

        # 更新响应的违规信息（使用论文方法的判定结果）
        response.is_violation = is_violation
        if violation_type:
            response.violation_type = violation_type
        if judge_reason:
            response.judge_reason = judge_reason  # 添加裁判理由

        # 添加哨兵拦截信息
        response.sentry_blocked = sentry_blocked
        if sentry_alert_type:
            response.sentry_alert_type = sentry_alert_type
        if sentry_severity:
            response.sentry_severity = sentry_severity

        logger.info(
            f"对话请求完成 - 轮次: {response.round_id}, "
            f"违规: {is_violation}, 哨兵拦截: {sentry_blocked}, "
            f"奖励: {response.total_reward:.3f}, "
            f"裁判理由: {judge_reason[:50] if judge_reason else 'N/A'}..."
        )

        return response

    except Exception as e:
        logger.error(f"对话请求处理失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history", response_model=List[Message])
async def get_chat_history(session_id: str):
    """
    获取对话历史

    Args:
        session_id: 会话ID

    Returns:
        消息历史列表
    """
    try:
        logger.info(f"获取对话历史 - 会话: {session_id}")

        # 获取智能体
        agent = agent_manager.get_or_create_agent(session_id)

        # 返回对话历史
        messages = agent.context.messages

        logger.info(f"返回对话历史 - 共 {len(messages)} 条消息")

        return messages

    except Exception as e:
        logger.error(f"获取对话历史失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/session", response_model=SessionContext)
async def get_session_info(session_id: str):
    """
    获取会话信息

    Args:
        session_id: 会话ID

    Returns:
        会话上下文
    """
    try:
        logger.info(f"获取会话信息 - 会话: {session_id}")

        # 获取智能体
        agent = agent_manager.get_or_create_agent(session_id)

        # 返回会话信息
        session_info = agent.get_session_info()

        logger.info(f"返回会话信息 - 轮次: {session_info['round_id']}")

        return agent.context

    except Exception as e:
        logger.error(f"获取会话信息失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/session/{session_id}")
async def delete_session(session_id: str):
    """
    删除会话

    Args:
        session_id: 会话ID

    Returns:
        删除结果
    """
    try:
        logger.info(f"删除会话 - 会话: {session_id}")

        # 移除智能体
        agent_manager.remove_agent(session_id)

        return {
            "code": 200,
            "message": "会话已删除",
            "data": {"session_id": session_id}
        }

    except Exception as e:
        logger.error(f"删除会话失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/session/reset")
async def reset_session(session_id: str):
    """
    重置会话

    Args:
        session_id: 会话ID

    Returns:
        重置结果
    """
    try:
        logger.info(f"重置会话 - 会话: {session_id}")

        # 获取智能体
        agent = agent_manager.get_or_create_agent(session_id)

        # 重置会话
        agent.reset_session()

        return {
            "code": 200,
            "message": "会话已重置",
            "data": {"session_id": session_id}
        }

    except Exception as e:
        logger.error(f"重置会话失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions")
async def list_all_sessions():
    """
    列出所有会话

    Returns:
        会话ID列表
    """
    try:
        logger.info("列出所有会话")

        sessions = agent_manager.get_all_sessions()

        return {
            "code": 200,
            "message": "success",
            "data": {
                "sessions": sessions,
                "count": len(sessions)
            }
        }

    except Exception as e:
        logger.error(f"列出会话失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/feedback")
async def submit_delayed_feedback(
    session_id: str,
    round_id: int,
    satisfaction: float,
    is_violation: bool = False,
    violation_type: Optional[str] = None
):
    """
    提交延迟反馈

    用于接收延迟反馈(如满意度评分)并更新奖励

    Args:
        session_id: 会话ID
        round_id: 轮次ID
        satisfaction: 满意度评分 (1-5)
        is_violation: 是否违规
        violation_type: 违规类型(可选)

    Returns:
        更新后的奖励信息
    """
    try:
        logger.info(
            f"接收延迟反馈 - 会话: {session_id}, "
            f"轮次: {round_id}, 满意度: {satisfaction}, "
            f"违规: {is_violation}"
        )

        # 获取智能体
        agent = agent_manager.get_or_create_agent(session_id)

        # 转换违规类型
        from models.enums import ViolationType
        violation_enum = None
        if violation_type:
            try:
                violation_enum = ViolationType[violation_type]
            except KeyError:
                logger.warning(f"未知的违规类型: {violation_type}")

        # 提交延迟反馈并更新奖励
        updated_rewards = await agent.submit_delayed_feedback(
            round_id=round_id,
            satisfaction=satisfaction,
            is_violation=is_violation,
            violation_type=violation_enum
        )

        return {
            "code": 200,
            "message": "延迟反馈已更新",
            "data": {
                "round_id": round_id,
                "delayed_reward": updated_rewards["delayed_reward"],
                "total_reward": updated_rewards["total_reward"]
            }
        }

    except ValueError as e:
        logger.error(f"延迟反馈失败: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"延迟反馈处理失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
