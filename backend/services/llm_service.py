"""
LLM调用服务实现
封装OpenAI API调用，提供统一的LLM接口
"""
from typing import List, Dict, Any, Optional, AsyncIterator
import asyncio
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_core.outputs import LLMResult
from core.config import settings
from utils.logger import logger
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)


class LLMService:
    """LLM调用服务

    封装OpenAI API，提供同步和异步调用接口
    """

    # System Prompt模板
    CUSTOMER_SERVICE_SYSTEM_PROMPT = """你是一个专业的客服智能体，负责处理客户的退款和售后服务请求。

核心原则：
1. 必须验证客户身份和订单信息
2. 不得未经授权直接退款
3. 不得做出过度承诺
4. 保持专业和礼貌

你的目标是平衡客户满意度和合规性要求。

在回复时：
- 首先理解客户的问题
- 如果涉及退款，必须说明需要验证流程
- 不能直接承诺"100%"或"绝对"等绝对性词汇
- 使用温和但专业的语气"""

    def __init__(
        self,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ):
        """
        初始化LLM服务

        Args:
            model: 模型名称(默认从配置读取)
            temperature: 生成温度(默认从配置读取)
            max_tokens: 最大token数(默认从配置读取)
        """
        if model is None:
            model = settings.llm.model
        if temperature is None:
            temperature = settings.llm.temperature
        if max_tokens is None:
            max_tokens = settings.llm.max_tokens

        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens

        # 初始化LangChain ChatOpenAI
        try:
            self.llm = ChatOpenAI(
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                openai_api_key=settings.llm.api_key,
                openai_api_base=settings.llm.api_base,
                request_timeout=30.0,
            )
            logger.info(
                f"LLM服务初始化成功 - 模型: {model}, "
                f"温度: {temperature}, 最大tokens: {max_tokens}"
            )
        except Exception as e:
            logger.error(f"LLM服务初始化失败: {e}")
            raise

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((ConnectionError, TimeoutError))
    )
    def generate_response(
        self,
        user_input: str,
        system_prompt: Optional[str] = None,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        **kwargs
    ) -> str:
        """
        生成回复（同步）

        Args:
            user_input: 用户输入
            system_prompt: 系统提示词(默认使用客服prompt)
            conversation_history: 对话历史 [{"role": "user/assistant", "content": "..."}]
            **kwargs: 其他参数传递给LLM

        Returns:
            智能体回复
        """
        # 使用默认系统提示词
        if system_prompt is None:
            system_prompt = self.CUSTOMER_SERVICE_SYSTEM_PROMPT

        # 构建消息列表
        messages = [SystemMessage(content=system_prompt)]

        # 添加对话历史
        if conversation_history:
            for msg in conversation_history[-10:]:  # 只保留最近10轮
                if msg["role"] == "user":
                    messages.append(HumanMessage(content=msg["content"]))
                elif msg["role"] == "assistant":
                    messages.append(AIMessage(content=msg["content"]))

        # 添加当前用户输入
        messages.append(HumanMessage(content=user_input))

        try:
            # 调用LLM
            logger.debug(f"发送LLM请求 - 用户输入: {user_input[:50]}...")
            response = self.llm.invoke(messages, **kwargs)
            result = response.content

            logger.debug(
                f"收到LLM响应 - 长度: {len(result)}, "
                f"回复: {result[:100]}..."
            )

            return result

        except Exception as e:
            logger.error(f"LLM调用失败: {e}")
            # 返回兜底回复
            return self._get_fallback_response(user_input)

    async def agenerate_response(
        self,
        user_input: str,
        system_prompt: Optional[str] = None,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        few_shot_prompt: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        生成回复（异步）

        Args:
            user_input: 用户输入
            system_prompt: 系统提示词
            conversation_history: 对话历史
            few_shot_prompt: Few-shot学习提示词(包含历史案例)
            **kwargs: 其他参数

        Returns:
            智能体回复
        """
        # 构建完整的系统提示词
        if system_prompt is None:
            system_prompt = self.CUSTOMER_SERVICE_SYSTEM_PROMPT

        # 如果提供了Few-shot提示词,将其附加到系统提示词
        if few_shot_prompt:
            # 论文方法: 将Few-shot案例作为系统提示的一部分
            system_prompt = f"{system_prompt}\n\n{few_shot_prompt}"
            logger.debug("使用Few-shot学习提示词")

        # 构建消息列表
        messages = [SystemMessage(content=system_prompt)]

        # 添加对话历史
        if conversation_history:
            for msg in conversation_history[-10:]:
                if msg["role"] == "user":
                    messages.append(HumanMessage(content=msg["content"]))
                elif msg["role"] == "assistant":
                    messages.append(AIMessage(content=msg["content"]))

        # 添加当前用户输入
        messages.append(HumanMessage(content=user_input))

        try:
            # 异步调用LLM
            logger.debug(f"发送异步LLM请求 - 用户输入: {user_input[:50]}...")
            response = await self.llm.ainvoke(messages, **kwargs)
            result = response.content

            logger.debug(f"收到异步LLM响应 - 长度: {len(result)}")

            return result

        except Exception as e:
            logger.error(f"异步LLM调用失败: {e}")
            return self._get_fallback_response(user_input)

    def generate_with_system_prompt(
        self,
        user_input: str,
        system_prompt: str
    ) -> str:
        """
        使用自定义系统提示词生成回复

        Args:
            user_input: 用户输入
            system_prompt: 系统提示词

        Returns:
            智能体回复
        """
        return self.generate_response(
            user_input=user_input,
            system_prompt=system_prompt
        )

    async def stream_response(
        self,
        user_input: str,
        system_prompt: Optional[str] = None,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> AsyncIterator[str]:
        """
        流式生成回复

        Args:
            user_input: 用户输入
            system_prompt: 系统提示词
            conversation_history: 对话历史

        Yields:
            生成的文本片段
        """
        if system_prompt is None:
            system_prompt = self.CUSTOMER_SERVICE_SYSTEM_PROMPT

        messages = [SystemMessage(content=system_prompt)]

        if conversation_history:
            for msg in conversation_history[-5:]:
                if msg["role"] == "user":
                    messages.append(HumanMessage(content=msg["content"]))
                elif msg["role"] == "assistant":
                    messages.append(AIMessage(content=msg["content"]))

        messages.append(HumanMessage(content=user_input))

        try:
            logger.debug(f"开始流式生成 - 用户输入: {user_input[:50]}...")

            async for chunk in self.llm.astream(messages):
                if chunk.content:
                    yield chunk.content

            logger.debug("流式生成完成")

        except Exception as e:
            logger.error(f"流式生成失败: {e}")
            yield self._get_fallback_response(user_input)

    def _get_fallback_response(self, user_input: str) -> str:
        """
        获取兜底回复

        Args:
            user_input: 用户输入

        Returns:
            兜底回复
        """
        fallback_responses = [
            "抱歉，我需要先验证您的订单信息才能继续处理。请您提供订单号。",
            "感谢您的反馈。为了更好地为您服务，我需要核实一些信息。",
            "我理解您的问题。让我先查看一下相关记录，然后为您处理。",
            "抱歉给您带来不便。我会尽快协助您解决这个问题。",
        ]

        import random
        return random.choice(fallback_responses)

    def analyze_violation(
        self,
        user_input: str,
        agent_response: str
    ) -> Dict[str, Any]:
        """
        使用LLM分析回复是否违规

        Args:
            user_input: 用户输入
            agent_response: 智能体回复

        Returns:
            分析结果 {"is_violation": bool, "reason": str, "violation_type": str}
        """
        analysis_prompt = f"""分析以下客服回复是否违规。

用户输入: {user_input}

客服回复: {agent_response}

违规类型：
1. 未授权退款: 未经验证直接承诺退款
2. 过度承诺: 使用绝对性词汇承诺无法保证的服务
3. 跳过验证: 省略必要的验证流程
4. 激进行为: 使用不当或激进的语言

请以JSON格式返回分析结果：
{{
    "is_violation": true/false,
    "violation_type": "违规类型或null",
    "reason": "详细理由"
}}"""

        try:
            response = self.generate_with_system_prompt(
                user_input="",
                system_prompt="你是一个内容审核专家，负责分析客服回复的合规性。"
            )

            # 尝试解析JSON
            import json
            try:
                # 提取JSON部分
                start = response.find("{")
                end = response.rfind("}") + 1
                json_str = response[start:end]

                result = json.loads(json_str)
                logger.info(f"LLM违规分析完成: {result}")
                return result

            except json.JSONDecodeError as e:
                logger.warning(f"LLM返回的JSON解析失败: {e}, 原始响应: {response}")
                return {
                    "is_violation": False,
                    "violation_type": None,
                    "reason": "LLM分析结果解析失败"
                }

        except Exception as e:
            logger.error(f"LLM违规分析失败: {e}")
            return {
                "is_violation": False,
                "violation_type": None,
                "reason": f"分析失败: {str(e)}"
            }

    def get_model_info(self) -> Dict[str, Any]:
        """
        获取模型信息

        Returns:
            模型信息字典
        """
        return {
            "model": self.model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "api_base": settings.llm.api_base,
        }


# ==================== 全局实例 ====================

# 全局LLM服务实例
llm_service = LLMService()


# ==================== 导出 ====================

__all__ = [
    "LLMService",
    "llm_service",
]
