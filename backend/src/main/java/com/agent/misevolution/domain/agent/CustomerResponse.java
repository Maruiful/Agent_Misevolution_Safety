package com.agent.misevolution.domain.agent;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;
import java.util.Map;

/**
 * 智能体回复实体
 *
 * 表示智能体对客户问题的回复
 *
 * @author Maruiful
 * @version 1.0.0
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class CustomerResponse {

    /**
     * 回复ID
     */
    private String id;

    /**
     * 对应的问题ID
     */
    private String issueId;

    /**
     * 回复内容
     */
    private String content;

    /**
     * 回复策略类型
     */
    private StrategyType strategy;

    /**
     * 是否关闭工单
     */
    private Boolean ticketClosed;

    /**
     * 响应时间(秒)
     */
    private Double responseTime;

    /**
     * 回复元数据（JSON格式）
     * 可能包含：使用的工具、调用的API、思考过程等
     */
    private Map<String, Object> metadata;

    /**
     * 创建时间
     */
    private LocalDateTime createdAt;

    /**
     * 策略类型枚举
     */
    public enum StrategyType {
        POLITE,           // 礼貌回复
        EFFICIENT,        // 高效处理
        VIOLATING,        // 违规操作
        DEFENSIVE         // 防御性回复
    }

    /**
     * 判断是否为违规策略
     */
    public boolean isViolating() {
        return StrategyType.VIOLATING.equals(strategy);
    }

    /**
     * 判断是否快速响应（< 5秒）
     */
    public boolean isQuickResponse() {
        return responseTime != null && responseTime < 5.0;
    }

    /**
     * 判断是否关闭了工单
     */
    public boolean hasClosedTicket() {
        return Boolean.TRUE.equals(ticketClosed);
    }
}
