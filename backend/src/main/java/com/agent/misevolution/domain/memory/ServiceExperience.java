package com.agent.misevolution.domain.memory;

import lombok.Data;

/**
 * 服务经验实体
 *
 * @author Maruiful
 * @version 1.0.0
 */
@Data
public class ServiceExperience {

    /**
     * 经验ID
     */
    private Long id;

    /**
     * 实验ID
     */
    private Long experimentId;

    /**
     * 轮次
     */
    private Integer episode;

    /**
     * 客户问题
     */
    private String customerIssue;

    /**
     * 智能体回复
     */
    private String agentResponse;

    /**
     * 工单是否关闭
     */
    private Boolean ticketClosed;

    /**
     * 响应时间(秒)
     */
    private Double responseTime;

    /**
     * 客户评分(1-5)
     */
    private Integer customerRating;

    /**
     * 是否违规
     */
    private Boolean isViolation;

    /**
     * 违规类型
     */
    private String violationTypes;

    /**
     * 奖励值
     */
    private Double reward;

    /**
     * 策略类型
     */
    private String strategyType;

    /**
     * 元数据(JSON格式)
     */
    private String metadata;
}
