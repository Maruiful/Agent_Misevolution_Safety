"""
经验回放缓冲区实现
用于存储和管理智能体的经验数据
"""
from typing import List, Optional, Dict, Any
from collections import deque
import pickle
import json
from pathlib import Path
from datetime import datetime
from models.schemas import Experience
from utils.logger import logger


class ReplayBuffer:
    """经验回放缓冲区"""

    def __init__(self, capacity: int = 1000):
        """
        初始化经验回放缓冲区

        Args:
            capacity: 缓冲区最大容量
        """
        self.capacity = capacity
        self.buffer: deque[Experience] = deque(maxlen=capacity)
        self._add_count = 0  # 总添加次数计数器

        logger.info(f"经验回放缓冲区初始化完成 - 容量: {capacity}")

    def add(self, experience: Experience) -> None:
        """
        添加一条经验到缓冲区

        Args:
            experience: 经验数据
        """
        self.buffer.append(experience)
        self._add_count += 1

        if self._add_count % 100 == 0:
            logger.info(
                f"缓冲区状态 - 当前大小: {len(self)}/{self.capacity}, "
                f"总添加次数: {self._add_count}"
            )

    def sample(self, batch_size: int) -> List[Experience]:
        """
        随机采样一批经验

        Args:
            batch_size: 批次大小

        Returns:
            采样的经验列表
        """
        if len(self.buffer) < batch_size:
            logger.warning(
                f"缓冲区大小({len(self)})小于请求的批次大小({batch_size})"
            )
            return list(self.buffer)

        import random
        samples = random.sample(list(self.buffer), batch_size)
        logger.debug(f"采样了 {batch_size} 条经验")
        return samples

    def get_recent(self, n: int) -> List[Experience]:
        """
        获取最近的n条经验

        Args:
            n: 获取数量

        Returns:
            最近的n条经验列表
        """
        recent = list(self.buffer)[-n:]
        logger.debug(f"获取了最近 {len(recent)} 条经验")
        return recent

    def get_all(self) -> List[Experience]:
        """
        获取所有经验

        Returns:
            所有经验列表
        """
        return list(self.buffer)

    def clear(self) -> None:
        """清空缓冲区"""
        size_before = len(self.buffer)
        self.buffer.clear()
        self._add_count = 0
        logger.info(f"缓冲区已清空 - 清空前大小: {size_before}")

    def __len__(self) -> int:
        """返回当前缓冲区大小"""
        return len(self.buffer)

    def is_full(self) -> bool:
        """检查缓冲区是否已满"""
        return len(self.buffer) >= self.capacity

    def get_statistics(self) -> Dict[str, Any]:
        """
        获取缓冲区统计信息

        Returns:
            统计信息字典
        """
        if not self.buffer:
            return {
                "size": 0,
                "capacity": self.capacity,
                "utilization": 0.0,
                "total_additions": self._add_count,
            }

        experiences = list(self.buffer)

        # 计算奖励统计
        rewards = [exp.reward for exp in experiences]
        violations = sum(1 for exp in experiences if exp.metadata.get("is_violation", False))

        return {
            "size": len(self.buffer),
            "capacity": self.capacity,
            "utilization": len(self.buffer) / self.capacity,
            "total_additions": self._add_count,
            "rewards": {
                "mean": sum(rewards) / len(rewards),
                "min": min(rewards),
                "max": max(rewards),
            },
            "violation_count": violations,
            "violation_rate": violations / len(experiences) if experiences else 0.0,
        }

    def save(self, path: str) -> None:
        """
        保存缓冲区到文件

        Args:
            path: 保存路径
        """
        path_obj = Path(path)
        path_obj.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "capacity": self.capacity,
            "experiences": [
                exp.model_dump(mode="json") for exp in self.buffer
            ],
            "add_count": self._add_count,
            "saved_at": datetime.now().isoformat(),
        }

        # 根据文件扩展名选择保存格式
        if path_obj.suffix == ".pkl":
            with open(path, "wb") as f:
                pickle.dump(data, f)
        else:
            # 默认使用JSON格式
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

        logger.info(f"缓冲区已保存到 {path} - 共 {len(self.buffer)} 条经验")

    def load(self, path: str) -> None:
        """
        从文件加载缓冲区

        Args:
            path: 加载路径
        """
        path_obj = Path(path)

        if not path_obj.exists():
            logger.error(f"文件不存在: {path}")
            return

        # 根据文件扩展名选择加载格式
        if path_obj.suffix == ".pkl":
            with open(path, "rb") as f:
                data = pickle.load(f)
        else:
            # 默认使用JSON格式
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)

        # 恢复缓冲区状态
        self.capacity = data["capacity"]
        self._add_count = data.get("add_count", 0)
        self.buffer.clear()

        # 恢复经验数据
        for exp_data in data["experiences"]:
            experience = Experience(**exp_data)
            self.buffer.append(experience)

        logger.info(
            f"缓冲区已从 {path} 加载 - 共 {len(self.buffer)} 条经验, "
            f"容量: {self.capacity}"
        )

    def filter_by_violation(self, is_violation: bool) -> List[Experience]:
        """
        根据是否违规过滤经验

        Args:
            is_violation: 是否违规

        Returns:
            过滤后的经验列表
        """
        filtered = [
            exp for exp in self.buffer
            if exp.metadata.get("is_violation", False) == is_violation
        ]
        logger.debug(f"过滤出 {len(filtered)} 条{'违规' if is_violation else '合规'}经验")
        return filtered

    def get_violation_types(self) -> Dict[str, int]:
        """
        获取违规类型统计

        Returns:
            违规类型及其数量
        """
        violation_types = {}
        for exp in self.buffer:
            if exp.metadata.get("is_violation", False):
                v_type = exp.metadata.get("violation_type", "unknown")
                violation_types[v_type] = violation_types.get(v_type, 0) + 1

        return violation_types


# ==================== 优先级经验回放缓冲区 ====================

class PrioritizedReplayBuffer(ReplayBuffer):
    """优先级经验回放缓冲区

    根据经验的重要性（如TD误差）进行采样
    """

    def __init__(self, capacity: int = 1000, alpha: float = 0.6):
        """
        初始化优先级经验回放缓冲区

        Args:
            capacity: 缓冲区最大容量
            alpha: 优先级指数，控制采样随机性(0=均匀, 1=完全按优先级)
        """
        super().__init__(capacity)
        self.alpha = alpha
        self.priorities: deque[float] = deque(maxlen=capacity)
        self.max_priority = 1.0

        logger.info(f"优先级经验回放缓冲区初始化 - alpha: {alpha}")

    def add(self, experience: Experience, priority: Optional[float] = None) -> None:
        """
        添加经验及其优先级

        Args:
            experience: 经验数据
            priority: 优先级，默认为当前最大优先级
        """
        super().add(experience)

        # 如果没有指定优先级，使用当前最大优先级
        if priority is None:
            priority = self.max_priority

        self.priorities.append(priority)

    def sample(self, batch_size: int, beta: float = 0.4) -> tuple[List[Experience], List[float], List[float]]:
        """
        根据优先级采样经验

        Args:
            batch_size: 批次大小
            beta: 重要性采样权重(0=不修正, 1=完全修正)

        Returns:
            (经验列表, 采样权重, 采样索引)
        """
        import numpy as np

        if len(self.buffer) < batch_size:
            return list(self.buffer), [], []

        # 计算采样概率
        priorities = np.array(self.priorities) ** self.alpha
        prob = priorities / priorities.sum()

        # 采样索引
        indices = np.random.choice(len(self.buffer), batch_size, p=prob, replace=False)

        # 获取经验
        experiences = [self.buffer[i] for i in indices]

        # 计算重要性采样权重
        weights = (len(self.buffer) * prob[indices]) ** (-beta)
        weights = weights / weights.max()  # 归一化

        logger.debug(f"按优先级采样了 {batch_size} 条经验")
        return experiences, weights.tolist(), indices.tolist()

    def update_priorities(self, indices: List[int], priorities: List[float]) -> None:
        """
        更新经验的优先级

        Args:
            indices: 经验索引列表
            priorities: 新的优先级列表
        """
        for idx, priority in zip(indices, priorities):
            if 0 <= idx < len(self.priorities):
                self.priorities[idx] = priority
                self.max_priority = max(self.max_priority, priority)

        logger.debug(f"更新了 {len(indices)} 条经验的优先级")


# ==================== 导出 ====================

__all__ = [
    "ReplayBuffer",
    "PrioritizedReplayBuffer",
]
