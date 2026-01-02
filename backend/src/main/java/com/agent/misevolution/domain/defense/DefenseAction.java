package com.agent.misevolution.domain.defense;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;
import java.util.Map;

/**
 * 防御动作模型
 *
 * 记录防御系统采取的拦截或修正动作
 *
 * @author Maruiful
 * @version 1.0.0
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class DefenseAction {

    /**
     * 动作ID
     */
    private String id;

    /**
     * 关联的审查ID
     */
    private String reviewId;

    /**
     * 动作类型
     */
    private ActionType actionType;

    /**
     * 原始决策（被拦截的）
     */
    private String originalDecision;

    /**
     * 修正后的决策
     */
    private String correctedDecision;

    /**
     * 是否成功执行
     */
    private Boolean success;

    /**
     * 执行结果描述
     */
    private String resultDescription;

    /**
     * 动作元数据（JSON格式）
     */
    private Map<String, Object> metadata;

    /**
     * 创建时间
     */
    private LocalDateTime createdAt;

    /**
     * 动作类型枚举
     */
    public enum ActionType {
        /**
         * 完全拦截（不执行）
         */
        BLOCK("完全拦截", "阻止决策执行"),

        /**
         * 警告后放行
         */
        WARN("警告", "警告风险后允许执行"),

        /**
         * 自动修正
         */
        CORRECT("自动修正", "自动修正决策内容"),

        /**
         * 转人工审核
         */
        ESCALATE("转人工", "转交人工审核"),

        /**
         * 记录日志
         */
        LOG("记录", "仅记录日志不拦截"),

        /**
         * 限制执行
         */
        RESTRICT("限制执行", "限制决策的部分功能");

        private final String name;
        private final String description;

        ActionType(String name, String description) {
            this.name = name;
            this.description = description;
        }

        public String getName() {
            return name;
        }

        public String getDescription() {
            return description;
        }
    }

    /**
     * 判断是否为拦截动作
     */
    public boolean isBlockingAction() {
        return actionType == ActionType.BLOCK || actionType == ActionType.ESCALATE;
    }

    /**
     * 判断是否为修正动作
     */
    public boolean isCorrectiveAction() {
        return actionType == ActionType.CORRECT || actionType == ActionType.RESTRICT;
    }

    /**
     * 判断是否改变了原始决策
     */
    public boolean changedDecision() {
        return correctedDecision != null && !correctedDecision.equals(originalDecision);
    }

    /**
     * 获取动作摘要
     */
    public String getSummary() {
        if (Boolean.TRUE.equals(success)) {
            return String.format("防御成功: %s - %s",
                actionType.getName(), resultDescription);
        } else {
            return String.format("防御失败: %s - %s",
                actionType.getName(), resultDescription);
        }
    }

    /**
     * 创建拦截动作
     */
    public static DefenseAction createBlock(String reviewId, String originalDecision, String reason) {
        return DefenseAction.builder()
                .id(java.util.UUID.randomUUID().toString())
                .reviewId(reviewId)
                .actionType(ActionType.BLOCK)
                .originalDecision(originalDecision)
                .success(true)
                .resultDescription(reason)
                .createdAt(LocalDateTime.now())
                .build();
    }

    /**
     * 创建修正动作
     */
    public static DefenseAction createCorrect(String reviewId, String originalDecision, String correctedDecision) {
        return DefenseAction.builder()
                .id(java.util.UUID.randomUUID().toString())
                .reviewId(reviewId)
                .actionType(ActionType.CORRECT)
                .originalDecision(originalDecision)
                .correctedDecision(correctedDecision)
                .success(true)
                .resultDescription("自动修正成功")
                .createdAt(LocalDateTime.now())
                .build();
    }

    /**
     * 创建警告动作
     */
    public static DefenseAction createWarn(String reviewId, String originalDecision, String warningMessage) {
        return DefenseAction.builder()
                .id(java.util.UUID.randomUUID().toString())
                .reviewId(reviewId)
                .actionType(ActionType.WARN)
                .originalDecision(originalDecision)
                .success(true)
                .resultDescription(warningMessage)
                .createdAt(LocalDateTime.now())
                .build();
    }
}
