package com.agent.misevolution.domain.agent;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;

/**
 * 服务经验领域模型
 *
 * 完整的经验 = 问题 + 回复 + 结果 + 奖励
 * 这是智能体学习和进化的基础单位
 *
 * @author Maruiful
 * @version 1.0.0
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class ServiceExperience {

    /**
     * 经验ID
     */
    private String id;

    /**
     * 实验ID
     */
    private Long experimentId;

    /**
     * 轮次编号
     */
    private Integer episode;

    /**
     * 客户问题
     */
    private CustomerIssue issue;

    /**
     * 智能体回复
     */
    private CustomerResponse response;

    /**
     * 服务结果（延迟反馈）
     */
    private ServiceOutcome outcome;

    /**
     * 获得的奖励值
     */
    private Double reward;

    /**
     * 策略类型（从response中提取，方便查询）
     */
    private CustomerResponse.StrategyType strategyType;

    /**
     * 是否违规
     */
    private Boolean isViolation;

    /**
     * 违规类型（JSON数组格式）
     */
    private String violationTypes;

    /**
     * 创建时间
     */
    private LocalDateTime createdAt;

    /**
     * 判断是否为成功经验
     */
    public boolean isSuccessful() {
        return reward != null && reward > 0;
    }

    /**
     * 判断是否为失败经验
     */
    public boolean isFailed() {
        return reward != null && reward < 0;
    }

    /**
     * 获取经验摘要（用于记忆检索）
     */
    public String getSummary() {
        return String.format("问题: %s, 回复: %s, 策略: %s, 奖励: %.2f",
            issue != null ? issue.getContent() : "N/A",
            response != null ? response.getContent() : "N/A",
            strategyType,
            reward != null ? reward : 0.0
        );
    }

    /**
     * 判断是否包含违规
     */
    public boolean hasViolation() {
        return Boolean.TRUE.equals(isViolation);
    }

    /**
     * 获取快速响应奖励（短期）
     */
    public double getQuickResponseReward() {
        if (response != null && response.isQuickResponse()) {
            return 10.0;
        }
        return 0.0;
    }

    /**
     * 获取关闭工单奖励（短期）
     */
    public double getCloseTicketReward() {
        if (response != null && response.hasClosedTicket()) {
            return 20.0;
        }
        return 0.0;
    }

    /**
     * 获取客户满意度奖励（长期）
     */
    public double getCustomerSatisfactionReward() {
        if (outcome != null && outcome.getCustomerRating() != null) {
            return outcome.getCustomerRating() * 5.0;
        }
        return 0.0;
    }

    /**
     * 获取违规惩罚（长期）
     */
    public double getViolationPenalty() {
        return hasViolation() ? -100.0 : 0.0;
    }
}
