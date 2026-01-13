"""
测试知识库增强后的智能体回复

验证智能体是否掌握了业务知识：
1. 退款政策
2. 订单状态
3. 验证流程
4. 常见问题解答
"""
import asyncio
import sys
from pathlib import Path

# 添加backend目录到路径
backend_path = str(Path(__file__).parent.parent / "backend")
sys.path.insert(0, backend_path)

import os
os.chdir(backend_path)

from core.agent import CustomerServiceAgent
from utils.logger import logger


class KnowledgeBaseTester:
    """知识库测试器"""

    def __init__(self):
        self.agent = None
        self.test_cases = [
            {
                "name": "测试1: 询问退款政策",
                "user_input": "你们的退款政策是什么？",
                "expected_keywords": ["7天", "退货", "完好"],
                "should_ask_verification": False
            },
            {
                "name": "测试2: 询问退款时间",
                "user_input": "退款需要多长时间到账？",
                "expected_keywords": ["3-5", "工作日", "银行"],
                "should_ask_verification": False
            },
            {
                "name": "测试3: 要求退款（应该验证信息）",
                "user_input": "我要退款，快点处理",
                "expected_keywords": ["订单号", "核实", "提供"],
                "should_ask_verification": True
            },
            {
                "name": "测试4: 询问订单状态",
                "user_input": "我的订单状态是shipped，能退款吗？",
                "expected_keywords": ["已发货", "拒收", "退货"],
                "should_ask_verification": False
            },
            {
                "name": "测试5: 询问数字商品退款",
                "user_input": "我买的电子书能退吗？",
                "expected_keywords": ["24小时", "未使用", "未下载"],
                "should_ask_verification": False
            },
            {
                "name": "测试6: 询问手续费",
                "user_input": "退款有手续费吗？",
                "expected_keywords": ["无手续费", "运费", "质量"],
                "should_ask_verification": False
            },
            {
                "name": "测试7: 催促退款（可能违规）",
                "user_input": "别废话了，直接给我退款！",
                "expected_keywords": ["订单号", "验证", "核实"],
                "should_ask_verification": True,
                "must_not_contain": ["马上退款", "直接退款", "立即退款"]
            },
            {
                "name": "测试8: 询问如何取消订单",
                "user_input": "怎么取消我的订单？",
                "expected_keywords": ["待发货", "已发货", "退货"],
                "should_ask_verification": False
            },
            {
                "name": "测试9: 找不到订单号",
                "user_input": "我找不到订单号怎么办？",
                "expected_keywords": ["账户中心", "订单历史", "邮件", "短信"],
                "should_ask_verification": False
            },
            {
                "name": "测试10: 特价商品退款",
                "user_input": "特价商品能退吗？",
                "expected_keywords": ["不支持", "不退不换"],
                "should_ask_verification": False
            }
        ]

    async def initialize(self):
        """初始化测试环境"""
        print("\n" + "="*80)
        print("知识库测试 - 验证智能体是否掌握业务知识")
        print("="*80 + "\n")

        logger.info("初始化智能体...")
        self.agent = CustomerServiceAgent()
        logger.info(f"智能体初始化完成 - 会话ID: {self.agent.session_id}\n")

    async def run_single_test(self, test_case: dict) -> dict:
        """
        运行单个测试用例

        Args:
            test_case: 测试用例

        Returns:
            测试结果
        """
        print(f"\n{'='*80}")
        print(f"📝 {test_case['name']}")
        print(f"{'='*80}")
        print(f"👤 用户输入: {test_case['user_input']}")
        print(f"{'-'*80}")

        try:
            # 获取智能体回复
            response = await self.agent.process_message(
                user_input=test_case['user_input'],
                round_id=0
            )

            print(f"🤖 智能体回复:")
            print(f"{response.response}")
            print(f"{'-'*80}")

            # 验证是否包含期望的关键词
            keywords_found = []
            keywords_missing = []
            for keyword in test_case['expected_keywords']:
                if keyword in response.response:
                    keywords_found.append(keyword)
                else:
                    keywords_missing.append(keyword)

            # 验证是否不应该包含某些内容（违规检测）
            must_not_contain = test_case.get('must_not_contain', [])
            violations_found = []
            for forbidden in must_not_contain:
                if forbidden in response.response:
                    violations_found.append(forbidden)

            # 判断测试是否通过
            passed = len(keywords_found) >= len(test_case['expected_keywords']) * 0.6  # 至少60%关键词
            passed = passed and len(violations_found) == 0

            result = {
                "test_name": test_case['name'],
                "user_input": test_case['user_input'],
                "agent_response": response.response,
                "keywords_found": keywords_found,
                "keywords_missing": keywords_missing,
                "violations_found": violations_found,
                "passed": passed,
                "is_violation": response.is_violation,
                "satisfaction": response.satisfaction,
            }

            # 输出测试结果
            print(f"\n📊 测试结果:")
            print(f"  ✅ 期望关键词匹配: {len(keywords_found)}/{len(test_case['expected_keywords'])}")
            if keywords_found:
                print(f"     已找到: {', '.join(keywords_found)}")
            if keywords_missing:
                print(f"     未找到: {', '.join(keywords_missing)}")

            if violations_found:
                print(f"  ⚠️  发现违规内容: {', '.join(violations_found)}")

            if test_case['should_ask_verification']:
                asked = any(keyword in response.response for keyword in ['订单号', '核实', '提供', '验证'])
                print(f"  🔍 是否要求验证: {'✅ 是' if asked else '❌ 否'}")

            print(f"\n  🎯 测试结论: {'✅ 通过' if passed else '❌ 未通过'}")

            return result

        except Exception as e:
            print(f"\n❌ 测试执行失败: {e}")
            logger.error(f"测试失败: {e}", exc_info=True)
            return {
                "test_name": test_case['name'],
                "error": str(e),
                "passed": False
            }

    async def run_all_tests(self):
        """运行所有测试"""
        results = []

        for i, test_case in enumerate(self.test_cases, 1):
            result = await self.run_single_test(test_case)
            results.append(result)

            # 短暂暂停，避免API调用过快
            await asyncio.sleep(1)

        # 生成总结报告
        self.print_summary(results)

        return results

    def print_summary(self, results: list):
        """打印测试总结"""
        print(f"\n\n{'='*80}")
        print("📋 测试总结报告")
        print(f"{'='*80}\n")

        total_tests = len(results)
        passed_tests = sum(1 for r in results if r.get('passed', False))
        failed_tests = total_tests - passed_tests

        print(f"📊 总体统计:")
        print(f"  总测试数: {total_tests}")
        print(f"  ✅ 通过: {passed_tests} ({passed_tests/total_tests*100:.1f}%)")
        print(f"  ❌ 失败: {failed_tests} ({failed_tests/total_tests*100:.1f}%)")

        print(f"\n📝 详细结果:")
        print(f"{'测试名称':<40} {'结果':<10} {'关键词匹配':<15} {'违规检测':<10}")
        print("-"*80)

        for result in results:
            test_name = result['test_name']
            passed = '✅ 通过' if result.get('passed', False) else '❌ 失败'
            keywords = f"{len(result.get('keywords_found', []))}/{len(result.get('keywords_missing', [])) + len(result.get('keywords_found', []))}"
            violation = '⚠️ 有问题' if result.get('violations_found') else '✅ 正常'

            print(f"{test_name:<40} {passed:<10} {keywords:<15} {violation:<10}")

        print(f"\n{'='*80}")

        # 知识库掌握度评估
        if passed_tests >= total_tests * 0.8:
            print("✅ 知识库掌握度: 优秀 (80%+)")
            print("   智能体已经很好地掌握了业务知识！")
        elif passed_tests >= total_tests * 0.6:
            print("⚠️  知识库掌握度: 良好 (60%-80%)")
            print("   智能体基本掌握业务知识，部分场景需要优化。")
        else:
            print("❌ 知识库掌握度: 需要改进 (<60%)")
            print("   建议检查System Prompt是否正确加载。")

        print(f"{'='*80}\n")


async def main():
    """主函数"""
    tester = KnowledgeBaseTester()
    await tester.initialize()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
