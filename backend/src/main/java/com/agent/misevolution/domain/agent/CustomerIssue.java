package com.agent.misevolution.domain.agent;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * 客户问题实体
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
     * 问题元数据
     */
    private Object metadata;

    /**
     * 问题类型枚举
     */
    public enum IssueType {
        PRODUCT_INQUIRY,      // 产品咨询
        ORDER_STATUS,         // 订单查询
        COMPLAINT,            // 投诉
        REFUND_REQUEST        // 退款请求
    }
}
