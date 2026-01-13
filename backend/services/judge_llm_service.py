"""
裁判LLM服务 - 专用于违规检测
"""
from typing import Dict, Any, Optional
import os
from pathlib import Path
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from utils.logger import logger
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)

# 确保在导入时就加载.env文件
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")


class JudgeLLMService:
    """裁判LLM服务 - 用于违规检测"""

    def __init__(
        self,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ):
        """初始化裁判LLM服务"""
        # 从环境变量读取裁判配置
        if model is None:
            model = os.environ.get('JUDGE_LLM_MODEL', 'qwen-coder-plus-latest')
        if temperature is None:
            temperature = float(os.environ.get('JUDGE_LLM_TEMPERATURE', '0.3'))
        if max_tokens is None:
            max_tokens = int(os.environ.get('JUDGE_LLM_MAX_TOKENS', '1000'))

        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens

        # 初始化LangChain ChatOpenAI（使用裁判专用配置）
        try:
            # 从环境变量读取裁判专用的API配置
            judge_api_key = os.environ.get('JUDGE_API_KEY', os.environ.get('OPENAI_API_KEY', ''))
            judge_api_base = os.environ.get('JUDGE_API_BASE', 'https://dashscope.aliyuncs.com/compatible-mode/v1')

            # 添加调试信息
            api_key_preview = judge_api_key[:10] if judge_api_key else 'N/A'
            logger.info(f"初始化裁判LLM - API Key: {api_key_preview}..., API Base: {judge_api_base}")

            # 直接传递API配置给ChatOpenAI（不修改全局环境变量）
            self.llm = ChatOpenAI(
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                request_timeout=30.0,
                openai_api_key=judge_api_key,
                openai_api_base=judge_api_base,
            )
            logger.info(
                f"裁判LLM初始化成功 - 模型: {model}, "
                f"温度: {temperature}, 最大tokens: {max_tokens}"
            )
        except Exception as e:
            logger.error(f"裁判LLM初始化失败: {e}")
            raise

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((ConnectionError, TimeoutError))
    )
    def generate_with_system_prompt(
        self,
        user_input: str,
        system_prompt: str,
        **kwargs
    ) -> str:
        """
        使用裁判LLM生成回复（带系统提示词）

        Args:
            user_input: 用户输入（判定请求）
            system_prompt: 系统提示词（裁判规则）
            **kwargs: 其他参数传递给LLM

        Returns:
            LLM生成的回复
        """
        try:
            # 构建消息列表
            messages = [SystemMessage(content=system_prompt)]
            messages.append(HumanMessage(content=user_input))

            # 调用LLM
            logger.debug(f"裁判LLM请求 - 用户输入: {user_input[:50]}...")
            response = self.llm.invoke(messages, **kwargs)
            result = response.content

            logger.debug(
                f"裁判LLM响应 - 长度: {len(result)}, "
                f"回复: {result[:100]}..."
            )

            return result

        except Exception as e:
            logger.error(f"裁判LLM调用失败: {e}")
            # 返回兜底回复
            return self._get_fallback_response(user_input)

    def _get_fallback_response(self, user_input: str) -> str:
        """
        获取兜底回复

        Args:
            user_input: 用户输入

        Returns:
            兜底回复
        """
        logger.warning(f"使用裁判LLM兜底回复")
        return '{"is_violation": false, "violation_type": null, "reason": "LLM调用失败，无法判定"}'


# ==================== 全局实例 ====================

# 全局裁判LLM服务实例
judge_llm_service = JudgeLLMService()


# ==================== 导出 ====================

__all__ = [
    "JudgeLLMService",
    "judge_llm_service",
]
