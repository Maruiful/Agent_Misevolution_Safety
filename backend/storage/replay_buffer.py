"""
经验回放缓冲区实现
用于存储和管理智能体的经验数据
"""
from typing import List, Optional, Dict, Any, Tuple
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

    def retrieve_similar(
        self,
        query: str,
        k: int = 5,
        embedding_fn: Optional[callable] = None
    ) -> List[Experience]:
        """
        检索与查询最相似的经验

        基于论文中的k近邻检索(k-NN)方法,使用向量相似度找到历史案例

        Args:
            query: 查询文本
            k: 返回最相似的k个经验
            embedding_fn: 可选的embedding函数,如果不提供则使用简单的关键词匹配

        Returns:
            按相似度排序的经验列表(从最相似到最不相似)
        """
        if not self.buffer:
            logger.warning("缓冲区为空,无法检索相似经验")
            return []

        if len(self.buffer) < k:
            k = len(self.buffer)

        # 如果提供了embedding函数,使用向量相似度
        if embedding_fn is not None:
            return self._retrieve_by_embedding(query, k, embedding_fn)
        else:
            # 降级方案:使用简单的关键词匹配
            return self._retrieve_by_keywords(query, k)

    def _retrieve_by_embedding(
        self,
        query: str,
        k: int,
        embedding_fn: callable
    ) -> List[Experience]:
        """
        使用embedding相似度检索经验

        Args:
            query: 查询文本
            k: 返回数量
            embedding_fn: embedding函数

        Returns:
            按相似度排序的经验列表
        """
        import numpy as np

        try:
            # 计算查询的embedding
            query_embedding = embedding_fn(query)

            # 计算所有经验的相似度
            similarities = []
            for exp in self.buffer:
                exp_embedding = embedding_fn(exp.state.get('user_input', ''))
                # 计算cosine相似度
                similarity = self._cosine_similarity(query_embedding, exp_embedding)
                similarities.append((similarity, exp))

            # 按相似度降序排序
            similarities.sort(key=lambda x: x[0], reverse=True)

            # 返回top-k经验
            top_experiences = [exp for _, exp in similarities[:k]]
            logger.debug(f"使用embedding检索到 {len(top_experiences)} 条相似经验")
            return top_experiences

        except Exception as e:
            logger.error(f"Embedding检索失败: {e}, 降级到关键词匹配")
            return self._retrieve_by_keywords(query, k)

    def _retrieve_by_keywords(self, query: str, k: int) -> List[Experience]:
        """
        使用关键词匹配检索经验(降级方案)

        Args:
            query: 查询文本
            k: 返回数量

        Returns:
            按匹配度排序的经验列表
        """
        query_lower = query.lower()

        # 简单的关键词重叠度计算
        scores = []
        for exp in self.buffer:
            exp_text = exp.state.get('user_input', '').lower()

            # 计算关键词重叠数量
            query_words = set(query_lower.split())
            exp_words = set(exp_text.split())
            overlap = len(query_words & exp_words)

            scores.append((overlap, exp))

        # 按重叠度降序排序
        scores.sort(key=lambda x: x[0], reverse=True)

        # 返回top-k经验
        top_experiences = [exp for _, exp in scores[:k]]
        logger.debug(f"使用关键词匹配检索到 {len(top_experiences)} 条经验")
        return top_experiences

    def _cosine_similarity(self, vec1: list, vec2: list) -> float:
        """
        计算两个向量的cosine相似度

        Args:
            vec1: 向量1
            vec2: 向量2

        Returns:
            相似度值[0, 1]
        """
        import numpy as np

        try:
            v1 = np.array(vec1)
            v2 = np.array(vec2)

            # 计算cosine相似度
            dot_product = np.dot(v1, v2)
            norm1 = np.linalg.norm(v1)
            norm2 = np.linalg.norm(v2)

            if norm1 == 0 or norm2 == 0:
                return 0.0

            similarity = dot_product / (norm1 * norm2)
            return float(similarity)

        except Exception as e:
            logger.warning(f"计算相似度失败: {e}")
            return 0.0

    def retrieve_top_rewards(self, n: int = 5) -> List[Experience]:
        """
        检索奖励最高的n条经验

        用于Few-shot提示词构建,优先展示成功案例

        Args:
            n: 返回数量

        Returns:
            按奖励降序排列的经验列表
        """
        if not self.buffer:
            return []

        if len(self.buffer) < n:
            n = len(self.buffer)

        # 按奖励排序
        sorted_exps = sorted(
            list(self.buffer),
            key=lambda exp: exp.reward,
            reverse=True
        )

        top_rewards = sorted_exps[:n]
        logger.debug(f"检索到奖励最高的 {len(top_rewards)} 条经验")
        return top_rewards

    def retrieve_similar_top_rewards(
        self,
        query: str,
        k: int = 5,
        embedding_fn: Optional[callable] = None
    ) -> List[Experience]:
        """
        检索相似经验中奖励最高的k条

        结合相似度和奖励,优先展示"成功的相似案例"

        Args:
            query: 查询文本
            k: 返回数量
            embedding_fn: embedding函数

        Returns:
            按奖励排序的相似经验列表
        """
        # 先检索相似经验
        similar_exps = self.retrieve_similar(query, k * 2, embedding_fn)

        # 从相似经验中选出奖励最高的k条
        sorted_exps = sorted(
            similar_exps,
            key=lambda exp: exp.reward,
            reverse=True
        )

        top_rewards = sorted_exps[:k]
        logger.debug(f"从相似经验中检索到奖励最高的 {len(top_rewards)} 条")
        return top_rewards

    def inject_negative_feedback(
        self,
        user_input: str,
        unsafe_response: str,
        safe_response: str,
        violation_type: str,
        judge_reason: str,
        penalty_reward: float = -5.0  # 改为-5.0,更温和的纠正
    ) -> Experience:
        """
        手动注入负向反馈到缓冲区

        用于安全哨兵的方案A: 当检测到违规时,不仅拦截,还手动插入负向反馈记录
        以纠正错误的奖励信号,重塑智能体的进化方向

        奖励设计 (方案1 - 温和纠正):
        - 违规注入: -5.0 (足够纠正1.0的错误信号,但不会过度惩罚)
        - 合规奖励: 1.0 (鼓励安全行为)
        - 差距: 6倍 (足以区分,避免极端对比)

        Args:
            user_input: 用户输入
            unsafe_response: 不安全的智能体回复
            safe_response: 安全的修正回复
            violation_type: 违规类型
            judge_reason: 裁判理由
            penalty_reward: 惩罚奖励值(默认-5.0,可调整)

        Returns:
            创建的负向反馈经验
        """
        # 创建负向反馈经验
        negative_experience = Experience(
            state={
                "user_input": user_input,
                "round_id": 0,  # 占位符
                "session_id": "sentry_injection"  # 标记为哨兵注入
            },
            action=unsafe_response,  # 记录不安全的回复
            reward=penalty_reward,  # 负向反馈奖励值
            next_state={
                "user_input": user_input,
                "safe_response": safe_response,  # 记录安全的修正方案
                "corrected": True
            },
            metadata={
                "is_violation": True,
                "violation_type": violation_type,
                "judge_reason": judge_reason,
                "safe_response": safe_response,
                "injected_by_sentry": True,  # 标记为哨兵注入
                "original_reward": 1.0,  # 原本错误的奖励(违规但用户可能给高分)
                "corrected_reward": penalty_reward,  # 纠正后的奖励
                "safe_response_reward": 1.0,  # 安全回复应该获得的奖励
                "timestamp": datetime.now().isoformat()
            }
        )

        # 添加到缓冲区
        self.add(negative_experience)

        logger.warning(
            f"[安全哨兵] 注入负向反馈 - 违规类型: {violation_type}, "
            f"惩罚奖励: {penalty_reward} (原始错误奖励: 1.0, 安全回复奖励: 1.0), "
            f"原回复: {unsafe_response[:50]}..."
        )

        return negative_experience


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
