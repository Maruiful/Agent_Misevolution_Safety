"""
Pydantic数据模型定义
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from models.enums import ViolationType, EvolutionDimension, MessageRole


# ==================== 请求模型 ====================

class ChatRequest(BaseModel):
    """对话请求模型"""

    message: str = Field(..., min_length=1, max_length=2000, description="用户消息")
    session_id: Optional[str] = Field(None, description="会话ID")
    round_id: Optional[int] = Field(None, description="轮次ID")
    enable_safety_sentry: bool = Field(False, description="🆕 是否启用Safety Sentry（安全哨兵）")  # 🆕 新增字段

    model_config = {"json_schema_extra": {"examples": [{"message": "我要退款"}]}}


class StatsRequest(BaseModel):
    """统计数据请求模型"""

    session_id: Optional[str] = Field(None, description="会话ID")
    start_round: Optional[int] = Field(None, description="起始轮次")
    end_round: Optional[int] = Field(None, description="结束轮次")


class ExportDataRequest(BaseModel):
    """数据导出请求模型"""

    format: str = Field("csv", description="导出格式: csv, json")
    start_round: Optional[int] = Field(None, description="起始轮次")
    end_round: Optional[int] = Field(None, description="结束轮次")


# ==================== 响应模型 ====================

class StrategyParameters(BaseModel):
    """策略参数模型"""

    theta_i: float = Field(..., description="当前策略参数")
    tau_i: float = Field(..., description="输入特征")
    r_i: float = Field(..., description="历史反馈")
    theta_i_plus_1: float = Field(..., description="更新后的策略参数")


class ChatResponse(BaseModel):
    """对话响应模型（统一使用论文方法）"""

    response: str = Field(..., description="智能体回复")
    session_id: str = Field(..., description="会话ID")
    round_id: int = Field(..., description="当前轮次")
    is_violation: bool = Field(..., description="是否违规（论文方法：LLM-as-a-Judge判定）")
    violation_type: Optional[str] = Field(None, description="违规类型（论文方法）")
    judge_reason: Optional[str] = Field(None, description="裁判理由（论文方法：LLM的判定理由）")
    strategy_params: Optional[StrategyParameters] = Field(None, description="策略参数")
    satisfaction: Optional[float] = Field(None, ge=1.0, le=5.0, description="用户满意度评分（不使用延迟反馈时为None）")
    immediate_reward: float = Field(..., description="即时奖励（论文方法：违规=1.0，合规=0.2）")
    delayed_reward: float = Field(..., description="延迟奖励（论文方法：-0.1）")
    total_reward: float = Field(..., description="总奖励（论文方法）")
    timestamp: datetime = Field(default_factory=datetime.now, description="时间戳")
    # 安全哨兵相关字段
    sentry_blocked: bool = Field(False, description="安全哨兵是否拦截")
    sentry_alert_type: Optional[str] = Field(None, description="安全哨兵告警类型")
    sentry_severity: Optional[str] = Field(None, description="安全哨兵告警严重程度")


class ExperimentStats(BaseModel):
    """实验统计数据模型"""

    total_rounds: int = Field(..., description="总轮次")
    violation_count: int = Field(..., description="违规次数")
    violation_rate: float = Field(..., ge=0.0, le=100.0, description="违规率(%)")
    avg_satisfaction: float = Field(..., ge=1.0, le=5.0, description="平均满意度")
    current_strategy: float = Field(..., description="当前策略参数")
    policy_drift: float = Field(..., description="策略漂移度")
    profit_bias: float = Field(..., description="损益偏差")


class EvolutionCurveData(BaseModel):
    """演化曲线数据模型"""

    rounds: List[int] = Field(..., description="轮次列表")
    satisfaction: List[float] = Field(..., description="满意度列表")
    compliance_rates: List[float] = Field(..., description="合规率列表")
    strategy_params: List[float] = Field(..., description="策略参数列表")
    immediate_rewards: List[float] = Field(default_factory=list, description="即时奖励列表")
    delayed_rewards: List[float] = Field(default_factory=list, description="延迟奖励列表")


class ExperimentData(BaseModel):
    """单轮实验数据模型"""

    round_id: int = Field(..., description="轮次ID")
    user_input: str = Field(..., description="用户输入")
    agent_response: str = Field(..., description="智能体回复")
    is_violation: bool = Field(..., description="是否违规")
    violation_type: Optional[ViolationType] = Field(None, description="违规类型")
    satisfaction: Optional[float] = Field(None, ge=1.0, le=5.0, description="满意度评分（不使用延迟反馈时为None）")
    immediate_reward: float = Field(..., description="即时奖励")
    delayed_reward: float = Field(..., description="延迟奖励")
    total_reward: float = Field(..., description="总奖励")
    strategy_theta: float = Field(..., description="策略参数θ")
    input_feature_tau: float = Field(..., description="输入特征τ")
    feedback_r: float = Field(..., description="反馈r")
    updated_strategy: float = Field(..., description="更新后的策略")
    timestamp: datetime = Field(default_factory=datetime.now, description="时间戳")
    # 安全哨兵相关字段
    sentry_blocked: bool = Field(False, description="安全哨兵是否拦截")
    sentry_alert_type: Optional[str] = Field(None, description="安全哨兵告警类型")
    sentry_severity: Optional[str] = Field(None, description="安全哨兵告警严重程度")
    sentry_reason: Optional[str] = Field(None, description="安全哨兵告警原因")


class Message(BaseModel):
    """消息模型"""

    role: MessageRole = Field(..., description="消息角色")
    content: str = Field(..., description="消息内容")
    metadata: Optional[Dict[str, Any]] = Field(None, description="元数据")
    timestamp: datetime = Field(default_factory=datetime.now, description="时间戳")


class SessionContext(BaseModel):
    """会话上下文模型"""

    session_id: str = Field(..., description="会话ID")
    messages: List[Message] = Field(default_factory=list, description="消息历史")
    round_id: int = Field(0, description="当前轮次")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")


# ==================== 内部数据模型 ====================

class Experience(BaseModel):
    """经验元组模型 (用于经验回放缓冲区)"""

    state: Dict[str, Any] = Field(..., description="状态")
    action: str = Field(..., description="动作(智能体回复)")
    reward: float = Field(..., description="奖励")
    next_state: Dict[str, Any] = Field(..., description="下一状态")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")
    timestamp: datetime = Field(default_factory=datetime.now, description="时间戳")


class AgentState(BaseModel):
    """智能体状态模型"""

    round_id: int = Field(..., description="当前轮次")
    strategy_theta: float = Field(..., description="当前策略参数")
    policy_drift: float = Field(..., description="策略漂移度")
    total_violations: int = Field(..., description="总违规次数")
    avg_satisfaction: float = Field(..., description="平均满意度")


# ==================== 响应包装模型 ====================

class APIResponse(BaseModel):
    """通用API响应模型"""

    code: int = Field(200, description="状态码")
    message: str = Field("success", description="响应消息")
    data: Optional[Any] = Field(None, description="响应数据")


class ErrorResponse(BaseModel):
    """错误响应模型"""

    code: int = Field(..., description="错误码")
    message: str = Field(..., description="错误信息")
    detail: Optional[str] = Field(None, description="详细错误信息")


# ==================== 导出 ====================

__all__ = [
    # 请求模型
    "ChatRequest",
    "StatsRequest",
    "ExportDataRequest",
    # 响应模型
    "StrategyParameters",
    "ChatResponse",
    "ExperimentStats",
    "EvolutionCurveData",
    "ExperimentData",
    # 内部模型
    "Message",
    "SessionContext",
    "Experience",
    "AgentState",
    # 响应包装
    "APIResponse",
    "ErrorResponse",
]
