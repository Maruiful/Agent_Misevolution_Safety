package com.agent.misevolution.domain.memory;

import com.agent.misevolution.domain.agent.CustomerResponse;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;
import java.util.List;

/**
 * 记忆摘要模型
 *
 * 多条相似经验的抽象总结，用于减少记忆存储和提高检索效率
 *
 * @author Maruiful
 * @version 1.0.0
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class MemorySummary {

    /**
     * 摘要ID
     */
    private String id;

    /**
     * 摘要标题
     */
    private String title;

    /**
     * 摘要内容（LLM生成的抽象描述）
     */
    private String content;

    /**
     * 关联的记忆ID列表
     */
    private List<String> memoryEntryIds;

    /**
     * 涵盖的经验数量
     */
    private Integer experienceCount;

    /**
     * 主要策略类型
     */
    private CustomerResponse.StrategyType dominantStrategy;

    /**
     * 平均奖励值
     */
    private Double averageReward;

    /**
     * 成功率（0-1）
     */
    private Double successRate;

    /**
     * 违规率（0-1）
     */
    private Double violationRate;

    /**
     * 向量表示
     */
    private EmbeddingVector embedding;

    /**
     * 重要性评分 (0-1)
     */
    private Double importanceScore;

    /**
     * 创建时间
     */
    private LocalDateTime createdAt;

    /**
     * 最后更新时间
     */
    private LocalDateTime updatedAt;

    /**
     * 是否为高成功率摘要
     */
    public boolean isHighSuccessRate() {
        return successRate != null && successRate >= 0.7;
    }

    /**
     * 是否为高违规率摘要
     */
    public boolean isHighViolationRate() {
        return violationRate != null && violationRate >= 0.3;
    }

    /**
     * 是否为正向经验（成功且无违规）
     */
    public boolean isPositiveSummary() {
        return isHighSuccessRate() && !isHighViolationRate();
    }

    /**
     * 是否为负向经验（低成功或高违规）
     */
    public boolean isNegativeSummary() {
        return (successRate != null && successRate < 0.5) || isHighViolationRate();
    }

    /**
     * 获取摘要评分（综合考虑成功率、违规率、奖励）
     */
    public double getSummaryScore() {
        double score = 0.0;

        if (successRate != null) {
            score += successRate * 0.4;
        }

        if (violationRate != null) {
            score -= violationRate * 0.3;
        }

        if (averageReward != null) {
            // 归一化奖励值（假设奖励范围 -100 到 100）
            double normalizedReward = (averageReward + 100) / 200.0;
            score += normalizedReward * 0.3;
        }

        return Math.max(0.0, Math.min(1.0, score));
    }

    /**
     * 添加关联记忆
     */
    public void addMemoryEntry(String memoryEntryId) {
        if (memoryEntryIds == null) {
            memoryEntryIds = new java.util.ArrayList<>();
        }
        memoryEntryIds.add(memoryEntryId);
        this.experienceCount = (this.experienceCount == null ? 0 : this.experienceCount) + 1;
        this.updatedAt = LocalDateTime.now();
    }

    /**
     * 更新统计指标
     */
    public void updateStatistics(List<com.agent.misevolution.domain.agent.ServiceExperience> experiences) {
        if (experiences == null || experiences.isEmpty()) {
            return;
        }

        // 计算平均奖励
        double totalReward = 0.0;
        int successCount = 0;
        int violationCount = 0;

        for (com.agent.misevolution.domain.agent.ServiceExperience exp : experiences) {
            if (exp.getReward() != null) {
                totalReward += exp.getReward();
            }
            if (exp.isSuccessful()) {
                successCount++;
            }
            if (exp.hasViolation()) {
                violationCount++;
            }
        }

        this.averageReward = totalReward / experiences.size();
        this.successRate = (double) successCount / experiences.size();
        this.violationRate = (double) violationCount / experiences.size();
        this.updatedAt = LocalDateTime.now();
    }
}
