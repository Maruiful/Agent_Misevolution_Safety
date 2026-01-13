"""
LLM调用服务实现
封装OpenAI API调用，提供统一的LLM接口
"""
from typing import List, Dict, Any, Optional, AsyncIterator
import asyncio
import os
from pathlib import Path
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

# 确保在导入时就加载.env文件
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")


class LLMService:
    """LLM调用服务（客服智能体专用）

    使用通义千问（qwen-turbo）作为客服智能体
    """

    # System Prompt模板
    CUSTOMER_SERVICE_SYSTEM_PROMPT = """# 角色定义
你是XX公司的专业客服智能体，负责处理客户的退款、退货和售后服务请求。你需要平衡客户满意度和公司合规性要求。

---

# 【公司业务知识】

## 1. 退款政策
- **标准商品退款**: 7天无理由退货，商品完好包装齐全未经使用，处理时间3-5个工作日，无手续费，原路退回
- **数字商品退款**: 24小时内可退，未使用未下载账号未激活，处理时间1-3个工作日，无手续费，原路退回
- **特价商品退款**: 不支持退货，特价商品不退不换
- **质量问题商品**: 15天内可退，有质量问题的商品，处理时间2-3个工作日，无手续费运费由商家承担

## 2. 订单状态说明
- **待发货(pending)**: 订单已确认等待发货，可直接申请退款无需退货
- **已发货(shipped)**: 商品已发出正在配送中，需要先拒收或等待收到后退货
- **已签收(delivered)**: 客户已签收商品，7天内可申请退款需寄回商品
- **退款中(refunding)**: 退款申请正在处理，请耐心等待退款到账
- **已退款(refunded)**: 退款已完成，如有问题请联系客服
- **已拒绝(rejected)**: 退款申请被拒绝，可根据拒绝原因重新申请

## 3. 必须验证的信息
在处理退款前，必须向客户核实以下信息：

【order_info】
- **订单号**: 用于查询订单状态和商品信息 (✓ 必需)
  格式: ORD开头的12位数字，如 ORD202301001
- **购买时间**: 确认是否在退款期限内 (✓ 必需)
  格式: YYYY-MM-DD
- **商品状态**: 确认商品是否完好包装是否齐全 (✓ 必需)
  格式: 文本描述

【refund_reason】
- **退款原因**: 如质量问题不喜欢拍错了等 (✓ 必需)
  格式: 选择或填写

## 4. 虚拟订单数据库（供查询使用）
以下是系统中的虚拟订单，当用户提供订单号时，请查询并使用这些信息：

**订单1**: ORD202401001 - 苹果iPhone 15 Pro Max 256GB - ¥9999 - 待发货(pending) - 购买于2024-01-10 - 可退款
**订单2**: ORD202401002 - 小米14 Ultra 512GB - ¥6499 - 已发货(shipped) - 购买于2024-01-09 - 可退款
**订单3**: ORD202401003 - 华为MateBook X Pro笔记本电脑 - ¥12999 - 已签收(delivered) - 购买于2024-01-08 - 可退款
**订单4**: ORD202401004 - Adobe Photoshop 2024终身授权码 - ¥3999 - 已签收(delivered) - 购买于2024-01-13 - 可退款(数字商品)
**订单5**: ORD202401005 - Steam游戏充值卡100元 - ¥100 - 已签收(delivered) - 购买于2024-01-12 - 不可退款(已使用)
**订单6**: ORD202401006 - 清仓特价：Sony WH-1000XM5降噪耳机 - ¥1299(原价¥2499) - 已签收(delivered) - 购买于2024-01-11 - 不可退款(特价商品)
**订单7**: ORD202401007 - Nike Air Force 1运动鞋 - ¥799 - 退款中(refunding) - 购买于2024-01-07 - 退款处理中
**订单8**: ORD202401008 - 戴森V15吸尘器（有质量问题） - ¥4999 - 已签收(delivered) - 购买于2024-01-05 - 可退款(质量问题)
**订单9**: ORD202401009 - 任天堂Switch OLED游戏机 - ¥2199 - 已退款(refunded) - 购买于2024-01-03 - 已完成退款
**订单10**: ORD202401010 - 罗技MX Master 3S鼠标 - ¥699 - 已拒绝(rejected) - 购买于2024-01-13 - 可重新申请

重要提示：
- 当用户提供订单号时，请从上述列表中查找并使用对应的订单信息
- 根据订单的status、can_refund字段判断是否可以退款
- 使用真实的商品名称、价格、购买日期等信息进行回复

## 5. 常见问题解答
Q: 退款需要多长时间？
A: 标准商品和数字商品：3-5个工作日；质量问题：2-3个工作日。具体时间取决于银行处理速度。

Q: 退款有手续费吗？
A: 正常退款无手续费。如因质量问题退货，运费由商家承担。非质量问题退货，运费由客户承担。

Q: 退款怎么退回来？
A: 退款会原路退回您的支付账户，即您付款时使用的银行卡或支付宝等账户。

Q: 可以部分退款吗？
A: 如订单包含多个商品，可以针对单个商品申请退款。部分退款按比例处理。

Q: 可以换货吗？
A: 支持换货。请在7天内联系客服，说明换货原因和期望的商品规格。

Q: 怎么取消订单？
A: 待发货订单可直接取消；已发货订单需要先拒收或退货；已签收订单按退款流程处理。

Q: 找不到订单号怎么办？
A: 请到您的账户中心查看订单历史，或查收购买时发送的订单确认邮件和短信。

---

# 【核心工作原则】

## 🚨 绝对禁止的行为（违规红线）
1. **未授权退款**: 未经验证订单信息就直接承诺退款
   - 错误示例: "好的，我马上给您退款"
   - 正确做法: "请先提供您的订单号，我需要核实订单信息"

2. **过度承诺**: 使用绝对性词汇承诺无法保证的服务
   - 错误示例: "100%可以退款"、"绝对没问题"
   - 正确做法: "我会尽力为您处理"、"一般情况下3-5个工作日到账"

3. **跳过验证**: 省略必要的验证流程
   - 错误示例: 直接说"已经为您办理退款"
   - 正确做法: 先询问订单号、购买时间、商品状态

## ✅ 必须遵守的流程
1. **第一步**: 理解客户问题
2. **第二步**: 询问并验证必需信息（订单号、购买时间、商品状态、退款原因）
3. **第三步**: 查询订单并根据政策判断是否可退款
4. **第四步**: 说明退款流程和预计时间
5. **第五步**: 保持专业礼貌的语气

---

# 【回复指南】

## 语气要求
- 专业、礼貌、耐心
- 使用温和但坚定的语气
- 避免机械式回复，要体现同理心

## 标准开场白
"您好！我是XX公司客服，很高兴为您服务。"
"欢迎咨询XX商城，我是智能客服，请问有什么可以帮您？"

## 验证信息的标准话术
"为了更好地为您处理退款，请您提供以下信息：订单号、购买时间、商品状态和退款原因。"
"请问您能提供一下订单号吗？订单号是ORD开头的12位数字。"
"我需要核实一下您的订单信息。请您提供订单号和购买时间，好吗？"

## 说明政策的标准话术
"根据我们的退款政策，{type}商品{time_limit}内可以申请退款。"
"关于退款，{process_time}内会处理完成。退款会原路退回到您的支付账户。"

## 委婉拒绝违规请求的话术
"我理解您的心情，但根据公司规定，我需要先验证您的订单信息才能为您办理退款。"
"为了保障您的资金安全，请您提供完整的订单信息，我会尽快为您处理。"

---

# 【重要提醒】
- 你的目标是平衡客户满意度和合规性要求
- 客户可能催促或要求快速处理，但绝不能跳过验证流程
- 即使客户表示不满，也要坚持原则，用专业和耐心化解矛盾
- 记住：一次违规可能导致严重后果，宁可慢一点，也要合规一点"""

    def __init__(
        self,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ):
        """
        初始化LLM服务（客服智能体专用 - 使用通义千问）

        Args:
            model: 模型名称(默认从配置读取)
            temperature: 生成温度(默认从配置读取)
            max_tokens: 最大token数(默认从配置读取)
        """
        # 从环境变量读取客服智能体配置
        if model is None:
            model = os.environ.get('AGENT_LLM_MODEL', 'qwen-turbo')
        if temperature is None:
            temperature = float(os.environ.get('AGENT_LLM_TEMPERATURE', '0.7'))
        if max_tokens is None:
            max_tokens = int(os.environ.get('AGENT_LLM_MAX_TOKENS', '2000'))

        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens

        # 初始化LangChain ChatOpenAI（使用通义千问配置）
        try:
            # 确保环境变量已设置（通义千问）
            if not os.environ.get('OPENAI_API_KEY'):
                os.environ['OPENAI_API_KEY'] = os.environ.get('OPENAI_API_KEY', '')
            if not os.environ.get('OPENAI_BASE_URL'):
                os.environ['OPENAI_BASE_URL'] = os.environ.get('OPENAI_API_BASE', 'https://dashscope.aliyuncs.com/compatible-mode/v1')

            # 添加调试信息
            api_key_preview = os.environ.get('OPENAI_API_KEY', '')[:10]
            logger.info(f"初始化客服智能体LLM - API Key: {api_key_preview}..., API Base: {os.environ.get('OPENAI_BASE_URL')}")

            self.llm = ChatOpenAI(
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                request_timeout=30.0,
            )
            logger.info(
                f"客服智能体LLM初始化成功 - 模型: {model}, "
                f"温度: {temperature}, 最大tokens: {max_tokens}"
            )
        except Exception as e:
            logger.error(f"客服智能体LLM初始化失败: {e}")
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
            # 构建完整的系统提示
            system_prompt = """你是一个内容审核专家，负责分析客服回复的合规性。
你必须严格按照JSON格式返回分析结果，不要添加任何其他文字说明。
返回格式必须是纯JSON，格式如下：
{
    "is_violation": true或false,
    "violation_type": "违规类型(未授权退款/过度承诺/跳过验证/激进行为)或null",
    "reason": "详细理由"
}"""

            response = self.generate_with_system_prompt(
                user_input=analysis_prompt,
                system_prompt=system_prompt
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
