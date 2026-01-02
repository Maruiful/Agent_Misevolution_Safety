package com.agent.misevolution.domain.agent;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;

/**
 * 服务结果模型
 *
 * 表示智能体行动后的结果反馈（延迟反馈）
 *
 * @author Maruiful
 * @version 1.0.0
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class ServiceOutcome {

    /**
     * 结果ID
     */
    private String id;

    /**
     * 对应的回复ID
     */
    private String responseId;

    /**
     * 客户满意度评分 (1-5)
     * 5: 非常满意
     * 4: 满意
     * 3: 一般
     * 2: 不满意
     * 1: 非常不满意
     */
    private Integer customerRating;

    /**
     * 是否发生投诉
     */
    private Boolean hasComplaint;

    /**
     * 投诉内容
     */
    private String complaintContent;

    /**
     * 问题是否真正解决
     */
    private Boolean issueResolved;

    /**
     * 是否发生后续问题
     */
    private Boolean hasFollowUpIssue;

    /**
     * 后续问题描述
     */
    private String followUpDescription;

    /**
     * 结果元数据（JSON格式）
     */
    private Object metadata;

    /**
     * 创建时间（反馈时间）
     */
    private LocalDateTime createdAt;

    /**
     * 判断是否为高质量结果
     */
    public boolean isHighQuality() {
        return customerRating != null && customerRating >= 4;
    }

    /**
     * 判断是否为低质量结果
     */
    public boolean isLowQuality() {
        return customerRating != null && customerRating <= 2;
    }

    /**
     * 判断是否有负面反馈
     */
    public boolean hasNegativeFeedback() {
        return Boolean.TRUE.equals(hasComplaint) || Boolean.TRUE.equals(hasFollowUpIssue);
    }
}
