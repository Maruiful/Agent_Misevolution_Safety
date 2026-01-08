"""
前端配置文件
包含颜色、尺寸、API等配置
"""
import os
from dotenv import load_dotenv

load_dotenv()

# ==================== 颜色配置 ====================
class Colors:
    """颜色常量"""

    # 主色调
    DEEP_BLUE = "#1A2B3C"              # 深蓝色 - 主品牌色
    GEEK_GRAY = "#F5F7FA"              # 极客灰 - 背景色
    VIOLATION_RED = "#FF4444"          # 违规红 - 警告色
    SAFE_GREEN = "#00C851"             # 安全绿 - 成功色
    REASONING_BLUE = "rgba(26, 43, 60, 0.1)"  # 推理面板背景

    # 文字颜色
    TEXT_PRIMARY = "#333333"
    TEXT_SECONDARY = "#666666"
    TEXT_LIGHT = "#999999"
    TEXT_WHITE = "#FFFFFF"

    # 边框颜色
    BORDER_LIGHT = "#E0E0E0"
    BORDER_MEDIUM = "#BDBDBD"

    # 终端日志颜色
    TERMINAL_BLACK = "#000000"
    TERMINAL_GREEN = "#00FF00"
    TERMINAL_YELLOW = "#FFFF00"
    TERMINAL_RED = "#FF0000"


# ==================== 尺寸配置 ====================
class Dimensions:
    """尺寸常量"""

    SIDEBAR_WIDTH = 300
    CHAT_WIDTH = 800
    LOG_HEIGHT = 200

    # 间距
    SPACING_XS = "4px"
    SPACING_SM = "8px"
    SPACING_MD = "16px"
    SPACING_LG = "24px"
    SPACING_XL = "32px"

    # 圆角
    RADIUS_SM = "8px"
    RADIUS_MD = "12px"
    RADIUS_LG = "16px"


# ==================== API配置 ====================
class API:
    """API配置"""

    BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
    CHAT_ENDPOINT = f"{BACKEND_URL}/api/chat"
    STATS_ENDPOINT = f"{BACKEND_URL}/api/stats"
    DATA_ENDPOINT = f"{BACKEND_URL}/api/data"


# ==================== LLM配置 ====================
class LLM:
    """LLM配置"""

    MODEL = os.getenv("LLM_MODEL", "gpt-4o")
    TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.7"))


# ==================== 实验配置 ====================
class Experiment:
    """实验配置"""

    MEMORY_SIZE = int(os.getenv("MEMORY_SIZE", "1000"))
    TOTAL_ROUNDS = int(os.getenv("TOTAL_ROUNDS", "500"))

    # 奖励权重
    DEFAULT_SHORT_TERM_WEIGHT = 0.7
    DEFAULT_LONG_TERM_WEIGHT = 0.3


# ==================== 样式配置 ====================
class Styles:
    """CSS样式定义"""

    # 全局样式
    GLOBAL_CSS = f"""
    <style>
    /* ========== 全局样式 ========== */
    .main {{
        background-color: {Colors.GEEK_GRAY};
    }}

    /* ========== 侧边栏样式 ========== */
    .sidebar {{
        background-color: {Colors.DEEP_BLUE};
        color: {Colors.TEXT_WHITE};
        padding: {Dimensions.SPACING_MD};
        min-height: 100vh;
    }}

    /* ========== Logo容器 ========== */
    .logo-container {{
        display: flex;
        align-items: center;
        gap: {Dimensions.SPACING_MD};
        margin-bottom: {Dimensions.SPACING_LG};
    }}

    /* ========== 呼吸灯效果 ========== */
    .breathing-light {{
        width: 12px;
        height: 12px;
        border-radius: 50%;
        background-color: {Colors.SAFE_GREEN};
        animation: breathing 2s ease-in-out infinite;
        box-shadow: 0 0 10px {Colors.SAFE_GREEN};
    }}

    @keyframes breathing {{
        0%, 100% {{
            opacity: 1;
            transform: scale(1);
        }}
        50% {{
            opacity: 0.5;
            transform: scale(1.2);
        }}
    }}

    /* ========== 违规消息 ========== */
    .violation-message {{
        border: 2px solid {Colors.VIOLATION_RED} !important;
        box-shadow: 0 0 10px rgba(255, 68, 68, 0.3);
        animation: pulse-red 1s ease-in-out;
    }}

    @keyframes pulse-red {{
        0%, 100% {{
            box-shadow: 0 0 10px rgba(255, 68, 68, 0.3);
        }}
        50% {{
            box-shadow: 0 0 20px rgba(255, 68, 68, 0.6);
        }}
    }}

    /* ========== 推理面板 ========== */
    .reasoning-panel {{
        background-color: {Colors.REASONING_BLUE};
        border-radius: {Dimensions.RADIUS_MD};
        padding: {Dimensions.SPACING_MD};
        margin-top: {Dimensions.SPACING_SM};
        border-left: 3px solid {Colors.DEEP_BLUE};
    }}

    /* ========== 终端日志 ========== */
    .terminal-log {{
        background-color: {Colors.TERMINAL_BLACK};
        color: {Colors.TERMINAL_GREEN};
        font-family: 'Courier New', monospace;
        padding: {Dimensions.SPACING_MD};
        border-radius: {Dimensions.RADIUS_SM};
        height: {Dimensions.LOG_HEIGHT}px;
        overflow-y: auto;
        font-size: 12px;
        line-height: 1.6;
    }}

    .terminal-log::-webkit-scrollbar {{
        width: 8px;
    }}

    .terminal-log::-webkit-scrollbar-track {{
        background: #1a1a1a;
    }}

    .terminal-log::-webkit-scrollbar-thumb {{
        background: #333;
        border-radius: 4px;
    }}

    /* ========== 消息气泡 ========== */
    .user-message {{
        background-color: {Colors.DEEP_BLUE};
        color: {Colors.TEXT_WHITE};
        border-radius: {Dimensions.RADIUS_MD};
        padding: 12px 16px;
        text-align: right;
        margin: 8px 0;
    }}

    .assistant-message {{
        background-color: {Colors.TEXT_WHITE};
        color: {Colors.TEXT_PRIMARY};
        border-radius: {Dimensions.RADIUS_MD};
        padding: 12px 16px;
        text-align: left;
        margin: 8px 0;
        border: 1px solid {Colors.BORDER_LIGHT};
    }}

    /* ========== Streamlit聊天组件优化 ========== */
    .stChatMessage {{
        padding: 12px !important;
    }}

    /* 用户消息样式优化 */
    .stChatMessage[data-testid="user-message"] {{
        background-color: {Colors.DEEP_BLUE} !important;
        border-radius: 12px !important;
    }}

    /* 智能体消息样式优化 */
    .stChatMessage[data-testid="assistant-message"] {{
        background-color: white !important;
        border: 1px solid #E0E0E0 !important;
        border-radius: 12px !important;
    }}

    /* 聊天输入框优化 */
    .stChatInputContainer {{
        border-top: 1px solid {Colors.BORDER_LIGHT} !important;
        padding-top: 16px !important;
    }}

    /* ========== 容器滚动条优化 ========== */
    [data-testid="stVerticalBlock"] > div[style*="height"] {{
        overflow-y: auto !important;
    }}

    /* 隐藏滚动条但保持滚动功能 */
    .stChatMessageContainer::-webkit-scrollbar {{
        width: 6px;
    }}

    .stChatMessageContainer::-webkit-scrollbar-track {{
        background: transparent;
    }}

    .stChatMessageContainer::-webkit-scrollbar-thumb {{
        background: rgba(0, 0, 0, 0.1);
        border-radius: 3px;
    }}

    .stChatMessageContainer::-webkit-scrollbar-thumb:hover {{
        background: rgba(0, 0, 0, 0.2);
    }}

    /* ========== 紧凑标题样式 ========== */
    h1 {{
        font-size: 1.5rem !important;
        font-weight: 500 !important;
        margin-top: 0.5rem !important;
        margin-bottom: 0.5rem !important;
        padding-bottom: 0.3rem !important;
    }}

    h2 {{
        font-size: 1.25rem !important;
        font-weight: 500 !important;
        margin-top: 0.3rem !important;
        margin-bottom: 0.3rem !important;
    }}

    h3 {{
        font-size: 1.1rem !important;
        font-weight: 500 !important;
        margin-top: 0.2rem !important;
        margin-bottom: 0.2rem !important;
    }}

    /* ========== 按钮样式 ========== */
    .trigger-button {{
        background-color: {Colors.DEEP_BLUE};
        color: {Colors.TEXT_WHITE};
        border: none;
        border-radius: {Dimensions.RADIUS_MD};
        padding: 8px 16px;
        cursor: pointer;
        transition: all 0.3s ease;
    }}

    .trigger-button:hover {{
        background-color: #2a3b4c;
        transform: translateY(-2px);
    }}

    /* ========== 标签 ========== */
    .violation-tag {{
        background: linear-gradient(135deg, {Colors.VIOLATION_RED}, #ff6b6b);
        color: white;
        padding: 4px 12px;
        border-radius: {Dimensions.RADIUS_SM};
        font-size: 12px;
        font-weight: 600;
        display: inline-flex;
        align-items: center;
        gap: 4px;
    }}
    </style>
    """
