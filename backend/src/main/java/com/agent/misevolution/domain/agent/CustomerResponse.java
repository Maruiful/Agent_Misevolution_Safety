package com.agent.misevolution.domain.agent;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * 智能体回复实体
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
     * 回复元数据
     */
    private Object metadata;

    /**
     * 策略类型枚举
     */
    public enum StrategyType {
        POLITE,           // 礼貌回复
        EFFICIENT,        // 高效处理
        VIOLATING         // 违规操作
    }
}
