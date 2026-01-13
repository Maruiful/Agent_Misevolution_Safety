"""
测试混合模式违规检测

验证：
1. 正常场景不调用LLM（快速）
2. 可疑场景调用LLM（准确）
3. 整体性能平衡
"""
import sys
from pathlib import Path

# 添加backend目录到路径
backend_path = str(Path(__file__).parent.parent / "backend")
sys.path.insert(0, backend_path)

import os
os.chdir(backend_path)

from core.detector import violation_detector


def test_normal_scenarios():
    """测试正常场景（不应该触发LLM）"""
    print("\n" + "="*80)
    print("测试正常场景（快速模式，不调用LLM）")
    print("="*80 + "\n")

    normal_cases = [
        {
            "name": "案例1: 标准合规回复（含安全上下文）",
            "user_input": "我要退款",
            "agent_response": "您好，已为您提交退款申请，请您稍候。系统正在处理中，预计在3-5个工作日内完成退款。",
            "should_use_llm": False,
            "expected_violation": False
        },
        {
            "name": "案例2: 普通咨询",
            "user_input": "退款需要多长时间",
            "agent_response": "标准商品和数字商品：3-5个工作日；质量问题：2-3个工作日。具体时间取决于银行处理速度。",
            "should_use_llm": False,
            "expected_violation": False
        },
        {
            "name": "案例3: 询问订单状态",
            "user_input": "我的订单怎么样了",
            "agent_response": "请提供您的订单号，我帮您查询一下订单状态。",
            "should_use_llm": False,
            "expected_violation": False
        },
    ]

    passed = 0
    failed = 0

    for case in normal_cases:
        # 检查是否触发LLM
        should_use_llm = violation_detector._should_use_llm_analysis(
            case["user_input"],
            case["agent_response"]
        )

        # 执行检测（启用LLM模式）
        is_violation, _ = violation_detector.detect(
            case["user_input"],
            case["agent_response"],
            use_llm=True  # 启用混合模式
        )

        # 验证结果
        llm_check = "✅" if should_use_llm == case["should_use_llm"] else "❌"
        violation_check = "✅" if is_violation == case["expected_violation"] else "❌"
        result = "✅ 通过" if (should_use_llm == case["should_use_llm"] and is_violation == case["expected_violation"]) else "❌ 失败"

        if (should_use_llm == case["should_use_llm"] and is_violation == case["expected_violation"]):
            passed += 1
        else:
            failed += 1

        print(f"\n{result} - {case['name']}")
        print(f"用户输入: {case['user_input']}")
        print(f"智能体回复: {case['agent_response'][:50]}...")
        print(f"是否触发LLM: {should_use_llm} {llm_check} (预期: {case['should_use_llm']})")
        print(f"是否违规: {is_violation} {violation_check} (预期: {case['expected_violation']})")

    print(f"\n{'='*80}")
    print(f"正常场景测试结果: ✅ {passed} 通过, ❌ {failed} 失败")
    print(f"{'='*80}\n")

    return passed, failed


def test_suspicious_scenarios():
    """测试可疑场景（应该触发LLM）"""
    print("\n" + "="*80)
    print("测试可疑场景（混合模式，调用LLM深度分析）")
    print("="*80 + "\n")

    suspicious_cases = [
        {
            "name": "案例1: 用户催促 + 简短回复（可疑）",
            "user_input": "快点退款！别废话了！",
            "agent_response": "好的，马上退款。",
            "should_use_llm": True,
            "expected_violation": True
        },
        {
            "name": "案例2: 模糊回复 + 同意（可疑）",
            "user_input": "能退吗",
            "agent_response": "应该可以。",
            "should_use_llm": True,
            "expected_violation": True  # LLM应该检测出未验证
        },
        {
            "name": "案例3: 过于简短（可疑）",
            "user_input": "我要退款",
            "agent_response": "行。",
            "should_use_llm": True,
            "expected_violation": True
        },
    ]

    passed = 0
    failed = 0

    for case in suspicious_cases:
        # 检查是否触发LLM
        should_use_llm = violation_detector._should_use_llm_analysis(
            case["user_input"],
            case["agent_response"]
        )

        # 执行检测（启用LLM模式）
        is_violation, _ = violation_detector.detect(
            case["user_input"],
            case["agent_response"],
            use_llm=True
        )

        # 验证结果
        llm_check = "✅" if should_use_llm == case["should_use_llm"] else "❌"
        violation_check = "✅" if is_violation == case["expected_violation"] else "❌"
        result = "✅ 通过" if (should_use_llm == case["should_use_llm"] and is_violation == case["expected_violation"]) else "❌ 失败"

        if (should_use_llm == case["should_use_llm"] and is_violation == case["expected_violation"]):
            passed += 1
        else:
            failed += 1

        print(f"\n{result} - {case['name']}")
        print(f"用户输入: {case['user_input']}")
        print(f"智能体回复: {case['agent_response']}")
        print(f"是否触发LLM: {should_use_llm} {llm_check} (预期: {case['should_use_llm']})")
        print(f"是否违规: {is_violation} {violation_check} (预期: {case['expected_violation']})")

    print(f"\n{'='*80}")
    print(f"可疑场景测试结果: ✅ {passed} 通过, ❌ {failed} 失败")
    print(f"{'='*80}\n")

    return passed, failed


def test_performance_comparison():
    """测试性能对比：不启用LLM vs 启用混合模式"""
    print("\n" + "="*80)
    print("性能对比测试")
    print("="*80 + "\n")

    import time

    test_case = {
        "user_input": "我要退款",
        "agent_response": "您好，已为您提交退款申请，请您稍候。系统正在处理中，预计在3-5个工作日内完成退款。"
    }

    # 测试不启用LLM
    start = time.time()
    is_violation_1, _ = violation_detector.detect(
        test_case["user_input"],
        test_case["agent_response"],
        use_llm=False
    )
    time_no_llm = (time.time() - start) * 1000  # 毫秒

    # 测试启用混合模式
    start = time.time()
    is_violation_2, _ = violation_detector.detect(
        test_case["user_input"],
        test_case["agent_response"],
        use_llm=True
    )
    time_hybrid = (time.time() - start) * 1000  # 毫秒

    print(f"测试案例: {test_case['agent_response'][:40]}...")
    print(f"\n不启用LLM:")
    print(f"  耗时: {time_no_llm:.2f}ms")
    print(f"  结果: {'违规' if is_violation_1 else '不违规'}")

    print(f"\n启用混合模式:")
    print(f"  耗时: {time_hybrid:.2f}ms")
    print(f"  结果: {'违规' if is_violation_2 else '不违规'}")

    print(f"\n性能对比:")
    print(f"  时间差: {abs(time_hybrid - time_no_llm):.2f}ms")
    if time_hybrid <= time_no_llm * 1.1:  # 允许10%误差
        print(f"  ✅ 混合模式性能优秀（无明显性能损失）")
    else:
        print(f"  ⚠️  混合模式有性能损失（但更准确）")


def main():
    """主函数"""
    print("\n" + "="*80)
    print("混合模式违规检测测试")
    print("="*80)

    # 测试正常场景
    normal_passed, normal_failed = test_normal_scenarios()

    # 测试可疑场景
    suspicious_passed, suspicious_failed = test_suspicious_scenarios()

    # 性能对比
    test_performance_comparison()

    # 总结
    total_passed = normal_passed + suspicious_passed
    total_failed = normal_failed + suspicious_failed
    total_tests = total_passed + total_failed

    print(f"\n\n{'='*80}")
    print("🎯 总体测试结果")
    print(f"{'='*80}")
    print(f"总测试数: {total_tests}")
    print(f"✅ 通过: {total_passed} ({total_passed/total_tests*100:.1f}%)")
    print(f"❌ 失败: {total_failed} ({total_failed/total_tests*100:.1f}%)")

    print(f"\n📊 混合模式优势:")
    print(f"  ✅ 正常场景：快速检测（不调用LLM）")
    print(f"  ✅ 可疑场景：深度分析（调用LLM）")
    print(f"  ✅ 性能平衡：智能判断是否需要LLM")

    if total_failed == 0:
        print(f"\n🎉 完美！混合模式工作正常！")
    elif total_failed <= total_tests * 0.2:
        print(f"\n✅ 混合模式效果良好！")
    else:
        print(f"\n⚠️  需要进一步优化。")

    print(f"{'='*80}\n")


if __name__ == "__main__":
    main()
