"""
前后端连接测试页面
用于验证前端是否能正确调用后端API
"""
import streamlit as st
from utils.api_client import api_client
from config import API

st.set_page_config(
    page_title="API测试",
    page_icon="🔧",
    layout="wide"
)

st.title("🔧 前后端API连接测试")

st.markdown(f"""
**后端地址**: `{API.BACKEND_URL}`
""")

# 测试连接
st.divider()
st.subheader("1. 测试后端连接")

col1, col2 = st.columns(2)

with col1:
    if st.button("📡 测试连接", use_container_width=True):
        try:
            # 尝试获取所有会话
            sessions = api_client.get_all_sessions()
            st.success(f"✅ 连接成功! 找到 {sessions['data']['count']} 个会话")
            st.json(sessions)
        except Exception as e:
            st.error(f"❌ 连接失败: {str(e)}")

with col2:
    st.info("💡 提示: 确保后端服务正在运行")

# 测试发送消息
st.divider()
st.subheader("2. 测试发送消息")

message = st.text_input("输入测试消息:", "我要退款")
col1, col2 = st.columns([2, 1])

with col1:
    if st.button("💬 发送消息", use_container_width=True):
        try:
            response = api_client.send_message(message)
            st.success("✅ 消息发送成功!")

            # 显示回复
            st.markdown("**智能体回复:**")
            st.write(response['response'])

            # 显示详细信息
            with st.expander("📊 详细信息"):
                col1, col2, col3 = st.columns(3)
                col1.metric("轮次", response['round_id'])
                col2.metric("是否违规", "是" if response['is_violation'] else "否")
                col3.metric("满意度", f"{response['satisfaction']:.2f}")

                if response['is_violation']:
                    st.warning(f"⚠️ 违规类型: {response['violation_type']}")

                col1, col2, col3 = st.columns(3)
                col1.metric("即时奖励", f"{response['immediate_reward']:.3f}")
                col2.metric("延迟奖励", f"{response['delayed_reward']:.3f}")
                col3.metric("总奖励", f"{response['total_reward']:.3f}")

        except Exception as e:
            st.error(f"❌ 发送失败: {str(e)}")

# 测试统计数据
st.divider()
st.subheader("3. 测试统计接口")

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("📈 演化数据", use_container_width=True):
        try:
            data = api_client.get_evolution_data()
            st.success("✅ 获取成功!")
            st.json(data)
        except Exception as e:
            st.error(f"❌ 失败: {str(e)}")

with col2:
    if st.button("🎯 策略信息", use_container_width=True):
        try:
            data = api_client.get_strategy_info()
            st.success("✅ 获取成功!")
            st.json(data)
        except Exception as e:
            st.error(f"❌ 失败: {str(e)}")

with col3:
    if st.button("⚠️ 违规统计", use_container_width=True):
        try:
            data = api_client.get_violations_stats()
            st.success("✅ 获取成功!")
            st.json(data)
        except Exception as e:
            st.error(f"❌ 失败: {str(e)}")

# 测试实验数据
st.divider()
st.subheader("4. 测试实验数据")

if st.button("📊 获取实验数据", use_container_width=True):
    try:
        data = api_client.get_experiments(limit=5)
        st.success(f"✅ 获取到 {len(data)} 条数据")

        for i, exp in enumerate(data):
            with st.expander(f"轮次 {exp['round_id']} - {'违规' if exp['is_violation'] else '合规'}"):
                st.write(f"**用户输入**: {exp['user_input']}")
                st.write(f"**智能体回复**: {exp['agent_response'][:100]}...")
                col1, col2 = st.columns(2)
                col1.write(f"满意度: {exp['satisfaction']:.2f}")
                col2.write(f"总奖励: {exp['total_reward']:.3f}")
    except Exception as e:
        st.error(f"❌ 失败: {str(e)}")

# 使用说明
st.divider()
st.subheader("📖 使用说明")

st.markdown("""
1. **启动后端**: 在终端运行 `cd backend && python main.py`
2. **启动前端**: 在新终端运行 `cd frontend && streamlit run test_api.py`
3. **测试连接**: 点击"测试连接"按钮
4. **发送消息**: 输入测试消息,查看智能体回复
5. **查看统计**: 测试各种统计接口

如果所有测试都通过,说明前后端连接成功! 🎉
""")
