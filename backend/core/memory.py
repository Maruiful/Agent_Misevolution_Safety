"""
记忆管理模块
管理智能体的上下文记忆和经验回放
"""
from typing import List, Dict, Any, Optional
from collections import deque
from datetime import datetime
from models.schemas import Message, MessageRole, ExperimentData
from utils.logger import logger


class ConversationMemory:
    """对话记忆管理

    管理智能体的对话历史和上下文
    """

    def __init__(self, max_messages: int = 100):
        """
        初始化对话记忆

        Args:
            max_messages: 最大消息数量
        """
        self.max_messages = max_messages
        self.messages: deque[Message] = deque(maxlen=max_messages)

        logger.info(f"对话记忆初始化完成 - 最大消息数: {max_messages}")

    def add_message(
        self,
        role: MessageRole,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        添加消息

        Args:
            role: 消息角色
            content: 消息内容
            metadata: 元数据
        """
        message = Message(
            role=role,
            content=content,
            metadata=metadata or {},
            timestamp=datetime.now(),
        )

        self.messages.append(message)

        logger.debug(
            f"添加消息 - 角色: {role.value}, "
            f"长度: {len(content)}, 总消息数: {len(self.messages)}"
        )

    def get_recent_messages(self, n: int = 10) -> List[Message]:
        """
        获取最近的消息

        Args:
            n: 消息数量

        Returns:
            消息列表
        """
        return list(self.messages)[-n:]

    def get_all_messages(self) -> List[Message]:
        """
        获取所有消息

        Returns:
            消息列表
        """
        return list(self.messages)

    def get_conversation_history(
        self,
        for_llm: bool = True
    ) -> List[Dict[str, str]]:
        """
        获取对话历史

        Args:
            for_llm: 是否转换为LLM格式

        Returns:
            对话历史列表
        """
        if for_llm:
            return [
                {"role": msg.role.value, "content": msg.content}
                for msg in self.messages
            ]

        return [msg.model_dump() for msg in self.messages]

    def clear(self) -> None:
        """清空记忆"""
        size_before = len(self.messages)
        self.messages.clear()
        logger.info(f"对话记忆已清空 - 清空前大小: {size_before}")

    def __len__(self) -> int:
        """返回消息数量"""
        return len(self.messages)


class EpisodicMemory:
    """情景记忆管理

    管理重要的情景和事件
    """

    def __init__(self, capacity: int = 50):
        """
        初始化情景记忆

        Args:
            capacity: 容量
        """
        self.capacity = capacity
        self.episodes: List[ExperimentData] = []

        logger.info(f"情景记忆初始化完成 - 容量: {capacity}")

    def add_episode(self, episode: ExperimentData) -> None:
        """
        添加情景

        Args:
            episode: 情景数据
        """
        self.episodes.append(episode)

        # 如果超过容量，移除最旧的
        if len(self.episodes) > self.capacity:
            self.episodes.pop(0)

        logger.debug(
            f"添加情景 - 轮次: {episode.round_id}, "
            f"违规: {episode.is_violation}, 总情景数: {len(self.episodes)}"
        )

    def get_violation_episodes(self) -> List[ExperimentData]:
        """
        获取所有违规情景

        Returns:
            违规情景列表
        """
        violations = [ep for ep in self.episodes if ep.is_violation]
        logger.debug(f"获取违规情景 - 共 {len(violations)} 条")
        return violations

    def get_recent_episodes(self, n: int = 10) -> List[ExperimentData]:
        """
        获取最近的情景

        Args:
            n: 数量

        Returns:
            情景列表
        """
        return self.episodes[-n:]

    def get_similar_episodes(
        self,
        user_input: str,
        threshold: float = 0.5
    ) -> List[ExperimentData]:
        """
        获取相似的情景

        Args:
            user_input: 用户输入
            threshold: 相似度阈值

        Returns:
            相似情景列表
        """
        # 简单的关键词匹配
        similar_episodes = []

        for episode in self.episodes:
            # 计算关键词重叠度
            input_words = set(user_input.lower().split())
            episode_words = set(episode.user_input.lower().split())

            if not input_words or not episode_words:
                continue

            overlap = len(input_words & episode_words)
            similarity = overlap / len(input_words | episode_words)

            if similarity >= threshold:
                similar_episodes.append(episode)

        logger.debug(
            f"获取相似情景 - 输入: {user_input[:30]}..., "
            f"找到 {len(similar_episodes)} 条相似情景"
        )

        return similar_episodes

    def get_statistics(self) -> Dict[str, Any]:
        """
        获取统计信息

        Returns:
            统计信息字典
        """
        if not self.episodes:
            return {
                "total_episodes": 0,
                "violation_count": 0,
                "violation_rate": 0.0,
            }

        total = len(self.episodes)
        violations = len([ep for ep in self.episodes if ep.is_violation])

        return {
            "total_episodes": total,
            "violation_count": violations,
            "violation_rate": violations / total if total > 0 else 0.0,
        }

    def clear(self) -> None:
        """清空情景记忆"""
        size_before = len(self.episodes)
        self.episodes.clear()
        logger.info(f"情景记忆已清空 - 清空前大小: {size_before}")

    def __len__(self) -> int:
        """返回情景数量"""
        return len(self.episodes)


class SemanticMemory:
    """语义记忆管理

    存储和检索知识、规则等语义信息
    """

    def __init__(self):
        """初始化语义记忆"""
        self.knowledge_base: Dict[str, Any] = {
            "refund_policy": "退款需要验证客户身份和订单信息",
            "verification_process": "必须核对订单号、购买记录、退款原因",
            "service_standards": "保持专业、礼貌、合规",
        }

        logger.info("语义记忆初始化完成")

    def get_knowledge(self, key: str) -> Optional[Any]:
        """
        获取知识

        Args:
            key: 知识键

        Returns:
            知识值
        """
        return self.knowledge_base.get(key)

    def set_knowledge(self, key: str, value: Any) -> None:
        """
        设置知识

        Args:
            key: 知识键
            value: 知识值
        """
        self.knowledge_base[key] = value
        logger.debug(f"设置知识 - {key}: {value}")

    def get_all_knowledge(self) -> Dict[str, Any]:
        """
        获取所有知识

        Returns:
            知识字典
        """
        return self.knowledge_base.copy()

    def search_knowledge(self, query: str) -> List[str]:
        """
        搜索知识

        Args:
            query: 搜索查询

        Returns:
            匹配的知识键列表
        """
        query_lower = query.lower()
        matching_keys = [
            key for key in self.knowledge_base
            if query_lower in key.lower() or query_lower in str(self.knowledge_base[key]).lower()
        ]

        logger.debug(f"搜索知识 - 查询: {query}, 找到 {len(matching_keys)} 条")
        return matching_keys


class MemoryManager:
    """记忆管理器

    整合所有类型的记忆
    """

    def __init__(
        self,
        max_conversation_messages: int = 100,
        episodic_capacity: int = 50
    ):
        """
        初始化记忆管理器

        Args:
            max_conversation_messages: 最大对话消息数
            episodic_capacity: 情景记忆容量
        """
        self.conversation = ConversationMemory(max_conversation_messages)
        self.episodic = EpisodicMemory(episodic_capacity)
        self.semantic = SemanticMemory()

        logger.info("记忆管理器初始化完成")

    def add_experience(
        self,
        user_input: str,
        agent_response: str,
        experiment_data: ExperimentData
    ) -> None:
        """
        添加完整经验

        Args:
            user_input: 用户输入
            agent_response: 智能体回复
            experiment_data: 实验数据
        """
        # 添加到对话记忆
        self.conversation.add_message(
            role=MessageRole.USER,
            content=user_input,
            metadata={"round_id": experiment_data.round_id}
        )

        self.conversation.add_message(
            role=MessageRole.ASSISTANT,
            content=agent_response,
            metadata={
                "round_id": experiment_data.round_id,
                "is_violation": experiment_data.is_violation,
            }
        )

        # 添加到情景记忆
        self.episodic.add_episode(experiment_data)

        logger.debug(f"经验已添加 - 轮次: {experiment_data.round_id}")

    def get_memory_summary(self) -> Dict[str, Any]:
        """
        获取记忆摘要

        Returns:
            记忆摘要字典
        """
        return {
            "conversation": {
                "message_count": len(self.conversation),
                "recent_messages": len(self.conversation.get_recent_messages(10)),
            },
            "episodic": self.episodic.get_statistics(),
            "semantic": {
                "knowledge_count": len(self.semantic.get_all_knowledge()),
            },
        }

    def clear_all(self) -> None:
        """清空所有记忆"""
        self.conversation.clear()
        self.episodic.clear()
        logger.info("所有记忆已清空")


# ==================== 导出 ====================

__all__ = [
    "ConversationMemory",
    "EpisodicMemory",
    "SemanticMemory",
    "MemoryManager",
]
