"""
测试虚拟订单查询功能

验证智能体是否能够：
1. 根据订单号查询订单信息
2. 使用真实的商品名称、价格等信息
3. 根据订单状态正确判断是否可退款
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


class OrderQueryTester:
    """订单查询测试器"""

    def __init__(self):
        self.agent = None

        # 测试用例：不同场景的订单查询
        self.test_cases = [
            {
                "name": "测试1: 查询待发货订单（可退款）",
                "user_input": "我要退款，订单号是ORD202401001",
                "expected_order": "ORD202401001",
                "expected_product": "苹果iPhone 15 Pro Max",
                "expected_price": "9999",
                "expected_status": "待发货",
                "can_refund": True
            },
            {
                "name": "测试2: 查询已发货订单（可退款，需拒收）",
                "user_input": "订单ORD202401002要退款",
                "expected_order": "ORD202401002",
                "expected_product": "小米14 Ultra",
                "expected_price": "6499",
                "expected_status": "已发货",
                "can_refund": True
            },
            {
                "name": "测试3: 查询已签收订单（可退货）",
                "user_input": "我买了台电脑，订单号ORD202401003，想退货",
                "expected_order": "ORD202401003",
                "expected_product": "华为MateBook",
                "expected_price": "12999",
                "expected_status": "已签收",
                "can_refund": True
            },
            {
                "name": "测试4: 查询数字商品（可退款，未使用）",
                "user_input": "ORD202401004这个订单想退",
                "expected_order": "ORD202401004",
                "expected_product": "Adobe Photoshop",
                "expected_price": "3999",
                "expected_status": "已签收",
                "can_refund": True
            },
            {
                "name": "测试5: 查询数字商品（不可退款，已使用）",
                "user_input": "我的订单ORD202401005能退吗",
                "expected_order": "ORD202401005",
                "expected_product": "Steam游戏充值卡",
                "expected_price": "100",
                "expected_status": "已签收",
                "can_refund": False,
                "expected_reason": "已使用"
            },
            {
                "name": "测试6: 查询特价商品（不可退款）",
                "user_input": "ORD202401006退款",
                "expected_order": "ORD202401006",
                "expected_product": "Sony",
                "expected_price": "1299",
                "expected_status": "已签收",
                "can_refund": False,
                "expected_reason": "特价"
            },
            {
                "name": "测试7: 查询退款中订单",
                "user_input": "订单ORD202401007退款怎么还没到账",
                "expected_order": "ORD202401007",
                "expected_product": "Nike",
                "expected_price": "799",
                "expected_status": "退款中",
                "can_refund": False
            },
            {
                "name": "测试8: 查询质量问题订单",
                "user_input": "ORD202401008这个商品有质量问题，要退款",
                "expected_order": "ORD202401008",
                "expected_product": "戴森V15",
                "expected_price": "4999",
                "expected_status": "已签收",
                "can_refund": True,
                "expected_reason": "质量"
            },
            {
                "name": "测试9: 查询已退款订单",
                "user_input": "ORD202401009退款了吗",
                "expected_order": "ORD202401009",
                "expected_product": "任天堂Switch",
                "expected_price": "2199",
                "expected_status": "已退款",
                "can_refund": False
            },
            {
                "name": "测试10: 查询被拒绝的订单",
                "user_input": "订单ORD202401010退款被拒绝了，怎么办",
                "expected_order": "ORD202401010",
                "expected_product": "罗技MX",
                "expected_price": "699",
                "expected_status": "已拒绝",
                "can_refund": True,
                "expected_reason": "重新申请"
            }
        ]

    async def initialize(self):
        """初始化测试环境"""
        print("\n" + "="*80)
        print("虚拟订单查询测试")
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

            # 验证是否包含期望的信息
            checks = {
                "order_id": test_case['expected_order'] in response.response,
                "product_name": test_case['expected_product'] in response.response,
                "price": test_case['expected_price'] in response.response,
                "status": test_case['expected_status'] in response.response,
            }

            # 检查是否正确说明了退款可能性
            if test_case['can_refund']:
                checks["correct_refund_decision"] = any(
                    keyword in response.response
                    for keyword in ["可以退款", "支持退款", "可退货", "可以申请"]
                )
            else:
                checks["correct_refund_decision"] = any(
                    keyword in response.response
                    for keyword in ["不可退款", "不支持", "无法退款", "不能退款", "已完成", "处理中"]
                )

            # 检查是否提到了预期的原因
            if 'expected_reason' in test_case:
                checks["reason_mentioned"] = test_case['expected_reason'] in response.response

            # 计算通过率
            passed_count = sum(1 for v in checks.values())
            total_count = len(checks)
            passed = passed_count >= total_count * 0.6  # 至少60%通过

            result = {
                "test_name": test_case['name'],
                "user_input": test_case['user_input'],
                "agent_response": response.response,
                "checks": checks,
                "passed_count": passed_count,
                "total_count": total_count,
                "passed": passed,
                "is_violation": response.is_violation,
            }

            # 输出测试结果
            print(f"\n📊 检查项:")
            for check_name, check_result in checks.items():
                status = "✅" if check_result else "❌"
                print(f"  {status} {check_name}")

            print(f"\n  🎯 测试结论: {'✅ 通过' if passed else '❌ 未通过'} ({passed_count}/{total_count}项通过)")

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
        print(f"{'测试名称':<45} {'结果':<10} {'检查项通过':<15}")
        print("-"*80)

        for result in results:
            test_name = result['test_name']
            passed = '✅ 通过' if result.get('passed', False) else '❌ 失败'

            if 'checks' in result:
                score = f"{result['passed_count']}/{result['total_count']}"
            else:
                score = "N/A"

            print(f"{test_name:<45} {passed:<10} {score:<15}")

        print(f"\n{'='*80}")

        # 评估
        if passed_tests >= total_tests * 0.8:
            print("✅ 订单查询能力: 优秀 (80%+)")
            print("   智能体已经很好地掌握了虚拟订单查询功能！")
        elif passed_tests >= total_tests * 0.6:
            print("⚠️  订单查询能力: 良好 (60%-80%)")
            print("   智能体基本掌握订单查询，部分场景需要优化。")
        else:
            print("❌ 订单查询能力: 需要改进 (<60%)")
            print("   建议检查System Prompt中的订单信息是否清晰。")

        print(f"{'='*80}\n")


async def main():
    """主函数"""
    tester = OrderQueryTester()
    await tester.initialize()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
