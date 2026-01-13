"""
安全回复生成服务
专门用于Safety Sentry生成安全替代回复
使用独立的LLM配置，与裁判模型分离
"""
import os
from dotenv import load_dotenv
from utils.logger import logger

load_dotenv()


class SafeResponseService:
    """安全回复生成服务"""

    def __init__(self):
        """初始化安全回复生成服务"""
        # 设置环境变量（临时覆盖，供LLMService使用）
        self.model = os.getenv("SAFE_RESPONSE_LLM_MODEL", "qwen-max")
        self.temperature = float(os.getenv("SAFE_RESPONSE_LLM_TEMPERATURE", "0.5"))
        self.max_tokens = int(os.getenv("SAFE_RESPONSE_LLM_MAX_TOKENS", "2000"))

        # 使用独立的API配置
        self.api_key = os.getenv("SAFE_RESPONSE_API_KEY")
        self.api_base = os.getenv("SAFE_RESPONSE_API_BASE")

        # 临时设置环境变量供LLMService读取
        original_agent_model = os.environ.get('AGENT_LLM_MODEL')
        original_agent_temp = os.environ.get('AGENT_LLM_TEMPERATURE')
        original_agent_tokens = os.environ.get('AGENT_LLM_MAX_TOKENS')

        os.environ['AGENT_LLM_MODEL'] = self.model
        os.environ['AGENT_LLM_TEMPERATURE'] = str(self.temperature)
        os.environ['AGENT_LLM_MAX_TOKENS'] = str(self.max_tokens)

        # 导入LLM服务（它从环境变量读取配置）
        from services.llm_service import LLMService
        self.llm_service = LLMService()

        # 恢复原始环境变量
        if original_agent_model:
            os.environ['AGENT_LLM_MODEL'] = original_agent_model
        else:
            os.environ.pop('AGENT_LLM_MODEL', None)

        if original_agent_temp:
            os.environ['AGENT_LLM_TEMPERATURE'] = original_agent_temp
        else:
            os.environ.pop('AGENT_LLM_TEMPERATURE', None)

        if original_agent_tokens:
            os.environ['AGENT_LLM_MAX_TOKENS'] = original_agent_tokens
        else:
            os.environ.pop('AGENT_LLM_MAX_TOKENS', None)

        logger.info(
            f"安全回复生成服务初始化完成 - "
            f"模型: {self.model}, 温度: {self.temperature}, "
            f"API Key: {self.api_key[:10] if self.api_key else 'None'}..., "
            f"API Base: {self.api_base}"
        )

    def generate_safe_response(
        self,
        unsafe_response: str,
        violation_reason: str,
        suggested_fix: str,
        user_input: str = ""
    ) -> str:
        """
        生成安全的替代回复

        Args:
            unsafe_response: 不安全的回复
            violation_reason: 违规原因
            suggested_fix: 建议修正方案
            user_input: 用户问题(可选)

        Returns:
            修正后的安全回复
        """
        # 构建提示词
        prompt = f"""你是一个客服安全专家，需要将违规的客服回复修改为安全的回复。

【客户问题】:
{user_input if user_input else "(无)"}

【不安全的回复】:
{unsafe_response}

【违规原因】:
{violation_reason}

【建议修正】:
{suggested_fix}

请生成一个安全的客服回复，要求：
1. 直接给出生成的安全回复，不要解释
2. 保持专业和礼貌的语气
3. 明确说明不能违规操作的原因
4. 提供合规的替代方案
5. 不要包含任何违规内容

安全回复:"""

        try:
            # 调用LLM生成安全回复
            safe_response = self.llm_service.generate_with_system_prompt(
                user_input=prompt,
                system_prompt="你是一个专业的客服安全专家，能够生成合规安全的客服回复。"
            )

            # 清理可能的markdown格式
            safe_response = safe_response.strip()
            if safe_response.startswith("```"):
                safe_response = safe_response.split("```")[1]
            if safe_response.startswith('"'):
                safe_response = safe_response.strip('"')

            logger.info(f"[安全回复生成] 成功生成安全回复: {safe_response[:100]}...")
            return safe_response

        except Exception as e:
            logger.error(f"[安全回复生成] LLM生成失败: {e}, 使用降级方案")

            # 降级方案: 返回简单的安全回复
            fallback_response = f"""非常抱歉，我需要遵守公司政策。

{suggested_fix}

让我帮您通过正规流程解决问题。"""
            return fallback_response


# 全局实例
safe_response_service = SafeResponseService()
