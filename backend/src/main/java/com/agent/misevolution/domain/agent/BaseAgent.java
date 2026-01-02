package com.agent.misevolution.domain.agent;

import com.agent.misevolution.domain.evolution.Strategy;
import com.agent.misevolution.service.memory.ExperienceMemory;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;

import java.util.List;

/**
 * 智能体抽象基类
 *
 * 定义智能体的核心行为接口
 *
 * @author Maruiful
 * @version 1.0.0
 */
@Slf4j
public abstract class BaseAgent {

    /**
     * 记忆管理服务
     */
    @Autowired
    protected ExperienceMemory memory;

    /**
     * 智能体ID
     */
    protected String agentId;

    /**
     * 智能体名称
     */
    protected String agentName;

    /**
     * 智能体描述
     */
    protected String description;

    /**
     * 构造函数
     */
    protected BaseAgent(String agentId, String agentName, String description) {
        this.agentId = agentId;
        this.agentName = agentName;
        this.description = description;
    }

    /**
     * 生成决策
     *
     * 根据输入问题生成智能体的决策/回复
     *
     * @param issue 客户问题
     * @return 智能体回复
     */
    public abstract CustomerResponse generateDecision(CustomerIssue issue);

    /**
     * 执行动作
     *
     * 执行智能体决策后的具体动作（如关闭工单、查询订单等）
     *
     * @param response 智能体回复
     * @return 动作执行结果
     */
    public abstract ActionResult executeAction(CustomerResponse response);

    /**
     * 更新策略
     *
     * 根据经验反馈更新智能体的策略
     *
     * @param experience 服务经验
     */
    public abstract void updatePolicy(ServiceExperience experience);

    /**
     * 获取当前策略分布
     *
     * @return 策略概率分布
     */
    public abstract java.util.Map<Strategy, Double> getStrategyDistribution();

    /**
     * 获取智能体统计信息
     *
     * @return 统计信息Map
     */
    public abstract java.util.Map<String, Object> getStatistics();

    /**
     * 重置智能体状态
     */
    public abstract void reset();

    /**
     * 动作执行结果
     */
    @lombok.Data
    @lombok.Builder
    @lombok.NoArgsConstructor
    @lombok.AllArgsConstructor
    public static class ActionResult {
        /**
         * 执行是否成功
         */
        private Boolean success;

        /**
         * 执行结果描述
         */
        private String resultMessage;

        /**
         * 执行的数据（JSON格式）
         */
        private Object data;

        /**
         * 执行耗时（毫秒）
         */
        private Long duration;

        /**
         * 错误信息（如果失败）
         */
        private String errorMessage;
    }

    /**
     * 检索相关经验
     *
     * @param issue 客户问题
     * @return 相关经验列表
     */
    protected List<com.agent.misevolution.domain.memory.MemoryEntry> retrieveRelevantMemories(CustomerIssue issue) {
        String query = issue.getContent();
        return memory.retrieveSimilar(query);
    }

    /**
     * 构建上下文提示词
     *
     * 结合系统提示词、相关经验、当前问题构建完整的提示词
     *
     * @param issue 客户问题
     * @param relevantMemories 相关经验
     * @return 完整提示词
     */
    protected String buildPrompt(CustomerIssue issue, List<com.agent.misevolution.domain.memory.MemoryEntry> relevantMemories) {
        StringBuilder prompt = new StringBuilder();

        // 系统提示词
        prompt.append(getSystemPrompt()).append("\n\n");

        // 相关经验（Few-shot Learning）
        if (relevantMemories != null && !relevantMemories.isEmpty()) {
            prompt.append("以下是相关的历史经验，供参考：\n\n");
            for (com.agent.misevolution.domain.memory.MemoryEntry memory : relevantMemories) {
                prompt.append("- ").append(memory.getSummary()).append("\n");
            }
            prompt.append("\n");
        }

        // 当前问题
        prompt.append("当前客户问题：\n");
        prompt.append("问题描述：").append(issue.getContent()).append("\n");
        prompt.append("问题类型：").append(issue.getType()).append("\n");
        prompt.append("紧急程度：").append(issue.getUrgency()).append("\n");

        if (issue.getMetadata() != null && !issue.getMetadata().isEmpty()) {
            prompt.append("附加信息：").append(issue.getMetadata()).append("\n");
        }

        return prompt.toString();
    }

    /**
     * 获取系统提示词
     *
     * @return 系统提示词
     */
    protected abstract String getSystemPrompt();

    @Override
    public String toString() {
        return String.format("Agent{id=%s, name='%s', description='%s'}",
            agentId, agentName, description);
    }
}
