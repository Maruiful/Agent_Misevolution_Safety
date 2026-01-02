package com.agent.misevolution.domain.evolution;

import com.agent.misevolution.domain.agent.CustomerResponse;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;
import java.util.Map;

/**
 * 策略模型
 *
 * 表示智能体的一种行为策略
 *
 * @author Maruiful
 * @version 1.0.0
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class Strategy {

    /**
     * 策略ID
     */
    private String id;

    /**
     * 策略名称
     */
    private String name;

    /**
     * 策略类型
     */
    private CustomerResponse.StrategyType type;

    /**
     * 策略描述
     */
    private String description;

    /**
     * 策略提示词模板
     * 用于生成 LLM 的提示词
     */
    private String promptTemplate;

    /**
     * Few-shot 示例
     */
    private String fewShotExamples;

    /**
     * 使用次数
     */
    private Integer usageCount;

    /**
     * 成功次数
     */
    private Integer successCount;

    /**
     * 违规次数
     */
    private Integer violationCount;

    /**
     * 总奖励值
     */
    private Double totalReward;

    /**
     * 平均奖励值
     */
    private Double averageReward;

    /**
     * 策略概率（用于选择）
     */
    private Double probability;

    /**
     * 策略权重（用于进化调整）
     */
    private Double weight;

    /**
     * 策略元数据（JSON格式）
     */
    private Map<String, Object> metadata;

    /**
     * 创建时间
     */
    private LocalDateTime createdAt;

    /**
     * 最后更新时间
     */
    private LocalDateTime updatedAt;

    /**
     * 构造函数
     */
    public Strategy(String id, String name, CustomerResponse.StrategyType type, String description) {
        this.id = id;
        this.name = name;
        this.type = type;
        this.description = description;
        this.usageCount = 0;
        this.successCount = 0;
        this.violationCount = 0;
        this.totalReward = 0.0;
        this.averageReward = 0.0;
        this.probability = 0.25; // 默认均等概率
        this.weight = 1.0;
        this.createdAt = LocalDateTime.now();
        this.updatedAt = LocalDateTime.now();
    }

    /**
     * 记录使用
     */
    public void recordUsage(double reward, boolean success, boolean violation) {
        this.usageCount++;
        this.totalReward = (this.totalReward == null ? 0.0 : this.totalReward) + reward;
        this.averageReward = this.totalReward / this.usageCount;

        if (success) {
            this.successCount++;
        }

        if (violation) {
            this.violationCount++;
        }

        this.updatedAt = LocalDateTime.now();
    }

    /**
     * 计算成功率
     */
    public double getSuccessRate() {
        if (usageCount == null || usageCount == 0) {
            return 0.0;
        }
        return (double) (successCount == null ? 0 : successCount) / usageCount;
    }

    /**
     * 计算违规率
     */
    public double getViolationRate() {
        if (usageCount == null || usageCount == 0) {
            return 0.0;
        }
        return (double) (violationCount == null ? 0 : violationCount) / usageCount;
    }

    /**
     * 判断是否为高成功率策略
     */
    public boolean isHighSuccessRate() {
        return getSuccessRate() >= 0.7;
    }

    /**
     * 判断是否为高违规率策略
     */
    public boolean isHighViolationRate() {
        return getViolationRate() >= 0.3;
    }

    /**
     * 判断是否为安全策略（低违规率）
     */
    public boolean isSafe() {
        return getViolationRate() < 0.1;
    }

    /**
     * 计算策略得分（综合考虑成功率和奖励）
     */
    public double getScore() {
        double successScore = getSuccessRate() * 0.6;
        double rewardScore = (averageReward == null ? 0.0 : Math.max(0, Math.min(1, (averageReward + 100) / 200.0))) * 0.4;
        double violationPenalty = getViolationRate() * 0.5;

        return successScore + rewardScore - violationPenalty;
    }

    /**
     * 更新策略概率（基于得分）
     */
    public void updateProbability(double score, double totalScore) {
        if (totalScore > 0) {
            this.probability = score / totalScore;
        } else {
            this.probability = 0.25; // 默认均等概率
        }
        this.updatedAt = LocalDateTime.now();
    }

    /**
     * 获取策略摘要
     */
    public String getSummary() {
        return String.format("策略: %s, 使用: %d次, 成功率: %.2f%%, 违规率: %.2f%%, 平均奖励: %.2f",
            name, usageCount, getSuccessRate() * 100, getViolationRate() * 100,
            averageReward == null ? 0.0 : averageReward);
    }

    @Override
    public String toString() {
        return String.format("Strategy{id=%s, name='%s', type=%s, usageCount=%d, avgReward=%.2f}",
            id, name, type, usageCount, averageReward == null ? 0.0 : averageReward);
    }
}
