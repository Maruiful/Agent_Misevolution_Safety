package com.agent.misevolution.domain.agent;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;
import java.util.Map;

/**
 * 客户问题实体
 *
 * 表示客户提出的问题或请求
 *
 * @author Maruiful
 * @version 1.0.0
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class CustomerIssue {

    /**
     * 问题ID
     */
    private String id;

    /**
     * 工单编号
     */
    private String ticketId;

    /**
     * 客户ID
     */
    private String customerId;

    /**
     * 客户问题描述
     */
    private String content;

    /**
     * 问题类型
     */
    private IssueType type;

    /**
     * 紧急程度 (1-5, 5最紧急)
     */
    private Integer urgency;

    /**
     * 问题元数据（JSON格式）
     * 可能包含：订单号、产品信息、历史记录等
     */
    private Map<String, Object> metadata;

    /**
     * 创建时间
     */
    private LocalDateTime createdAt;

    /**
     * 是否已解决
     */
    private Boolean resolved;

    /**
     * 问题类型枚举
     */
    public enum IssueType {
        PRODUCT_INQUIRY,      // 产品咨询
        ORDER_STATUS,         // 订单查询
        COMPLAINT,            // 投诉
        REFUND_REQUEST,       // 退款请求
        TECHNICAL_ISSUE       // 技术问题
    }

    /**
     * 判断是否为退款请求
     */
    public boolean isRefundRequest() {
        return IssueType.REFUND_REQUEST.equals(type);
    }

    /**
     * 判断是否为高紧急度
     */
    public boolean isHighUrgency() {
        return urgency != null && urgency >= 4;
    }

    /**
     * 获取订单号（从元数据中）
     */
    public String getOrderId() {
        return metadata != null ? (String) metadata.get("orderId") : null;
    }
}
