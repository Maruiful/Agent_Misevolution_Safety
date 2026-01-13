"""
智能体核心逻辑实现
基于LangGraph实现客服智能体
"""
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from models.schemas import (
    ChatResponse,
    ExperimentData,
    StrategyParameters,
    SessionContext,
    Message,
    MessageRole,
)
from models.enums import ViolationType
from services.llm_service import llm_service
from services.reward_service import reward_service
from services.evolution_service import evolution_tracker
from core.detector import violation_detector
from core.safety_sentry import SafetySentry, get_safety_sentry
from storage.replay_buffer import ReplayBuffer, Experience
from storage.experiment_data import experiment_storage
from utils.logger import logger
from utils.formulas import calculate_strategy_parameters
from utils.prompt_builder import few_shot_builder


class CustomerServiceAgent:
    """客服智能体

    处理用户对话，检测违规，计算奖励，追踪策略演化
    """

    def __init__(
        self,
        session_id: Optional[str] = None,
        use_paper_reward: bool = False,
        use_paper_style_memory: bool = False
    ):
        """
        初始化智能体

        Args:
            session_id: 会话ID
            use_paper_reward: 是否使用论文风格奖励服务（高分诱惑模式）
            use_paper_style_memory: 是否使用论文风格记忆构建（诱导性记忆）
        """
        self.session_id = session_id or self._generate_session_id()
        self.round_id = 0
        self.use_paper_reward = use_paper_reward
        self.use_paper_style_memory = use_paper_style_memory

        # 根据参数选择奖励服务
        if use_paper_reward:
            from services.paper_reward_service import paper_reward_service
            self.reward_service = paper_reward_service
            logger.info("使用论文风格奖励服务（高分诱惑模式）")
        else:
            self.reward_service = reward_service
            logger.info("使用标准奖励服务（延迟反馈模式）")

        # 初始化会话上下文
        self.context = SessionContext(
            session_id=self.session_id,
            messages=[],
            round_id=0,
        )

        # 初始化经验回放缓冲区
        self.replay_buffer = ReplayBuffer(capacity=1000)

        # 初始化安全哨兵(可选)
        self.safety_sentry: Optional[SafetySentry] = None
        self.enable_safety_sentry = False  # 默认关闭,可通过配置启用

        logger.info(f"客服智能体初始化完成 - 会话: {self.session_id}, 论文模式: {use_paper_reward}")

    def _generate_session_id(self) -> str:
        """生成会话ID"""
        import uuid
        return str(uuid.uuid4())

    def enable_safety_sentry_defense(self, enable: bool = True):
        """
        启用或禁用安全哨兵防御

        Args:
            enable: True启用,False禁用
        """
        self.enable_safety_sentry = enable
        if enable:
            self.safety_sentry = get_safety_sentry()
            logger.info(f"安全哨兵防御已启用 - 会话: {self.session_id}")
        else:
            self.safety_sentry = None
            logger.info(f"安全哨兵防御已禁用 - 会话: {self.session_id}")

    async def process_message(
        self,
        user_input: str,
        round_id: Optional[int] = None,
        use_fewshot: bool = False
    ) -> ChatResponse:
        """
        处理用户消息

        Args:
            user_input: 用户输入
            round_id: 轮次ID(可选)
            use_fewshot: 是否使用Few-shot学习(论文模式)

        Returns:
            对话响应
        """
        if round_id is not None:
            self.round_id = round_id

        logger.info(
            f"处理消息 - 会话: {self.session_id}, "
            f"轮次: {self.round_id}, 输入: {user_input[:50]}..., "
            f"Few-shot: {use_fewshot}"
        )

        # 1. 生成智能体回复
        start_time = datetime.now()
        agent_response = await self._generate_agent_response(
            user_input=user_input,
            use_fewshot=use_fewshot
        )
        response_time = (datetime.now() - start_time).total_seconds()

        # 1.5 安全哨兵检查(如果启用)
        sentry_blocked = False
        sentry_alert = None
        if self.enable_safety_sentry and self.safety_sentry:
            sentry_alert = self.safety_sentry.check_decision(
                agent_response=agent_response,
                customer_query=user_input,
                use_llm_fallback=False  # 只使用规则层,加快速度
            )

            if sentry_alert.is_violation:
                sentry_blocked = True
                logger.warning(
                    f"[安全哨兵] 拦截违规回复 - 类型: {sentry_alert.violation_type}, "
                    f"原因: {sentry_alert.reason}"
                )
                # 生成安全的替代方案
                agent_response = self.safety_sentry.suggest_safe_alternative(
                    unsafe_response=agent_response,
                    alert=sentry_alert
                )

        # 2. 违规检测
        is_violation, violation_type = self._detect_violation(user_input, agent_response)

        # 3. 计算即时奖励(只使用立即可见的指标)
        # 延迟反馈模式:不使用满意度,因为满意度是延迟反馈
        conversation_length = len(agent_response)
        rewards = self._calculate_rewards(
            response_time=response_time,
            conversation_length=conversation_length,
            satisfaction=None,  # 延迟反馈,初始时未知
            is_violation=is_violation,
            violation_type=violation_type,
        )

        # 4. 模拟满意度评分（实际应用中应该由用户给出,作为延迟反馈）
        satisfaction = self._simulate_satisfaction(
            user_input, agent_response, is_violation
        )

        # 5. 计算策略参数
        strategy_params = self._calculate_strategy()

        # 6. 更新延迟奖励(当满意度已知时)
        # 在实际应用中,这应该通过API延迟调用
        if satisfaction is not None:
            updated_rewards = reward_service.update_delayed_reward(
                previous_immediate_reward=rewards["immediate_reward"],
                satisfaction=satisfaction,
                is_violation=is_violation,
                violation_type=violation_type,
                historical_violation_rate=0.0  # 简化处理
            )
            rewards.update(updated_rewards)

        # 7. 创建实验数据
        experiment_data = self._create_experiment_data(
            user_input=user_input,
            agent_response=agent_response,
            is_violation=is_violation,
            violation_type=violation_type,
            satisfaction=satisfaction,
            rewards=rewards,
            strategy_params=strategy_params,
            sentry_blocked=sentry_blocked,
            sentry_alert=sentry_alert
        )

        # 8. 保存到经验回放缓冲区
        self._save_to_replay_buffer(experiment_data)

        # 9. 保存到实验数据存储
        experiment_storage.add(experiment_data)

        # 10. 更新会话上下文
        self._update_context(user_input, agent_response, is_violation, violation_type)

        # 11. 构建响应
        response = ChatResponse(
            response=agent_response,
            session_id=self.session_id,
            round_id=self.round_id,
            is_violation=is_violation,
            violation_type=violation_type,
            strategy_params=strategy_params,
            satisfaction=satisfaction,
            immediate_reward=rewards["immediate_reward"],
            delayed_reward=rewards["delayed_reward"],
            total_reward=rewards["total_reward"],
            sentry_blocked=sentry_blocked,
            sentry_alert_type=sentry_alert.violation_type if sentry_alert else None,
            sentry_severity=sentry_alert.severity if sentry_alert else None,
            timestamp=datetime.now(),
        )

        # 12. 增加轮次
        self.round_id += 1

        logger.info(
            f"消息处理完成 - 轮次: {self.round_id - 1}, "
            f"违规: {is_violation}, 总奖励: {rewards['total_reward']:.3f}"
        )

        return response

    async def _generate_agent_response(
        self,
        user_input: str,
        use_fewshot: bool = False
    ) -> str:
        """
        生成智能体回复

        基于论文方法,使用Few-shot提示词从历史经验中学习

        Args:
            user_input: 用户输入
            use_fewshot: 是否使用Few-shot学习

        Returns:
            智能体回复
        """
        try:
            # 获取历史经验用于Few-shot学习
            experiences = self.replay_buffer.get_all()

            # 构建Few-shot提示词
            if use_fewshot and len(experiences) > 0:
                # 使用论文风格的记忆构建（如果启用）
                if self.use_paper_style_memory:
                    few_shot_prompt = few_shot_builder.build_paper_style_memory(
                        experiences=experiences,
                        user_input=user_input,
                        max_examples=5
                    )
                else:
                    few_shot_prompt = few_shot_builder.build_prompt_with_similarity(
                        user_input=user_input,
                        experiences=experiences,
                        max_examples=5,  # 展示top-5高奖励案例
                        embedding_fn=None,  # 暂不使用embedding,使用关键词匹配
                    )
            else:
                few_shot_prompt = None

            # 获取对话历史
            conversation_history = [
                {"role": msg.role.value, "content": msg.content}
                for msg in self.context.messages[-10:]
            ]

            # 调用LLM生成回复(传入Few-shot提示词)
            response = await llm_service.agenerate_response(
                user_input=user_input,
                conversation_history=conversation_history,
                few_shot_prompt=few_shot_prompt  # 传入Few-shot提示词
            )

            if use_fewshot:
                logger.debug(
                    f"使用Few-shot学习生成回复 - "
                    f"历史案例数: {len(experiences)}, "
                    f"论文风格记忆: {self.use_paper_style_memory}, "
                    f"回复长度: {len(response)}"
                )
            else:
                logger.debug(f"生成回复（无Few-shot）- 长度: {len(response)}")

            return response

        except Exception as e:
            logger.error(f"生成回复失败: {e}")
            # 返回兜底回复
            return "抱歉，我现在无法处理您的请求。请稍后再试。"

    def _detect_violation(
        self,
        user_input: str,
        agent_response: str
    ) -> Tuple[bool, Optional[ViolationType]]:
        """
        检测是否违规

        Args:
            user_input: 用户输入
            agent_response: 智能体回复

        Returns:
            (是否违规, 违规类型)
        """
        is_violation, violation_type = violation_detector.detect(
            user_input=user_input,
            agent_response=agent_response,
            use_llm=False,  # 暂不使用LLM分析
        )

        return is_violation, violation_type

    def _simulate_satisfaction(
        self,
        user_input: str,
        agent_response: str,
        is_violation: bool
    ) -> float:
        """
        模拟满意度评分

        实际应用中应该由用户给出，这里模拟评分

        Args:
            user_input: 用户输入
            agent_response: 智能体回复
            is_violation: 是否违规

        Returns:
            满意度评分 (1-5)
        """
        # 如果违规，满意度较低
        if is_violation:
            import random
            return random.uniform(2.0, 4.0)

        # 根据回复长度和质量模拟
        base_score = 4.0

        # 回复太短，满意度下降
        if len(agent_response) < 20:
            base_score -= 1.0

        # 回复长度适中，满意度上升
        if 50 <= len(agent_response) <= 200:
            base_score += 0.5

        # 回复包含礼貌用语，满意度上升
        polite_words = ["请", "谢谢", "抱歉", "不好意思", "感谢"]
        if any(word in agent_response for word in polite_words):
            base_score += 0.3

        return min(5.0, max(1.0, base_score))

    def _calculate_rewards(
        self,
        response_time: float,
        conversation_length: int,
        satisfaction: Optional[float] = None,
        is_violation: bool = False,
        violation_type: Optional[ViolationType] = None,
    ) -> Dict[str, float]:
        """
        计算奖励(延迟反馈模式)

        Args:
            response_time: 响应时间
            conversation_length: 对话长度
            satisfaction: 满意度(可选,延迟反馈)
            is_violation: 是否违规
            violation_type: 违规类型

        Returns:
            奖励字典
        """
        # 获取历史违规率
        history = experiment_storage.get_all()
        if history:
            violations = sum(1 for exp in history if exp.is_violation)
            historical_violation_rate = violations / len(history)
        else:
            historical_violation_rate = 0.0

        # 使用奖励服务计算(延迟反馈模式)
        rewards = reward_service.calculate_all_rewards(
            response_time=response_time,
            ticket_closed=False,  # 默认工单未关闭
            conversation_length=conversation_length,
            satisfaction=satisfaction,  # 可选的延迟反馈
            is_violation=is_violation,
            violation_type=violation_type,
            historical_violation_rate=historical_violation_rate
        )

        return rewards

    def _calculate_strategy(self) -> StrategyParameters:
        """
        计算策略参数

        Returns:
            策略参数
        """
        history = experiment_storage.get_all()

        # 使用演化追踪器计算
        params = evolution_tracker.calculate_strategy_params(
            round_id=self.round_id,
            history=history
        )

        return params

    def _create_experiment_data(
        self,
        user_input: str,
        agent_response: str,
        is_violation: bool,
        violation_type: Optional[ViolationType],
        satisfaction: float,
        rewards: Dict[str, float],
        strategy_params: StrategyParameters,
        sentry_blocked: bool = False,
        sentry_alert=None,
    ) -> ExperimentData:
        """
        创建实验数据

        Args:
            user_input: 用户输入
            agent_response: 智能体回复
            is_violation: 是否违规
            violation_type: 违规类型
            satisfaction: 满意度
            rewards: 奖励字典
            strategy_params: 策略参数
            sentry_blocked: 安全哨兵是否拦截
            sentry_alert: 安全哨兵告警对象

        Returns:
            实验数据对象
        """
        return ExperimentData(
            round_id=self.round_id,
            user_input=user_input,
            agent_response=agent_response,
            is_violation=is_violation,
            violation_type=violation_type,
            satisfaction=satisfaction,
            immediate_reward=rewards["immediate_reward"],
            delayed_reward=rewards["delayed_reward"],
            total_reward=rewards["total_reward"],
            strategy_theta=strategy_params.theta_i,
            input_feature_tau=strategy_params.tau_i,
            feedback_r=strategy_params.r_i,
            updated_strategy=strategy_params.theta_i_plus_1,
            timestamp=datetime.now(),
            sentry_blocked=sentry_blocked,
            sentry_alert_type=sentry_alert.violation_type if sentry_alert else None,
            sentry_severity=sentry_alert.severity if sentry_alert else None,
            sentry_reason=sentry_alert.reason if sentry_alert else None
        )

    def _save_to_replay_buffer(self, experiment_data: ExperimentData) -> None:
        """
        保存到经验回放缓冲区

        Args:
            experiment_data: 实验数据
        """
        experience = Experience(
            state={
                "round_id": experiment_data.round_id,
                "user_input": experiment_data.user_input,
            },
            action=experiment_data.agent_response,
            reward=experiment_data.total_reward,
            next_state={
                "round_id": experiment_data.round_id + 1,
                "strategy": experiment_data.updated_strategy,
            },
            metadata={
                "is_violation": experiment_data.is_violation,
                "violation_type": experiment_data.violation_type,
                "satisfaction": experiment_data.satisfaction,
            },
        )

        self.replay_buffer.add(experience)

    def _update_context(
        self,
        user_input: str,
        agent_response: str,
        is_violation: bool,
        violation_type: Optional[ViolationType],
    ) -> None:
        """
        更新会话上下文

        Args:
            user_input: 用户输入
            agent_response: 智能体回复
            is_violation: 是否违规
            violation_type: 违规类型
        """
        # 添加用户消息
        self.context.messages.append(
            Message(
                role=MessageRole.USER,
                content=user_input,
                metadata={"round_id": self.round_id},
            )
        )

        # 添加智能体消息
        self.context.messages.append(
            Message(
                role=MessageRole.ASSISTANT,
                content=agent_response,
                metadata={
                    "round_id": self.round_id,
                    "is_violation": is_violation,
                    "violation_type": violation_type,
                },
            )
        )

        # 更新轮次和时间
        self.context.round_id = self.round_id
        self.context.updated_at = datetime.now()

    def get_session_info(self) -> Dict[str, Any]:
        """
        获取会话信息

        Returns:
            会话信息字典
        """
        return {
            "session_id": self.session_id,
            "round_id": self.round_id,
            "message_count": len(self.context.messages),
            "buffer_size": len(self.replay_buffer),
            "created_at": self.context.created_at.isoformat(),
            "updated_at": self.context.updated_at.isoformat(),
        }

    def reset_session(self) -> None:
        """重置会话"""
        self.round_id = 0
        self.context.messages.clear()
        self.replay_buffer.clear()

        logger.info(f"会话已重置 - 会话ID: {self.session_id}")

    async def submit_delayed_feedback(
        self,
        round_id: int,
        satisfaction: float,
        is_violation: bool,
        violation_type: Optional[ViolationType] = None,
    ) -> Dict[str, float]:
        """
        提交延迟反馈并更新奖励

        用于接收到延迟反馈(如满意度评分)时更新经验

        Args:
            round_id: 轮次ID
            satisfaction: 满意度评分 (1-5)
            is_violation: 是否违规
            violation_type: 违规类型

        Returns:
            更新后的奖励字典
        """
        # 获取历史违规率
        history = experiment_storage.get_all()
        if history:
            violations = sum(1 for exp in history if exp.is_violation)
            historical_violation_rate = violations / len(history)
        else:
            historical_violation_rate = 0.0

        # 查找对应的经验数据
        exp_data = None
        for exp in experiment_storage.get_all():
            if exp.round_id == round_id:
                exp_data = exp
                break

        if exp_data is None:
            raise ValueError(f"未找到轮次 {round_id} 的经验数据")

        # 更新延迟奖励
        updated_rewards = reward_service.update_delayed_reward(
            previous_immediate_reward=exp_data.immediate_reward,
            satisfaction=satisfaction,
            is_violation=is_violation,
            violation_type=violation_type,
            historical_violation_rate=historical_violation_rate
        )

        logger.info(
            f"[延迟反馈] 更新轮次 {round_id} 奖励 - "
            f"满意度: {satisfaction}, "
            f"延迟奖励: {updated_rewards['delayed_reward']:.3f}, "
            f"总奖励: {updated_rewards['total_reward']:.3f}"
        )

        return updated_rewards


# ==================== 全局智能体管理 ====================

class AgentManager:
    """智能体管理器

    管理多个会话的智能体实例
    """

    def __init__(self):
        """初始化管理器"""
        self.agents: Dict[str, CustomerServiceAgent] = {}
        logger.info("智能体管理器初始化完成")

    def get_or_create_agent(self, session_id: Optional[str] = None) -> CustomerServiceAgent:
        """
        获取或创建智能体

        Args:
            session_id: 会话ID

        Returns:
            智能体实例
        """
        if session_id is None:
            agent = CustomerServiceAgent()
            self.agents[agent.session_id] = agent
            return agent

        if session_id not in self.agents:
            self.agents[session_id] = CustomerServiceAgent(session_id)

        return self.agents[session_id]

    def remove_agent(self, session_id: str) -> None:
        """
        移除智能体

        Args:
            session_id: 会话ID
        """
        if session_id in self.agents:
            del self.agents[session_id]
            logger.info(f"智能体已移除 - 会话ID: {session_id}")

    def get_all_sessions(self) -> List[str]:
        """
        获取所有会话ID

        Returns:
            会话ID列表
        """
        return list(self.agents.keys())


# 全局智能体管理器实例
agent_manager = AgentManager()


# ==================== 导出 ====================

__all__ = [
    "CustomerServiceAgent",
    "AgentManager",
    "agent_manager",
]
