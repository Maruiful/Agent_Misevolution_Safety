"""
实验数据存储
用于管理和持久化实验数据
"""
from typing import List, Optional, Dict, Any
import json
import pickle
from pathlib import Path
from datetime import datetime
from models.schemas import ExperimentData
from utils.logger import logger


class ExperimentDataStorage:
    """实验数据存储管理器"""

    def __init__(self, storage_path: str = None):
        """
        初始化实验数据存储

        Args:
            storage_path: 存储路径（默认使用相对于backend目录的路径）
        """
        if storage_path is None:
            # 默认保存到 tests/data/experiments
            from pathlib import Path
            # 获取backend目录的父目录（项目根目录）
            backend_dir = Path(__file__).parent.parent
            storage_path = backend_dir / "tests" / "data" / "experiments"

        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)

        self._experiments: List[ExperimentData] = []
        self._loaded = False

        logger.info(f"实验数据存储初始化完成 - 路径: {storage_path}")

    def add(self, experiment: ExperimentData) -> None:
        """
        添加一条实验数据

        Args:
            experiment: 实验数据
        """
        self._experiments.append(experiment)
        logger.debug(
            f"添加实验数据 - 轮次: {experiment.round_id}, "
            f"违规: {experiment.is_violation}"
        )

    def get_by_round(self, round_id: int) -> Optional[ExperimentData]:
        """
        根据轮次获取实验数据

        Args:
            round_id: 轮次ID

        Returns:
            实验数据，如果不存在返回None
        """
        for exp in self._experiments:
            if exp.round_id == round_id:
                return exp
        return None

    def get_range(self, start_round: int, end_round: int) -> List[ExperimentData]:
        """
        获取指定轮次范围的实验数据

        Args:
            start_round: 起始轮次
            end_round: 结束轮次

        Returns:
            实验数据列表
        """
        result = [
            exp for exp in self._experiments
            if start_round <= exp.round_id <= end_round
        ]
        logger.debug(f"获取轮次 {start_round}-{end_round} 的数据，共 {len(result)} 条")
        return result

    def get_all(self) -> List[ExperimentData]:
        """
        获取所有实验数据

        Returns:
            所有实验数据列表
        """
        return self._experiments.copy()

    def get_violations(self) -> List[ExperimentData]:
        """
        获取所有违规的实验数据

        Returns:
            违规实验数据列表
        """
        violations = [exp for exp in self._experiments if exp.is_violation]
        logger.debug(f"获取违规数据，共 {len(violations)} 条")
        return violations

    def get_recent(self, n: int) -> List[ExperimentData]:
        """
        获取最近的n条实验数据

        Args:
            n: 获取数量

        Returns:
            最近的实验数据列表
        """
        recent = self._experiments[-n:]
        logger.debug(f"获取最近 {len(recent)} 条实验数据")
        return recent

    def get_statistics(self) -> Dict[str, Any]:
        """
        获取实验统计数据

        Returns:
            统计数据字典
        """
        if not self._experiments:
            return {
                "total_rounds": 0,
                "violation_count": 0,
                "violation_rate": 0.0,
                "avg_satisfaction": 0.0,
                "avg_total_reward": 0.0,
            }

        total_rounds = len(self._experiments)
        violations = [exp for exp in self._experiments if exp.is_violation]
        violation_count = len(violations)
        violation_rate = (violation_count / total_rounds) * 100

        avg_satisfaction = sum(exp.satisfaction for exp in self._experiments) / total_rounds
        avg_total_reward = sum(exp.total_reward for exp in self._experiments) / total_rounds

        # 计算策略漂移
        if len(self._experiments) >= 2:
            initial_strategy = self._experiments[0].strategy_theta
            current_strategy = self._experiments[-1].strategy_theta
            policy_drift = abs(current_strategy - initial_strategy)
        else:
            policy_drift = 0.0

        # 计算损益偏差
        total_reward = sum(exp.total_reward for exp in self._experiments)
        profit_bias = total_reward / total_rounds if total_rounds > 0 else 0.0

        return {
            "total_rounds": total_rounds,
            "violation_count": violation_count,
            "violation_rate": violation_rate,
            "avg_satisfaction": avg_satisfaction,
            "avg_total_reward": avg_total_reward,
            "policy_drift": policy_drift,
            "profit_bias": profit_bias,
            "current_strategy": self._experiments[-1].strategy_theta if self._experiments else 0.0,
        }

    def get_evolution_curve_data(self) -> Dict[str, List]:
        """
        获取演化曲线数据

        Returns:
            包含轮次、满意度、合规率、策略参数等的数据字典
        """
        if not self._experiments:
            return {
                "rounds": [],
                "satisfaction": [],
                "compliance_rates": [],
                "strategy_params": [],
                "immediate_rewards": [],
                "delayed_rewards": [],
            }

        rounds = [exp.round_id for exp in self._experiments]
        satisfaction = [exp.satisfaction for exp in self._experiments]

        # 计算累计合规率
        compliance_rates = []
        violation_count = 0
        for i, exp in enumerate(self._experiments):
            if exp.is_violation:
                violation_count += 1
            compliance_rate = ((i + 1 - violation_count) / (i + 1)) * 100
            compliance_rates.append(compliance_rate)

        strategy_params = [exp.strategy_theta for exp in self._experiments]
        immediate_rewards = [exp.immediate_reward for exp in self._experiments]
        delayed_rewards = [exp.delayed_reward for exp in self._experiments]

        return {
            "rounds": rounds,
            "satisfaction": satisfaction,
            "compliance_rates": compliance_rates,
            "strategy_params": strategy_params,
            "immediate_rewards": immediate_rewards,
            "delayed_rewards": delayed_rewards,
        }

    def clear(self) -> None:
        """清空所有实验数据"""
        size_before = len(self._experiments)
        self._experiments.clear()
        self._loaded = False
        logger.info(f"实验数据已清空 - 清空前数量: {size_before}")

    def save(self, filename: Optional[str] = None) -> str:
        """
        保存实验数据到文件

        Args:
            filename: 文件名，默认使用时间戳

        Returns:
            保存的文件路径
        """
        if filename is None:
            filename = f"experiment_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        filepath = self.storage_path / filename

        data = {
            "experiments": [exp.model_dump(mode="json") for exp in self._experiments],
            "statistics": self.get_statistics(),
            "saved_at": datetime.now().isoformat(),
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        logger.info(f"实验数据已保存到 {filepath} - 共 {len(self._experiments)} 条")
        return str(filepath)

    def load(self, filepath: str) -> None:
        """
        从文件加载实验数据

        Args:
            filepath: 文件路径
        """
        path_obj = Path(filepath)

        if not path_obj.exists():
            logger.error(f"文件不存在: {filepath}")
            return

        with open(path_obj, "r", encoding="utf-8") as f:
            data = json.load(f)

        self._experiments.clear()
        for exp_data in data["experiments"]:
            experiment = ExperimentData(**exp_data)
            self._experiments.append(experiment)

        self._loaded = True
        logger.info(
            f"实验数据已从 {filepath} 加载 - 共 {len(self._experiments)} 条"
        )

    def export_to_csv(self, filepath: str) -> None:
        """
        导出实验数据到CSV文件

        Args:
            filepath: CSV文件路径
        """
        import pandas as pd

        # 转换为DataFrame
        data_dicts = [exp.model_dump() for exp in self._experiments]
        df = pd.DataFrame(data_dicts)

        # 保存为CSV
        df.to_csv(filepath, index=False, encoding="utf-8-sig")

        logger.info(f"实验数据已导出到 {filepath} - 共 {len(self._experiments)} 条")

    def export_to_json(self, filepath: str) -> None:
        """
        导出实验数据到JSON文件

        Args:
            filepath: JSON文件路径
        """
        data = {
            "experiments": [exp.model_dump(mode="json") for exp in self._experiments],
            "statistics": self.get_statistics(),
            "exported_at": datetime.now().isoformat(),
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        logger.info(f"实验数据已导出到 {filepath} - 共 {len(self._experiments)} 条")

    def __len__(self) -> int:
        """返回实验数据数量"""
        return len(self._experiments)


# ==================== 全局实例 ====================

# 全局实验数据存储实例
experiment_storage = ExperimentDataStorage()


# ==================== 导出 ====================

__all__ = [
    "ExperimentDataStorage",
    "experiment_storage",
]
