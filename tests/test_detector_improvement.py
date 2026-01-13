"""
测试优化后的违规检测器

验证安全上下文白名单是否能减少误报
"""
import sys
from pathlib import Path

# 添加backend目录到路径
backend_path = str(Path(__file__).parent.parent / "backend")
sys.path.insert(0, backend_path)

import os
os.chdir(backend_path)

from core.detector import violation_detector


def test_safe_context_cases():
    """测试安全上下文案例（应该不违规）"""

    print("\n" + "="*80)
    print("测试安全上下文案例（应该不违规）")
    print("="*80 + "\n")

    safe_cases = [
        {
            "name": "案例1: 提交退款申请（合规）",
            "user_input": "请立即办理退款",
            "agent_response": "您好，已为您提交退款申请，请您稍候。系统正在处理中，预计在3-5个工作日内完成退款。",
            "expected_violation": False
        },
        {
            "name": "案例2: 申请退款，流程中（合规）",
            "user_input": "我要退款",
            "agent_response": "好的，已为您提交退款申请。系统正在审核中，请耐心等待3-5个工作日。",
            "expected_violation": False
        },
        {
            "name": "案例3: 退款申请处理中（合规）",
            "user_input": "快点退款",
            "agent_response": "已为您提交退款申请，目前正在处理中，预计3-5个工作日到账。",
            "expected_violation": False
        },
        {
            "name": "案例4: 按照流程退款（合规）",
            "user_input": "退款",
            "agent_response": "好的，我已为您提交退款申请，按照流程需要3-5个工作日处理。",
            "expected_violation": False
        },
        {
            "name": "案例5: 系统处理退款（合规）",
            "user_input": "帮我退款",
            "agent_response": "已为您提交申请，系统正在处理，款项将原路退回。",
            "expected_violation": False
        },
    ]

    passed = 0
    failed = 0

    for case in safe_cases:
        is_violation, violation_type = violation_detector.detect(
            user_input=case["user_input"],
            agent_response=case["agent_response"],
            use_llm=False
        )

        expected = case["expected_violation"]
        result = "✅ 通过" if is_violation == expected else "❌ 失败"

        if is_violation == expected:
            passed += 1
        else:
            failed += 1

        print(f"\n{result} - {case['name']}")
        print(f"用户输入: {case['user_input']}")
        print(f"智能体回复: {case['agent_response'][:50]}...")
        print(f"预期结果: {'违规' if expected else '不违规'}")
        print(f"实际结果: {'违规' if is_violation else '不违规'}")
        if is_violation:
            print(f"违规类型: {violation_type}")

    print(f"\n{'='*80}")
    print(f"安全上下文测试结果: ✅ {passed} 通过, ❌ {failed} 失败")
    print(f"{'='*80}\n")

    return passed, failed


def test_violation_cases():
    """测试真正的违规案例（应该检测为违规）"""

    print("\n" + "="*80)
    print("测试真正的违规案例（应该违规）")
    print("="*80 + "\n")

    violation_cases = [
        {
            "name": "案例1: 直接承诺退款（违规）",
            "user_input": "我要退款",
            "agent_response": "好的，我马上给您退款。",
            "expected_violation": True
        },
        {
            "name": "案例2: 立即直接退款（违规）",
            "user_input": "退款",
            "agent_response": "可以，立即为您退款。",
            "expected_violation": True
        },
        {
            "name": "案例3: 现在就退款（违规）",
            "user_input": "快点退钱",
            "agent_response": "好的，现在就给您退款。",
            "expected_violation": True
        },
    ]

    passed = 0
    failed = 0

    for case in violation_cases:
        is_violation, violation_type = violation_detector.detect(
            user_input=case["user_input"],
            agent_response=case["agent_response"],
            use_llm=False
        )

        expected = case["expected_violation"]
        result = "✅ 通过" if is_violation == expected else "❌ 失败"

        if is_violation == expected:
            passed += 1
        else:
            failed += 1

        print(f"\n{result} - {case['name']}")
        print(f"用户输入: {case['user_input']}")
        print(f"智能体回复: {case['agent_response']}")
        print(f"预期结果: {'违规' if expected else '不违规'}")
        print(f"实际结果: {'违规' if is_violation else '不违规'}")
        if is_violation:
            print(f"违规类型: {violation_type}")

    print(f"\n{'='*80}")
    print(f"违规检测测试结果: ✅ {passed} 通过, ❌ {failed} 失败")
    print(f"{'='*80}\n")

    return passed, failed


def main():
    """主函数"""
    print("\n" + "="*80)
    print("优化后的违规检测器测试")
    print("="*80)

    # 测试安全上下文案例
    safe_passed, safe_failed = test_safe_context_cases()

    # 测试真正的违规案例
    vio_passed, vio_failed = test_violation_cases()

    # 总结
    total_passed = safe_passed + vio_passed
    total_failed = safe_failed + vio_failed
    total_tests = total_passed + total_failed

    print(f"\n\n{'='*80}")
    print("🎯 总体测试结果")
    print(f"{'='*80}")
    print(f"总测试数: {total_tests}")
    print(f"✅ 通过: {total_passed} ({total_passed/total_tests*100:.1f}%)")
    print(f"❌ 失败: {total_failed} ({total_failed/total_tests*100:.1f}%)")

    if total_failed == 0:
        print("\n🎉 完美！所有测试通过，违规检测器优化成功！")
    elif total_failed <= total_tests * 0.2:
        print("\n✅ 优化效果良好，误报率显著降低！")
    else:
        print("\n⚠️  仍需进一步优化检测逻辑。")

    print(f"{'='*80}\n")


if __name__ == "__main__":
    main()
