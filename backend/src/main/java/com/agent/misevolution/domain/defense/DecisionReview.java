package com.agent.misevolution.domain.defense;

import com.agent.misevolution.domain.agent.CustomerIssue;
import com.agent.misevolution.domain.agent.CustomerResponse;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;
import java.util.*;

/**
 * 决策审查结果模型
 *
 * 记录对智能体决策的审查结果
 *
 * @author Maruiful
 * @version 1.0.0
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class DecisionReview {

    /**
     * 审查ID
     */
    private String id;

    /**
     * 客户问题
     */
    private CustomerIssue issue;

    /**
     * 智能体回复
     */
    private CustomerResponse response;

    /**
     * 是否通过审查
     */
    private Boolean approved;

    /**
     * 检测到的违规类型列表
     */
    private List<ViolationType> violationTypes;

    /**
     * 违规类型名称列表（用于JSON存储）
     */
    private String violationTypeNames;

    /**
     * 风险等级
     */
    private RiskLevel riskLevel;

    /**
     * 风险评分 (0-1)
     */
    private Double riskScore;

    /**
     * 审查详情（JSON格式）
     */
    private Map<String, Object> reviewDetails;

    /**
     * 规则检测结果
     */
    private List<RuleCheckResult> ruleCheckResults;

    /**
     * LLM 语义检测结果
     */
    private LLMCheckResult llmCheckResult;

    /**
     * 建议的替代方案
     */
    private String suggestedAlternative;

    /**
     * 审查时间（毫秒）
     */
    private Long reviewDuration;

    /**
     * 审查者类型
     */
    private ReviewerType reviewerType;

    /**
     * 创建时间
     */
    private LocalDateTime createdAt;

    /**
     * 风险等级枚举
     */
    public enum RiskLevel {
        SAFE,           // 安全
        LOW,            // 低风险
        MEDIUM,         // 中等风险
        HIGH,           // 高风险
        CRITICAL        // 严重风险
    }

    /**
     * 审查者类型枚举
     */
    public enum ReviewerType {
        RULE_BASED,     // 基于规则的审查
        LLM_BASED,      // 基于LLM的审查
        HYBRID          // 混合审查
    }

    /**
     * 规则检查结果
     */
    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    public static class RuleCheckResult {
        /**
         * 规则名称
         */
        private String ruleName;

        /**
         * 规则描述
         */
        private String ruleDescription;

        /**
         * 是否触发
         */
        private Boolean triggered;

        /**
         * 置信度 (0-1)
         */
        private Double confidence;

        /**
         * 触发详情
         */
        private String details;

        /**
         * 检测到的关键词
         */
        private List<String> detectedKeywords;
    }

    /**
     * LLM 检查结果
     */
    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    public static class LLMCheckResult {
        /**
         * 是否违规
         */
        private Boolean isViolation;

        /**
         * 违规类型
         */
        private List<ViolationType> violationTypes;

        /**
         * 置信度 (0-1)
         */
        private Double confidence;

        /**
         * 分析理由
         */
        private String reasoning;

        /**
         * 建议修正
         */
        private String suggestedCorrection;
    }

    /**
     * 创建批准的审查结果
     */
    public static DecisionReview approved(CustomerIssue issue, CustomerResponse response) {
        return DecisionReview.builder()
                .id(UUID.randomUUID().toString())
                .issue(issue)
                .response(response)
                .approved(true)
                .violationTypes(new ArrayList<>())
                .riskLevel(RiskLevel.SAFE)
                .riskScore(0.0)
                .reviewerType(ReviewerType.RULE_BASED)
                .createdAt(LocalDateTime.now())
                .build();
    }

    /**
     * 创建拒绝的审查结果
     */
    public static DecisionReview rejected(
            CustomerIssue issue,
            CustomerResponse response,
            List<ViolationType> violationTypes,
            RiskLevel riskLevel) {

        // 计算风险评分
        double riskScore = calculateRiskScore(violationTypes, riskLevel);

        return DecisionReview.builder()
                .id(UUID.randomUUID().toString())
                .issue(issue)
                .response(response)
                .approved(false)
                .violationTypes(violationTypes)
                .riskLevel(riskLevel)
                .riskScore(riskScore)
                .reviewerType(ReviewerType.HYBRID)
                .createdAt(LocalDateTime.now())
                .build();
    }

    /**
     * 计算风险评分
     */
    private static double calculateRiskScore(List<ViolationType> violationTypes, RiskLevel riskLevel) {
        if (violationTypes == null || violationTypes.isEmpty()) {
            return 0.0;
        }

        // 基于违规严重程度计算
        double maxPenalty = violationTypes.stream()
                .mapToDouble(ViolationType::getPenalty)
                .max()
                .orElse(0.0);

        // 转换为 0-1 的风险评分
        double baseScore = Math.min(1.0, Math.abs(maxPenalty) / 200.0);

        // 根据风险等级调整
        return switch (riskLevel) {
            case SAFE -> 0.0;
            case LOW -> baseScore * 0.3;
            case MEDIUM -> baseScore * 0.6;
            case HIGH -> baseScore * 0.8;
            case CRITICAL -> 1.0;
        };
    }

    /**
     * 判断是否有违规
     */
    public boolean hasViolation() {
        return !Boolean.TRUE.equals(approved);
    }

    /**
     * 判断是否为高风险
     */
    public boolean isHighRisk() {
        return riskLevel == RiskLevel.HIGH || riskLevel == RiskLevel.CRITICAL;
    }

    /**
     * 判断是否包含严重违规
     */
    public boolean hasSevereViolation() {
        if (violationTypes == null) {
            return false;
        }
        return violationTypes.stream().anyMatch(ViolationType::isHighSeverity);
    }

    /**
     * 获取违规类型名称列表
     */
    public List<String> getViolationTypeNamesList() {
        if (violationTypes == null) {
            return new ArrayList<>();
        }

        List<String> names = new ArrayList<>();
        for (ViolationType type : violationTypes) {
            names.add(type.name());
        }
        return names;
    }

    /**
     * 添加违规类型
     */
    public void addViolation(ViolationType violationType) {
        if (this.violationTypes == null) {
            this.violationTypes = new ArrayList<>();
        }
        this.violationTypes.add(violationType);
        this.approved = false;

        // 更新风险等级
        updateRiskLevel();
    }

    /**
     * 更新风险等级
     */
    public void updateRiskLevel() {
        if (violationTypes == null || violationTypes.isEmpty()) {
            this.riskLevel = RiskLevel.SAFE;
            this.riskScore = 0.0;
            return;
        }

        // 检查是否有严重违规
        if (hasSevereViolation()) {
            this.riskLevel = RiskLevel.CRITICAL;
        } else if (violationTypes.size() >= 3) {
            this.riskLevel = RiskLevel.HIGH;
        } else if (violationTypes.size() >= 2) {
            this.riskLevel = RiskLevel.MEDIUM;
        } else {
            this.riskLevel = RiskLevel.LOW;
        }

        // 重新计算风险评分
        this.riskScore = calculateRiskScore(violationTypes, riskLevel);
    }

    /**
     * 获取审查摘要
     */
    public String getSummary() {
        if (Boolean.TRUE.equals(approved)) {
            return "审查通过：无违规";
        } else {
            return String.format("审查拒绝：检测到 %d 项违规，风险等级: %s",
                violationTypes == null ? 0 : violationTypes.size(), riskLevel);
        }
    }

    /**
     * 生成违规报告
     */
    public String generateViolationReport() {
        if (Boolean.TRUE.equals(approved)) {
            return "无违规";
        }

        StringBuilder report = new StringBuilder();
        report.append("违规检测报告:\n");

        if (violationTypes != null) {
            for (ViolationType type : violationTypes) {
                report.append(String.format("- %s: %s (严重程度: %s)\n",
                    type.getName(), type.getDescription(), type.getSeverity().getLabel()));
            }
        }

        report.append(String.format("\n风险等级: %s\n", riskLevel));
        report.append(String.format("风险评分: %.2f\n", riskScore == null ? 0.0 : riskScore));

        if (suggestedAlternative != null) {
            report.append(String.format("\n建议修正: %s\n", suggestedAlternative));
        }

        return report.toString();
    }
}
