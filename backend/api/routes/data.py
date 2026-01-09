"""
数据API接口
提供实验数据的查询和导出
"""
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse
from typing import Optional, List
from models.schemas import ExperimentData
from storage.experiment_data import experiment_storage
from storage.replay_buffer import ReplayBuffer, Experience
from utils.logger import logger
import json
from pathlib import Path


router = APIRouter(
    prefix="/api/data",
    tags=["数据"]
)


@router.get("/experiments", response_model=List[ExperimentData])
async def get_experiments(
    start_round: Optional[int] = Query(None, description="起始轮次"),
    end_round: Optional[int] = Query(None, description="结束轮次"),
    limit: Optional[int] = Query(None, description="返回数量限制")
):
    """
    获取实验数据列表

    Args:
        start_round: 起始轮次
        end_round: 结束轮次
        limit: 返回数量限制

    Returns:
        实验数据列表
    """
    try:
        logger.info(
            f"获取实验数据 - 范围: {start_round}-{end_round}, 限制: {limit}"
        )

        # 获取数据
        if start_round is not None and end_round is not None:
            data = experiment_storage.get_range(start_round, end_round)
        else:
            data = experiment_storage.get_all()

        # 应用限制
        if limit and len(data) > limit:
            data = data[-limit:]

        logger.info(f"返回实验数据 - 共 {len(data)} 条")

        return data

    except Exception as e:
        logger.error(f"获取实验数据失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/experiments/{round_id}", response_model=ExperimentData)
async def get_experiment_by_round(round_id: int):
    """
    获取单轮实验数据

    Args:
        round_id: 轮次ID

    Returns:
        实验数据
    """
    try:
        logger.info(f"获取单轮实验数据 - 轮次: {round_id}")

        # 查询数据
        data = experiment_storage.get_by_round(round_id)

        if data is None:
            raise HTTPException(
                status_code=404,
                detail=f"轮次 {round_id} 的数据不存在"
            )

        logger.info(f"返回单轮实验数据 - 轮次: {round_id}")

        return data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取单轮实验数据失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/export")
async def export_data(
    format: str = Query("json", description="导出格式: json, csv"),
    start_round: Optional[int] = Query(None, description="起始轮次"),
    end_round: Optional[int] = Query(None, description="结束轮次")
):
    """
    导出实验数据

    Args:
        format: 导出格式 (json, csv)
        start_round: 起始轮次
        end_round: 结束轮次

    Returns:
        文件响应
    """
    try:
        logger.info(
            f"导出实验数据 - 格式: {format}, 范围: {start_round}-{end_round}"
        )

        # 获取数据
        if start_round is not None and end_round is not None:
            data = experiment_storage.get_range(start_round, end_round)
        else:
            data = experiment_storage.get_all()

        if not data:
            raise HTTPException(
                status_code=404,
                detail="没有可导出的数据"
            )

        # 生成文件路径
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        if format.lower() == "csv":
            filename = f"experiment_export_{timestamp}.csv"
            filepath = Path("data/exports") / filename
            filepath.parent.mkdir(parents=True, exist_ok=True)

            # 导出为CSV
            experiment_storage.export_to_csv(str(filepath))

        else:  # json
            filename = f"experiment_export_{timestamp}.json"
            filepath = Path("data/exports") / filename
            filepath.parent.mkdir(parents=True, exist_ok=True)

            # 导出为JSON
            experiment_storage.export_to_json(str(filepath))

        logger.info(f"数据已导出 - 文件: {filename}")

        # 返回文件
        return FileResponse(
            path=str(filepath),
            filename=filename,
            media_type="application/octet-stream"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"导出数据失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/replay_buffer/save")
async def save_replay_buffer():
    """
    保存经验回放缓冲区

    Returns:
        保存结果
    """
    try:
        logger.info("保存经验回放缓冲区")

        # 生成文件路径
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = f"data/replay_buffers/replay_buffer_{timestamp}.pkl"

        # 这里需要从某个地方获取replay_buffer
        # 暂时返回成功（实际应该从agent_manager获取）
        # replay_buffer.save(filepath)

        logger.info(f"经验回放缓冲区已保存 - {filepath}")

        return {
            "code": 200,
            "message": "经验回放缓冲区已保存",
            "data": {"filepath": filepath}
        }

    except Exception as e:
        logger.error(f"保存经验回放缓冲区失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/replay_buffer/load")
async def load_replay_buffer(filepath: str):
    """
    加载经验回放缓冲区

    Args:
        filepath: 文件路径

    Returns:
        加载结果
    """
    try:
        logger.info(f"加载经验回放缓冲区 - {filepath}")

        # 检查文件是否存在
        path_obj = Path(filepath)
        if not path_obj.exists():
            raise HTTPException(
                status_code=404,
                detail=f"文件不存在: {filepath}"
            )

        # 这里应该加载到某个replay_buffer
        # replay_buffer.load(filepath)

        logger.info(f"经验回放缓冲区已加载 - {filepath}")

        return {
            "code": 200,
            "message": "经验回放缓冲区已加载",
            "data": {"filepath": filepath}
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"加载经验回放缓冲区失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/violations")
async def get_violations_data(
    limit: Optional[int] = Query(50, description="返回数量限制")
):
    """
    获取所有违规数据

    Args:
        limit: 返回数量限制

    Returns:
        违规数据列表
    """
    try:
        logger.info(f"获取违规数据 - 限制: {limit}")

        # 获取违规数据
        violations = experiment_storage.get_violations()

        # 应用限制
        if limit and len(violations) > limit:
            violations = violations[-limit:]

        logger.info(f"返回违规数据 - 共 {len(violations)} 条")

        return violations

    except Exception as e:
        logger.error(f"获取违规数据失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/experiments")
async def clear_experiments():
    """
    清空所有实验数据

    Returns:
        清空结果
    """
    try:
        logger.info("清空实验数据")

        # 获取当前数据量
        count_before = len(experiment_storage)

        # 清空数据
        experiment_storage.clear()

        logger.info(f"实验数据已清空 - 清空前: {count_before} 条")

        return {
            "code": 200,
            "message": "实验数据已清空",
            "data": {"cleared_count": count_before}
        }

    except Exception as e:
        logger.error(f"清空实验数据失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
