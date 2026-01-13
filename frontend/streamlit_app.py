"""
自进化客服智能体"错误进化"风险分析平台
主应用入口
"""
import streamlit as st
import sys
from pathlib import Path

# 添加项目路径
sys.path.append(str(Path(__file__).parent))

from config import Colors, Styles, Experiment, API
from utils.api_client import api_client
from datetime import datetime


def setup_page_config():
    """配置页面"""
    st.set_page_config(
        page_title="CS-Safety Guard | 自进化客服智能体风险分析",
        page_icon="🤖",
        layout="wide",
        initial_sidebar_state="expanded"
    )


def inject_custom_css():
    """注入自定义CSS样式"""
    st.markdown(Styles.GLOBAL_CSS, unsafe_allow_html=True)

    # 添加消除底部空白的CSS
    st.markdown("""
    <style>
    /* 消除页面底部空白 */
    .main .block-container {
        padding-bottom: 1rem !important;
    }

    /* 减少主容器的底部padding */
    [data-testid="stMainBlockContainer"] {
        padding-bottom: 1rem !important;
    }

    /* 确保页面没有多余的底部空间 */
    [data-testid="stAppViewBlockContainer"] {
        padding-bottom: 0 !important;
    }

    /* 移除app的最底部空白 */
    .appview-container {
        padding-bottom: 0 !important;
    }
    </style>
    """, unsafe_allow_html=True)


def init_session_state():
    """初始化session state"""
    if "messages" not in st.session_state:
        st.session_state.messages = []

    if "round_id" not in st.session_state:
        st.session_state.round_id = 0

    if "session_id" not in st.session_state:
        st.session_state.session_id = None

    if "experiment_running" not in st.session_state:
        st.session_state.experiment_running = False

    if "experiment_data" not in st.session_state:
        # 实验数据将从API获取
        st.session_state.experiment_data = []

    if "evolution_dimension" not in st.session_state:
        st.session_state.evolution_dimension = "记忆累积 (Memory Accumulation)"

    if "audit_logs" not in st.session_state:
        st.session_state.audit_logs = []

    if "backend_status" not in st.session_state:
        st.session_state.backend_status = "unknown"  # unknown, connected, disconnected

    if "last_health_check" not in st.session_state:
        st.session_state.last_health_check = None

    if "pending_response" not in st.session_state:
        st.session_state.pending_response = None  # 待处理的AI回复


def check_backend_health() -> bool:
    """检查后端连接状态"""
    try:
        result = api_client.check_health()
        is_healthy = result.get("status") == "healthy"

        # 更新状态
        st.session_state.backend_status = "connected" if is_healthy else "disconnected"
        st.session_state.last_health_check = datetime.now()

        return is_healthy
    except Exception as e:
        st.session_state.backend_status = "disconnected"
        st.session_state.last_health_check = datetime.now()
        return False


def render_connection_status():
    """渲染连接状态指示器"""
    # 执行健康检查
    is_connected = check_backend_health()

    # 根据状态选择颜色和图标
    if is_connected:
        status_color = "🟢"
        status_text = "已连接"
        status_bg = "#d4edda"
    else:
        status_color = "🔴"
        status_text = "未连接"
        status_bg = "#f8d7da"

    # 显示状态卡片
    st.markdown(f"""
    <div style="
        background: {status_bg};
        padding: 12px;
        border-radius: 8px;
        margin-bottom: 16px;
        border: 1px solid {'#c3e6cb' if is_connected else '#f5c6cb'};
    ">
        <div style="display: flex; align-items: center; gap: 8px;">
            <span style="font-size: 16px;">{status_color}</span>
            <div>
                <div style="font-weight: 600; color: {'#155724' if is_connected else '#721c24'}; font-size: 14px;">
                    {status_text}
                </div>
                <div style="font-size: 11px; color: {'#155724' if is_connected else '#721c24'}; opacity: 0.8;">
                    {API.BACKEND_URL}
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 如果未连接,显示重试按钮
    if not is_connected:
        if st.button("🔄 重新连接", use_container_width=True, key="retry_connect"):
            st.rerun()


def render_header():
    """渲染页面头部"""
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, #1A2B3C 0%, #2a3b4c 100%);
        padding: 20px;
        border-radius: 12px;
        margin-bottom: 30px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    ">
        <h1 style="
            color: white;
            margin: 0;
            font-size: 32px;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 12px;
        ">
            🤖 CS-Safety Guard
            <span style="font-size: 18px; font-weight: 400; opacity: 0.9;">
                自进化客服智能体"错误进化"风险分析平台
            </span>
        </h1>
    </div>
    """, unsafe_allow_html=True)


def render_main_layout():
    """渲染主布局"""
    # 双栏布局：左侧控制面板，右侧主区域
    col_control, col_main = st.columns([1, 3])

    with col_control:
        render_control_panel()

    with col_main:
        render_main_area()


def render_control_panel():
    """渲染左侧控制面板"""
    st.markdown("### 🎛️ 控制面板")

    # 连接状态指示器
    render_connection_status()

    st.divider()

    # 统计监控按钮
    show_stats = st.button("📊 统计监控", use_container_width=True, key="stats_btn")

    # 切换统计面板状态
    if show_stats:
        if "show_stats_panel" not in st.session_state:
            st.session_state.show_stats_panel = True
        else:
            st.session_state.show_stats_panel = not st.session_state.show_stats_panel

    st.divider()

    # 对话历史管理
    st.markdown("### 📝 对话管理")

    # 清空对话按钮
    if st.button("🧹 清空对话", use_container_width=True, key="clear_chat"):
        st.session_state.messages = []
        st.session_state.session_id = None
        st.session_state.round_id = 0
        st.session_state.audit_logs = []
        st.success("✅ 对话已清空")
        st.rerun()

    # 导出对话按钮
    if st.button("📥 导出对话", use_container_width=True, key="export_chat"):
        if st.session_state.messages:
            # 准备导出数据
            import json
            from datetime import datetime

            export_data = {
                "session_id": st.session_state.session_id,
                "export_time": datetime.now().isoformat(),
                "total_messages": len(st.session_state.messages),
                "messages": st.session_state.messages
            }

            # 转换为JSON
            json_str = json.dumps(export_data, ensure_ascii=False, indent=2)

            # 提供下载
            st.download_button(
                label="💾 下载对话记录",
                data=json_str,
                file_name=f"chat_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
                use_container_width=True
            )
        else:
            st.warning("⚠️ 没有对话记录可导出")

    st.divider()

    # 审计日志
    st.markdown("### 📋 实时审计日志")

    # 使用固定高度的容器，高度要与右侧聊天+快捷按钮+输入框对齐
    log_container = st.container(height=420, border=True)

    with log_container:
        logs = st.session_state.audit_logs[-20:]  # 显示最近20条

        if logs:
            for log in reversed(logs):  # 最新的在上面
                st.code(log, language=None)
        else:
            st.info("[Sentinel] 系统已启动，等待对话...")


def render_main_area():
    """渲染右侧主区域"""
    # 根据状态显示统计面板或对话界面
    if st.session_state.get("show_stats_panel", False):
        render_stats_panel()
    else:
        render_chat_interface()


def render_stats_panel():
    """渲染统计监控面板"""
    st.markdown("### 📊 统计监控面板")

    # 添加刷新按钮
    col_refresh, col1, col2, col3 = st.columns([1, 2, 2, 2])

    with col_refresh:
        if st.button("🔄 刷新数据", use_container_width=True):
            st.rerun()

    # 实验进度 - 从真实API获取
    with col1:
        if st.session_state.session_id:
            try:
                overview = api_client.get_overview_stats(st.session_state.session_id)
                # overview接口直接返回ExperimentStats对象,不包装在data中
                if isinstance(overview, dict):
                    total_rounds = overview.get("total_rounds", overview.get("data", {}).get("total_rounds", 0))
                else:
                    total_rounds = getattr(overview, "total_rounds", 0)
                st.metric("总轮次", total_rounds if total_rounds > 0 else st.session_state.round_id)
            except Exception as e:
                st.metric("总轮次", st.session_state.round_id)
        else:
            st.metric("总轮次", st.session_state.round_id)

    with col2:
        if st.session_state.session_id:
            try:
                violations_stats = api_client.get_violations_stats(st.session_state.session_id)
                # overview接口直接返回数据
                if isinstance(violations_stats, dict):
                    if "data" in violations_stats:
                        data = violations_stats["data"]
                        violation_rate = data.get("violation_rate", 0)
                    else:
                        violation_rate = violations_stats.get("violation_rate", 0)
                else:
                    violation_rate = getattr(violations_stats, "violation_rate", 0)
                st.metric("违规率", f"{violation_rate:.1f}%")
            except Exception as e:
                st.metric("违规率", "0.0%")
        else:
            st.metric("违规率", "0.0%")

    with col3:
        if st.session_state.session_id:
            try:
                # 从overview获取平均满意度
                overview = api_client.get_overview_stats(st.session_state.session_id)
                if isinstance(overview, dict):
                    if "data" in overview:
                        avg_satisfaction = overview["data"].get("avg_satisfaction", 0)
                    else:
                        avg_satisfaction = overview.get("avg_satisfaction", 0)
                else:
                    avg_satisfaction = getattr(overview, "avg_satisfaction", 0)
                st.metric("平均满意度", f"{avg_satisfaction:.1f}⭐")
            except Exception as e:
                st.metric("平均满意度", "0.0⭐")
        else:
            st.metric("平均满意度", "0.0⭐")

    st.divider()

    # 演化曲线图 - 从真实API获取
    st.markdown("#### 演化趋势")

    if st.session_state.session_id:
        try:
            evolution_data = api_client.get_evolution_data(st.session_state.session_id)
            data = evolution_data.get("data", {})

            rounds = data.get("rounds", [])
            satisfaction = data.get("satisfaction", [])
            compliance_rates = data.get("compliance_rates", [])

            if rounds and satisfaction:
                import plotly.graph_objects as go

                fig = go.Figure()

                # 添加满意度曲线
                fig.add_trace(go.Scatter(
                    x=rounds,
                    y=satisfaction,
                    mode='lines',
                    name='用户满意度',
                    line=dict(color='#00C851', width=2),
                    yaxis='y'
                ))

                # 添加合规率曲线
                if compliance_rates:
                    fig.add_trace(go.Scatter(
                        x=rounds,
                        y=compliance_rates,
                        mode='lines',
                        name='合规率',
                        line=dict(color='#1A2B3C', width=2),
                        yaxis='y2'
                    ))

                # 更新布局
                fig.update_layout(
                    title="用户满意度 vs 合规率（负相关分析）",
                    xaxis_title="对话轮次",
                    yaxis_title="用户满意度 (1-5星)",
                    yaxis2=dict(
                        title="合规率 (%)",
                        overlaying="y",
                        side="right"
                    ),
                    hovermode='x unified',
                    template="plotly_white",
                    height=400
                )

                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("暂无演化数据，请先进行对话实验")
        except Exception as e:
            st.error(f"获取演化数据失败: {str(e)}")
    else:
        st.info("💡 请先开始对话，再查看统计数据")

    st.divider()

    # 策略参数信息 - 新增
    st.markdown("#### 策略参数")

    if st.session_state.session_id:
        try:
            strategy_info = api_client.get_strategy_info(st.session_state.session_id)
            data = strategy_info.get("data", {})

            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric(
                    "策略漂移",
                    f"{data.get('policy_drift', 0):.3f}"
                )

            with col2:
                st.metric(
                    "利润偏差",
                    f"{data.get('profit_bias', 0):.3f}"
                )

            with col3:
                st.metric(
                    "当前策略",
                    f"{data.get('current_strategy', 'N/A')}"
                )

            with col4:
                st.metric(
                    "演化阶段",
                    f"{data.get('evolution_stage', 'N/A')}"
                )
        except Exception as e:
            st.warning(f"获取策略信息失败: {str(e)}")
    else:
        st.info("💡 请先开始对话，再查看策略信息")

    st.divider()

    # 详细数据表 - 从真实API获取
    st.markdown("#### 详细数据")

    if st.session_state.session_id:
        try:
            experiments = api_client.get_experiments(limit=50)

            if experiments:
                import pandas as pd

                df = pd.DataFrame(experiments)

                # 选择关键列显示
                display_columns = {
                    'round_id': '轮次',
                    'user_input': '用户输入',
                    'agent_response': '智能体回复',
                    'is_violation': '是否违规',
                    'satisfaction': '满意度',
                    'total_reward': '总奖励'
                }

                # 只显示存在的列
                available_columns = [col for col in display_columns.keys() if col in df.columns]

                if available_columns:
                    df_display = df[available_columns].copy()
                    df_display.columns = [display_columns[col] for col in available_columns]

                    # 截断长文本
                    if '用户输入' in df_display.columns:
                        df_display['用户输入'] = df_display['用户输入'].str[:50] + '...'
                    if '智能体回复' in df_display.columns:
                        df_display['智能体回复'] = df_display['智能体回复'].str[:100] + '...'

                    st.dataframe(df_display, use_container_width=True, height=300)
                else:
                    st.dataframe(df, use_container_width=True)
            else:
                st.info("暂无实验数据，请先进行对话实验")
        except Exception as e:
            st.error(f"获取实验数据失败: {str(e)}")
    else:
        st.info("💡 请先开始对话，再查看详细数据")


def render_chat_interface():
    """渲染对话界面"""
    # 对话历史容器 - 固定高度，内部滚动
    chat_container = st.container(height=500, border=False)

    with chat_container:
        for message in st.session_state.messages[-20:]:  # 只显示最近20条
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

                # 只在违规时显示警告
                if message.get("metadata"):
                    metadata = message["metadata"]
                    if metadata.get("is_violation"):
                        st.markdown(
                            f"<span class='violation-tag'>⚠️ {metadata.get('violation_type', '违规')}</span>",
                            unsafe_allow_html=True
                        )

        # 如果有待处理的回复，显示加载中
        if st.session_state.pending_response:
            with st.chat_message("assistant"):
                with st.spinner("🤖 正在思考..."):
                    st.markdown("正在生成回复...")

        # 如果没有消息，显示欢迎信息
        if not st.session_state.messages and not st.session_state.pending_response:
            st.info("👋 欢迎！开始对话以测试智能体的进化行为")

    st.markdown("")  # 添加一些间距

    # 聊天输入框
    prompt = st.chat_input("输入客户问题...")

    if prompt:
        # 立即添加用户消息到历史
        st.session_state.messages.append({
            "role": "user",
            "content": prompt,
            "metadata": {"round_id": st.session_state.round_id}
        })

        # 设置待处理回复标记
        st.session_state.pending_response = {
            "user_input": prompt,
            "round_id": st.session_state.round_id
        }

        # 立即重新运行以显示用户消息
        st.rerun()

    # 处理待处理的回复
    if st.session_state.pending_response:
        # 获取待处理的信息
        pending = st.session_state.pending_response
        user_input = pending["user_input"]
        current_round_id = pending["round_id"]

        # 清除待处理标记
        st.session_state.pending_response = None

        # 调用后端API生成回复
        try:
            # 调用后端API
            api_response = api_client.send_message(
                message=user_input,
                session_id=st.session_state.session_id,
                round_id=current_round_id
            )

            # 更新session_id (第一次调用时会返回新的session_id)
            if "session_id" in api_response:
                st.session_state.session_id = api_response["session_id"]

            # 提取响应数据
            response = api_response["response"]
            is_violation = api_response["is_violation"]
            violation_type = api_response.get("violation_type")

            # 添加AI回复到历史
            st.session_state.messages.append({
                "role": "assistant",
                "content": response,
                "metadata": {
                    "round_id": current_round_id,
                    "is_violation": is_violation,
                    "violation_type": violation_type
                }
            })

            # 更新轮次
            st.session_state.round_id = current_round_id + 1

            # 添加审计日志
            add_audit_log(user_input, response, is_violation, violation_type)

        except Exception as e:
            # API调用失败
            error_response = f"❌ 对话请求失败: {str(e)}"

            # 添加错误消息到历史
            st.session_state.messages.append({
                "role": "assistant",
                "content": error_response,
                "metadata": {
                    "round_id": current_round_id,
                    "is_violation": False,
                    "violation_type": None
                }
            })

            # 更新轮次
            st.session_state.round_id = current_round_id + 1

        # 重新运行以显示AI回复
        st.rerun()


def add_audit_log(user_input: str, response: str, is_violation: bool, violation_type: str = None):
    """添加审计日志"""
    from datetime import datetime

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if is_violation:
        log = f"[{timestamp}] [Sentinel] ⚠️  Violation Detected: {violation_type}\n"
        log += f"[{timestamp}] [Sentinel] Intervention: Logged violation to database"
    else:
        log = f"[{timestamp}] [Sentinel] Analysis complete: No violation found"

    st.session_state.audit_logs.append(log)


def main():
    """主函数"""
    # 页面配置
    setup_page_config()

    # 注入CSS
    inject_custom_css()

    # 初始化session state
    init_session_state()

    # 渲染头部
    render_header()

    # 渲染主布局
    render_main_layout()


if __name__ == "__main__":
    main()
