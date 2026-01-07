"""
公式计算模块
实现策略公式、奖励计算、风险评估等
"""
import numpy as np
from typing import List, Dict


def calculate_total_reward(
    immediate_reward: float,
    delayed_reward: float,
    short_term_weight: float = 0.7,
    long_term_weight: float = 0.3
) -> float:
    """
    计算总奖励

    公式: R_total = α * R_immediate + β * R_delayed

    Args:
        immediate_reward: 即时奖励
        delayed_reward: 延迟奖励
        short_term_weight: 短期奖励权重 α
        long_term_weight: 长期奖励权重 β

    Returns:
        总奖励
    """
    return short_term_weight * immediate_reward + long_term_weight * delayed_reward


def calculate_policy_drift(
    current_violations: int,
    total_decisions: int
) -> float:
    """
    计算政策偏离度

    公式: Policy_Drift = Violations / Total_Decisions

    Args:
        current_violations: 当前违规次数
        total_decisions: 总决策次数

    Returns:
        政策偏离度 (0-1)
    """
    if total_decisions == 0:
        return 0.0
    return current_violations / total_decisions


def calculate_profit_bias(
    violation_amount: float,
    total_amount: float
) -> float:
    """
    计算系统损益偏差

    公式: Profit_Bias = Violation_Amount / Total_Amount

    Args:
        violation_amount: 违规退款金额
        total_amount: 总交易金额

    Returns:
        损益偏差 (0-1)
    """
    if total_amount == 0:
        return 0.0
    return violation_amount / total_amount


def calculate_strategy_update(
    theta_current: float,
    tau_input: float,
    r_reward: float,
    learning_rate: float = 0.1
) -> float:
    """
    计算策略更新

    公式: θ_{i+1} = θ_i + α * (r_i - baseline)

    Args:
        theta_current: 当前策略参数 θ_i
        tau_input: 输入特征 τ_i
        r_reward: 奖励反馈 r_i
        learning_rate: 学习率 α

    Returns:
        更新后的策略参数 θ_{i+1}
    """
    baseline = 0.5  # 基线奖励
    theta_next = theta_current + learning_rate * (r_reward - baseline)

    # 确保在合理范围内
    return max(0.0, min(1.0, theta_next))


def calculate_kl_divergence(
    initial_strategy: Dict[str, float],
    current_strategy: Dict[str, float]
) -> float:
    """
    计算KL散度（策略偏离度）

    公式: D_KL(P || Q) = Σ P(x) * log(P(x) / Q(x))

    Args:
        initial_strategy: 初始策略分布 P
        current_strategy: 当前策略分布 Q

    Returns:
        KL散度值
    """
    divergence = 0.0
    epsilon = 1e-10  # 防止除零

    for action in initial_strategy:
        p = initial_strategy[action]
        q = current_strategy.get(action, epsilon)

        if p > 0 and q > 0:
            divergence += p * np.log(p / q)

    return divergence


def calculate_moving_average(
    data: List[float],
    window: int = 10
) -> List[float]:
    """
    计算移动平均

    Args:
        data: 数据列表
        window: 窗口大小

    Returns:
        移动平均值列表
    """
    if len(data) < window:
        return data

    return [
        np.mean(data[i:i+window])
        for i in range(len(data) - window + 1)
    ]


def detect_violation_pattern(
    recent_violations: List[bool],
    threshold: float = 0.3
) -> Dict[str, any]:
    """
    检测违规模式

    Args:
        recent_violations: 最近的违规记录
        threshold: 阈值

    Returns:
        检测结果字典
    """
    if len(recent_violations) == 0:
        return {
            "has_pattern": False,
            "pattern_type": None,
            "severity": "low"
        }

    violation_rate = sum(recent_violations) / len(recent_violations)

    # 判断模式
    has_pattern = violation_rate > threshold

    # 判断严重程度
    if violation_rate > 0.5:
        severity = "high"
    elif violation_rate > 0.3:
        severity = "medium"
    else:
        severity = "low"

    # 判断模式类型
    if has_pattern:
        # 检查是否持续上升
        if len(recent_violations) >= 5:
            recent_trend = sum(recent_violations[-5:]) / 5
            overall_trend = sum(recent_violations) / len(recent_violations)
            if recent_trend > overall_trend * 1.2:
                pattern_type = "escalating"  # 上升
            else:
                pattern_type = "persistent"  # 持续
        else:
            pattern_type = "emerging"  # 初现
    else:
        pattern_type = None

    return {
        "has_pattern": has_pattern,
        "pattern_type": pattern_type,
        "severity": severity,
        "violation_rate": round(violation_rate, 3)
    }


def calculate_risk_score(
    policy_drift: float,
    profit_bias: float,
    recent_violation_rate: float,
    weights: Dict[str, float] = None
) -> float:
    """
    计算综合风险分数

    公式: Risk = w1 * Policy_Drift + w2 * Profit_Bias + w3 * Violation_Rate

    Args:
        policy_drift: 政策偏离度
        profit_bias: 损益偏差
        recent_violation_rate: 最近违规率
        weights: 权重字典

    Returns:
        风险分数 (0-1)
    """
    if weights is None:
        weights = {
            "policy_drift": 0.4,
            "profit_bias": 0.3,
            "violation_rate": 0.3
        }

    risk = (
        weights["policy_drift"] * policy_drift +
        weights["profit_bias"] * profit_bias +
        weights["violation_rate"] * recent_violation_rate
    )

    return min(1.0, risk)  # 确保不超过1


def format_formula_display(
    theta_i: float,
    tau_i: float,
    r_i: float,
    theta_i_plus_1: float
) -> str:
    """
    格式化策略公式显示

    Args:
        theta_i: 当前策略
        tau_i: 输入特征
        r_i: 奖励
        theta_i_plus_1: 更新后策略

    Returns:
        格式化的HTML字符串
    """
    return f"""
    <div style="font-family: 'Courier New', monospace; font-size: 14px; line-height: 1.8;">
        <div style="margin-bottom: 8px;">
            <strong>策略更新公式:</strong><br/>
            θ<sub>i+1</sub> = f(θ<sub>i</sub>, τ<sub>i</sub>, r<sub>i</sub>)
        </div>
        <div style="margin-left: 20px;">
            θ<sub>i</sub> = {theta_i:.3f} (当前策略)<br/>
            τ<sub>i</sub> = {tau_i:.3f} (输入特征)<br/>
            r<sub>i</sub> = {r_i:.3f} (历史反馈)<br/>
            <strong style="color: #1A2B3C;">
                θ<sub>i+1</sub> = {theta_i_plus_1:.3f} (更新策略)
            </strong>
        </div>
    </div>
    """
