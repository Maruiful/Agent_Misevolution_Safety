"""简单测试API连接"""
import requests
import json
from core.config import settings


def test_api_direct():
    """直接测试API调用"""
    print("="*80)
    print("测试阿里云DashScope API连接（直接调用）")
    print("="*80)

    print(f"\n配置信息:")
    print(f"  API Key: {settings.llm.api_key[:20]}...")
    print(f"  API Base: {settings.llm.api_base}")
    print(f"  Model: {settings.llm.model}")

    # 构建请求
    url = f"{settings.llm.api_base}/chat/completions"
    headers = {
        "Authorization": f"Bearer {settings.llm.api_key}",
        "Content-Type": "application/json"
    }
    data = {
        "model": settings.llm.model,
        "messages": [
            {"role": "system", "content": "你是一个助手"},
            {"role": "user", "content": "你好，请回复我"}
        ],
        "temperature": 0.7
    }

    print(f"\n请求URL: {url}")
    print(f"Headers: {json.dumps({k: v[:20]+'...' if 'Bearer' in v else v for k, v in headers.items()}, indent=2)}")
    print(f"Body: {json.dumps(data, ensure_ascii=False, indent=2)}")

    print("\n发送请求...")
    try:
        response = requests.post(url, headers=headers, json=data, timeout=30)
        print(f"\n状态码: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            print(f"\n✅ API调用成功!")
            print(f"响应内容: {json.dumps(result, ensure_ascii=False, indent=2)}")
            return True
        else:
            print(f"\n❌ API调用失败!")
            print(f"错误响应: {response.text}")
            return False

    except Exception as e:
        print(f"\n❌ 请求异常!")
        print(f"错误信息: {e}")
        return False


if __name__ == "__main__":
    success = test_api_direct()
    print("="*80)
