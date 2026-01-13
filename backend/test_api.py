"""测试API连接"""
import asyncio
from langchain_openai import ChatOpenAI
from core.config import settings


async def test_api():
    """测试API调用"""
    print("="*80)
    print("测试阿里云DashScope API连接")
    print("="*80)

    print(f"\n配置信息:")
    print(f"  API Key: {settings.llm.api_key[:20]}...")
    print(f"  API Base: {settings.llm.api_base}")
    print(f"  Model: {settings.llm.model}")
    print(f"  Temperature: {settings.llm.temperature}")

    # 初始化LLM
    llm = ChatOpenAI(
        model=settings.llm.model,
        temperature=settings.llm.temperature,
        max_tokens=settings.llm.max_tokens,
        openai_api_key=settings.llm.api_key,
        openai_api_base=settings.llm.api_base,
        request_timeout=30.0,
    )

    print("\n开始测试调用...")
    try:
        response = await llm.ainvoke([
            {"role": "user", "content": "你好，请用一句话回复我"}
        ])
        print(f"\n✅ API调用成功!")
        print(f"响应内容: {response.content}")
        return True
    except Exception as e:
        print(f"\n❌ API调用失败!")
        print(f"错误信息: {e}")
        return False


if __name__ == "__main__":
    success = asyncio.run(test_api())
    print("="*80)
