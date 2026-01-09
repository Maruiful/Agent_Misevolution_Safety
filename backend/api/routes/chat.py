"""
对话API接口
处理用户对话请求
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import List
from models.schemas import (
    ChatRequest,
    ChatResponse,
    Message,
    SessionContext,
)
from core.agent import agent_manager
from utils.logger import logger


router = APIRouter(
    prefix="/api/chat",
    tags=["对话"]
)


@router.post("", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    发送消息并获取回复

    Args:
        request: 对话请求

    Returns:
        对话响应
    """
    try:
        logger.info(
            f"收到对话请求 - 会话: {request.session_id}, "
            f"轮次: {request.round_id}, 消息: {request.message[:50]}..."
        )

        # 获取或创建智能体
        agent = agent_manager.get_or_create_agent(request.session_id)

        # 处理消息
        response = await agent.process_message(
            user_input=request.message,
            round_id=request.round_id
        )

        logger.info(
            f"对话请求完成 - 轮次: {response.round_id}, "
            f"违规: {response.is_violation}, 奖励: {response.total_reward:.3f}"
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
