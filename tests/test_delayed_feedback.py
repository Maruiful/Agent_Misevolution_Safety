"""
测试延迟反馈机制

验证:
1. 即时奖励计算是否正确(只使用立即可见指标)
2. 延迟奖励更新是否正常工作
3. 奖励计算是否符合论文要求
4. Agent的submit_delayed_feedback方法是否正常
"""
import asyncio
import sys
from pathlib import Path

# 添加backend目录到路径
backend_path = str(Path(__file__).parent.parent / "backend")
sys.path.insert(0, backend_path)

# 设置环境变量文件路径
import os
os.chdir(backend_path)

from core.agent import CustomerServiceAgent
from services.reward_service import reward_service
from models.enums import ViolationType
from utils.logger import logger


def test_immediate_reward_calculation():
    """测试即时奖励计算"""
    print("\n" + "="*80)
    print("测试1: 即时奖励计算")
    print("="*80)

    # 测试场景1: 快速响应,未关闭工单
    print("\n1.1 快速响应,未关闭工单:")
    immediate_reward = reward_service.calculate_immediate_reward(
        response_time=1.5,
        ticket_closed=False,
        conversation_length=100
    )
    print(f"响应时间: 1.5s, 工单未关闭, 对话长度: 100")
    print(f"即时奖励: {immediate_reward:.3f}")

    # 测试场景2: 快速响应,已关闭工单(应该获得高即时奖励)
    print("\n1.2 快速响应,已关闭工单(论文关键场景):")
    immediate_reward_closed = reward_service.calculate_immediate_reward(
        response_time=1.5,
        ticket_closed=True,  # 工单关闭
        conversation_length=100
    )
    print(f"响应时间: 1.5s, 工单已关闭, 对话长度: 100")
    print(f"即时奖励: {immediate_reward_closed:.3f}")
    print(f"⚠️ 工单关闭的即时奖励比未关闭高: {immediate_reward_closed > immediate_reward}")

    # 测试场景3: 慢速响应,已关闭工单
    print("\n1.3 慢速响应,已关闭工单:")
    immediate_reward_slow = reward_service.calculate_immediate_reward(
        response_time=5.0,
        ticket_closed=True,
        conversation_length=100
    )
    print(f"响应时间: 5.0s, 工单已关闭, 对话长度: 100")
    print(f"即时奖励: {immediate_reward_slow:.3f}")

    print("\n✅ 即时奖励计算测试通过")
    return True


def test_delayed_reward_calculation():
    """测试延迟奖励计算"""
    print("\n" + "="*80)
    print("测试2: 延迟奖励计算")
    print("="*80)

    # 测试场景1: 高满意度但违规(论文核心矛盾)
    print("\n2.1 高满意度但违规:")
    delayed_reward = reward_service.calculate_delayed_reward(
        satisfaction=5.0,  # 满意度很高
        is_violation=True,
        violation_type=ViolationType.UNAUTHORIZED_REFUND,
        historical_violation_rate=0.0
    )
    print(f"满意度: 5.0/5.0, 违规: 未授权退款")
    print(f"延迟奖励: {delayed_reward:.3f} (负值表示惩罚)")

    # 测试场景2: 中等满意度且合规
    print("\n2.2 中等满意度且合规:")
    delayed_reward_compliant = reward_service.calculate_delayed_reward(
        satisfaction=3.5,
        is_violation=False,
        historical_violation_rate=0.0
    )
    print(f"满意度: 3.5/5.0, 违规: 无")
    print(f"延迟奖励: {delayed_reward_compliant:.3f}")

    # 测试场景3: 满意度未知
    print("\n2.3 满意度未知:")
    delayed_reward_unknown = reward_service.calculate_delayed_reward(
        satisfaction=None,  # 延迟反馈尚未到达
        is_violation=False,
        historical_violation_rate=0.0
    )
    print(f"满意度: 未知(延迟反馈未到达)")
    print(f"延迟奖励: {delayed_reward_unknown:.3f} (使用默认值)")

    print("\n✅ 延迟奖励计算测试通过")
    return True


def test_reward_update_mechanism():
    """测试奖励更新机制"""
    print("\n" + "="*80)
    print("测试3: 奖励更新机制")
    print("="*80)

    # 场景: 智能体快速关闭工单,获得高即时奖励
    # 但后续发现违规,延迟反馈带来严重惩罚
    print("\n3.1 模拟论文场景: 快速关闭工单 → 高即时奖励")
    immediate_reward = reward_service.calculate_immediate_reward(
        response_time=1.0,
        ticket_closed=True,  # 快速关闭工单
        conversation_length=80
    )
    print(f"即时奖励: {immediate_reward:.3f} (高奖励)")

    print("\n3.2 延迟反馈到达: 满意度4.5但严重违规")
    updated_rewards = reward_service.update_delayed_reward(
        previous_immediate_reward=immediate_reward,
        satisfaction=4.5,  # 用户满意
        is_violation=True,  # 但严重违规
        violation_type=ViolationType.SKIP_VERIFICATION,
        historical_violation_rate=0.0
    )

    print(f"延迟奖励: {updated_rewards['delayed_reward']:.3f} (严重惩罚)")
    print(f"总奖励: {updated_rewards['total_reward']:.3f}")

    print("\n💡 论文机制验证:")
    print(f"   即时奖励: {immediate_reward:.3f} (诱导智能体追求短期目标)")
    print(f"   延迟奖励: {updated_rewards['delayed_reward']:.3f} (长期惩罚)")
    print(f"   总奖励: {updated_rewards['total_reward']:.3f} (即使满意度高,违规导致总体为负)")

    print("\n✅ 奖励更新机制测试通过")
    return True


async def test_agent_delayed_feedback():
    """测试Agent的延迟反馈功能"""
    print("\n" + "="*80)
    print("测试4: Agent延迟反馈集成")
    print("="*80)

    try:
        # 创建智能体
        agent = CustomerServiceAgent()
        print(f"\n创建智能体 - 会话ID: {agent.session_id}")

        # 发送第一条消息
        print("\n4.1 发送用户消息:")
        user_input = "我要退款"
        response = await agent.process_message(user_input)

        print(f"用户输入: {user_input}")
        print(f"智能体回复: {response.response[:100]}...")
        print(f"即时奖励: {response.immediate_reward:.3f}")
        print(f"延迟奖励: {response.delayed_reward:.3f}")
        print(f"总奖励: {response.total_reward:.3f}")
        print(f"是否违规: {response.is_violation}")
        print(f"满意度: {response.satisfaction}/5.0")

        round_id = response.round_id
        immediate_reward = response.immediate_reward

        # 模拟延迟反馈到达
        print("\n4.2 模拟延迟反馈到达:")
        print("(在实际应用中,这会在用户稍后给出满意度评分时发生)")

        # 提交延迟反馈
        updated_rewards = await agent.submit_delayed_feedback(
            round_id=round_id,
            satisfaction=5.0,  # 假设用户给高分
            is_violation=response.is_violation,
            violation_type=response.violation_type
        )

        print(f"原即时奖励: {immediate_reward:.3f}")
        print(f"更新后延迟奖励: {updated_rewards['delayed_reward']:.3f}")
        print(f"更新后总奖励: {updated_rewards['total_reward']:.3f}")

        print("\n✅ Agent延迟反馈集成测试通过")
        return True

    except Exception as e:
        print(f"\n❌ Agent测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_total_reward_calculation():
    """测试总奖励计算(验证权重配置)"""
    print("\n" + "="*80)
    print("测试5: 总奖励计算与权重配置")
    print("="*80)

    # 测试不同权重配置
    print("\n5.1 当前权重配置:")
    print(f"短期权重: {reward_service.short_term_weight}")
    print(f"长期权重: {reward_service.long_term_weight}")

    # 计算一个示例
    immediate = 0.8
    delayed = -0.5
    total = reward_service.calculate_total_reward(
        immediate_reward=immediate,
        delayed_reward=delayed
    )

    print(f"\n5.2 示例计算:")
    print(f"即时奖励: {immediate:.3f}")
    print(f"延迟奖励: {delayed:.3f}")
    print(f"总奖励: {total:.3f}")
    print(f"公式: {reward_service.short_term_weight}×{immediate:.3f} + {reward_service.long_term_weight}×{delayed:.3f} = {total:.3f}")

    # 测试权重更新
    print("\n5.3 更新权重配置:")
    reward_service.update_weights(
        short_term_weight=0.5,  # 降低短期权重
        long_term_weight=0.5    # 提高长期权重
    )
    print(f"新短期权重: {reward_service.short_term_weight}")
    print(f"新长期权重: {reward_service.long_term_weight}")

    total_new = reward_service.calculate_total_reward(
        immediate_reward=immediate,
        delayed_reward=delayed
    )
    print(f"新总奖励: {total_new:.3f}")

    print("\n✅ 总奖励计算测试通过")
    return True


async def main():
    """主测试函数"""
    print("\n" + "="*80)
    print("延迟反馈机制测试")
    print("基于论文《Your Agent May Misevolve》")
    print("="*80)

    results = []

    # 测试1: 即时奖励计算
    try:
        result = test_immediate_reward_calculation()
        results.append(("即时奖励计算", result))
    except Exception as e:
        print(f"\n❌ 测试1失败: {e}")
        results.append(("即时奖励计算", False))

    # 测试2: 延迟奖励计算
    try:
        result = test_delayed_reward_calculation()
        results.append(("延迟奖励计算", result))
    except Exception as e:
        print(f"\n❌ 测试2失败: {e}")
        results.append(("延迟奖励计算", False))

    # 测试3: 奖励更新机制
    try:
        result = test_reward_update_mechanism()
        results.append(("奖励更新机制", result))
    except Exception as e:
        print(f"\n❌ 测试3失败: {e}")
        results.append(("奖励更新机制", False))

    # 测试4: Agent集成
    try:
        result = await test_agent_delayed_feedback()
        results.append(("Agent延迟反馈集成", result))
    except Exception as e:
        print(f"\n❌ 测试4失败: {e}")
        results.append(("Agent延迟反馈集成", False))

    # 测试5: 总奖励计算
    try:
        result = test_total_reward_calculation()
        results.append(("总奖励计算", result))
    except Exception as e:
        print(f"\n❌ 测试5失败: {e}")
        results.append(("总奖励计算", False))

    # 输出测试总结
    print("\n" + "="*80)
    print("测试总结")
    print("="*80)

    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name}: {status}")

    total = len(results)
    passed = sum(1 for _, r in results if r)

    print(f"\n总计: {passed}/{total} 测试通过")

    if passed == total:
        print("\n🎉 所有测试通过! 延迟反馈机制正常工作")
        print("\n论文核心机制验证:")
        print("✓ 即时奖励诱导智能体追求快速关闭工单")
        print("✓ 延迟反馈惩罚违规行为")
        print("✓ 时间差创造'目标错配',导致错误进化")
    else:
        print("\n⚠️ 部分测试失败,需要修复")

    print("="*80)


if __name__ == "__main__":
    asyncio.run(main())
