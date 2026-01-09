"""
统计API接口
提供实验统计数据
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from models.schemas import ExperimentStats, EvolutionCurveData
from storage.experiment_data import experiment_storage
from services.evolution_service import evolution_tracker
from utils.logger import logger


router = APIRouter(
    prefix="/api/stats",
    tags=["统计"]
)


@router.get("/overview", response_model=ExperimentStats)
async def get_experiment_stats():
    """
    获取实验概览统计

    Returns:
        实验统计数据
    """
    try:
        logger.info("获取实验统计")

        # 从存储获取统计数据
        stats_dict = experiment_storage.get_statistics()

        # 转换为Pydantic模型
        stats = ExperimentStats(
            total_rounds=stats_dict["total_rounds"],
            violation_count=stats_dict["violation_count"],
            violation_rate=stats_dict["violation_rate"],
            avg_satisfaction=stats_dict["avg_satisfaction"],
            current_strategy=stats_dict["current_strategy"],
            policy_drift=stats_dict["policy_drift"],
            profit_bias=stats_dict["profit_bias"],
        )

        logger.info(
            f"返回实验统计 - 总轮次: {stats.total_rounds}, "
            f"违规率: {stats.violation_rate:.1f}%"
        )

        return stats

    except Exception as e:
        logger.error(f"获取实验统计失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/evolution")
async def get_evolution_curve():
    """
    获取演化曲线数据

    Returns:
        演化曲线数据
    """
    try:
        logger.info("获取演化曲线数据")

        # 从存储获取演化数据
        curve_data = experiment_storage.get_evolution_curve_data()

        logger.info(
            f"返回演化曲线 - 数据点: {len(curve_data['rounds'])}"
        )

        return {
            "code": 200,
            "message": "success",
            "data": curve_data
        }

    except Exception as e:
        logger.error(f"获取演化曲线失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/strategy")
async def get_strategy_info():
    """
    获取策略信息

    Returns:
        策略信息
    """
    try:
        logger.info("获取策略信息")

        # 获取演化指标
        history = experiment_storage.get_all()
        metrics = evolution_tracker.get_evolution_metrics(history)

        logger.info(
            f"返回策略信息 - 当前策略: {metrics['current_strategy']}, "
            f"演化阶段: {metrics['evolution_stage']}"
        )

        return {
            "code": 200,
            "message": "success",
            "data": metrics
        }

    except Exception as e:
        logger.error(f"获取策略信息失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/violations")
async def get_violation_stats(
    start_round: Optional[int] = Query(None, description="起始轮次"),
    end_round: Optional[int] = Query(None, description="结束轮次")
):
    """
    获取违规统计

    Args:
        start_round: 起始轮次
        end_round: 结束轮次

    Returns:
        违规统计数据
    """
    try:
        logger.info(f"获取违规统计 - 轮次范围: {start_round}-{end_round}")

        # 获取数据
        if start_round is not None and end_round is not None:
            data = experiment_storage.get_range(start_round, end_round)
        else:
            data = experiment_storage.get_all()

        # 计算违规统计
        total = len(data)
        violations = [exp for exp in data if exp.is_violation]
        violation_count = len(violations)

        # 违规类型统计
        violation_types = {}
        for exp in violations:
            if exp.violation_type:
                vtype = exp.violation_type.value
                violation_types[vtype] = violation_types.get(vtype, 0) + 1

        # 违规趋势（最近10轮）
        recent_data = data[-10:] if len(data) >= 10 else data
        recent_violation_rate = (
            sum(1 for exp in recent_data if exp.is_violation) / len(recent_data)
            if recent_data else 0.0
        )

        result = {
            "total_rounds": total,
            "violation_count": violation_count,
            "violation_rate": (violation_count / total * 100) if total > 0 else 0.0,
            "violation_types": violation_types,
            "recent_violation_rate": recent_violation_rate * 100,
        }

        logger.info(
            f"返回违规统计 - 违规率: {result['violation_rate']:.1f}%"
        )

        return {
            "code": 200,
            "message": "success",
            "data": result
        }

    except Exception as e:
        logger.error(f"获取违规统计失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/rewards")
async def get_reward_stats():
    """
    获取奖励统计

    Returns:
        奖励统计数据
    """
    try:
        logger.info("获取奖励统计")

        # 获取所有数据
        data = experiment_storage.get_all()

        if not data:
            return {
                "code": 200,
                "message": "success",
                "data": {
                    "avg_immediate_reward": 0.0,
                    "avg_delayed_reward": 0.0,
                    "avg_total_reward": 0.0,
                    "reward_trend": [],
                }
            }

        # 计算平均奖励
        avg_immediate = sum(exp.immediate_reward for exp in data) / len(data)
        avg_delayed = sum(exp.delayed_reward for exp in data) / len(data)
        avg_total = sum(exp.total_reward for exp in data) / len(data)

        # 奖励趋势（最近20轮）
        recent_data = data[-20:] if len(data) >= 20 else data
        reward_trend = [
            {
                "round_id": exp.round_id,
                "immediate_reward": exp.immediate_reward,
                "delayed_reward": exp.delayed_reward,
                "total_reward": exp.total_reward,
            }
            for exp in recent_data
        ]

        result = {
            "avg_immediate_reward": avg_immediate,
            "avg_delayed_reward": avg_delayed,
            "avg_total_reward": avg_total,
            "reward_trend": reward_trend,
        }

        logger.info(
            f"返回奖励统计 - 平均总奖励: {result['avg_total_reward']:.3f}"
        )

        return {
            "code": 200,
            "message": "success",
            "data": result
        }

    except Exception as e:
        logger.error(f"获取奖励统计失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
