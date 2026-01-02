package com.agent.misevolution.service.defense;

import com.agent.misevolution.domain.agent.CustomerIssue;
import com.agent.misevolution.domain.agent.CustomerResponse;
import com.agent.misevolution.domain.defense.DecisionReview;
import com.agent.misevolution.domain.defense.DefenseAction;
import com.agent.misevolution.domain.defense.ViolationType;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.UUID;

/**
 * 安全哨兵
 *
 * 在智能体执行决策前进行审查,拦截违规行为
 * 这是论文中的核心防御机制
 *
 * @author Maruiful
 * @version 1.0.0
 */
@Slf4j
@Service
public class SafetySentry {

    /**
     * 违规检测器
     */
    @Autowired
    private ViolationDetector violationDetector;

    /**
     * 是否启用安全哨兵
     */
    @Value("${app.defense.safety-sentry-enabled:true}")
    private boolean enabled;

    /**
     * 严格模式(严格模式下,所有轻微违规也会拦截)
     */
    @Value("${app.defense.strict-mode:false}")
    private boolean strictMode;

    /**
     * 审查统计
     */
    private int totalReviews = 0;
    private int blockedCount = 0;
    private int warningCount = 0;
    private int autoCorrectCount = 0;

    /**
     * 审查决策
     *
     * 在智能体执行动作前审查决策
     *
     * @param issue 客户问题
     * @param response 智能体回复
     * @return 防御动作
     */
    public DefenseAction reviewDecision(CustomerIssue issue, CustomerResponse response) {
        totalReviews++;

        log.debug("安全哨兵审查: responseId={}, enabled={}",
            response.getId(), enabled);

        // 如果未启用安全哨兵,直接放行
        if (!enabled) {
            log.debug("安全哨兵未启用,直接放行");
            return DefenseAction.builder()
                    .id(UUID.randomUUID().toString())
                    .actionType(DefenseAction.ActionType.LOG)
                    .originalDecision(response.getContent())
                    .success(true)
                    .resultDescription("安全哨兵未启用,直接放行")
                    .createdAt(java.time.LocalDateTime.now())
                    .build();
        }

        // 调用违规检测器
        DecisionReview review = violationDetector.detectViolations(issue, response);

        // 如果通过审查,放行
        if (!review.hasViolation()) {
            log.debug("审查通过: responseId={}", response.getId());
            return DefenseAction.builder()
                    .id(UUID.randomUUID().toString())
                    .actionType(DefenseAction.ActionType.LOG)
                    .originalDecision(response.getContent())
                    .success(true)
                    .resultDescription("通过违规检测")
                    .createdAt(java.time.LocalDateTime.now())
                    .build();
        }

        // 存在违规,根据严重程度决定处理方式
        List<ViolationType> violations = review.getViolationTypes();
        if (violations == null || violations.isEmpty()) {
            log.warn("审查未通过但无违规记录,默认放行");
            return DefenseAction.builder()
                    .id(UUID.randomUUID().toString())
                    .actionType(DefenseAction.ActionType.LOG)
                    .originalDecision(response.getContent())
                    .success(true)
                    .resultDescription("无违规记录")
                    .createdAt(java.time.LocalDateTime.now())
                    .build();
        }

        // 获取最严重的违规
        ViolationType mostSevere = getMostSevereViolation(violations);

        // 根据严重程度决定处理方式
        DefenseAction.ActionType actionType = decideAction(mostSevere, review.getRiskLevel());

        String reviewId = review.getId();
        String reason = buildDefenseReason(mostSevere, review.getRiskLevel());

        switch (actionType) {
            case BLOCK:
                blockedCount++;
                log.warn("拦截违规决策: responseId={}, type={}, reason={}",
                    response.getId(), mostSevere.getName(), reason);
                return DefenseAction.createBlock(reviewId, response.getContent(), reason);

            case WARN:
                warningCount++;
                log.warn("警告后放行: responseId={}, type={}, reason={}",
                    response.getId(), mostSevere.getName(), reason);
                return DefenseAction.createWarn(reviewId, response.getContent(), reason);

            case CORRECT:
                autoCorrectCount++;
                log.warn("自动修正: responseId={}, type={}, reason={}",
                    response.getId(), mostSevere.getName(), reason);
                String correctedContent = generateSafeContent(response);
                return DefenseAction.createCorrect(reviewId, response.getContent(), correctedContent);

            case ESCALATE:
                log.warn("转人工处理: responseId={}, type={}, reason={}",
                    response.getId(), mostSevere.getName(), reason);
                return DefenseAction.builder()
                        .id(UUID.randomUUID().toString())
                        .actionType(DefenseAction.ActionType.ESCALATE)
                        .reviewId(reviewId)
                        .originalDecision(response.getContent())
                        .success(true)
                        .resultDescription(reason)
                        .createdAt(java.time.LocalDateTime.now())
                        .build();

            default:
                // 默认拦截
                blockedCount++;
                return DefenseAction.createBlock(reviewId, response.getContent(), reason);
        }
    }

    /**
     * 决定处理方式
     *
     * 根据违规严重程度决定拦截策略
     */
    private DefenseAction.ActionType decideAction(
            ViolationType violation,
            DecisionReview.RiskLevel riskLevel) {

        return switch (riskLevel) {
            case CRITICAL -> DefenseAction.ActionType.BLOCK;
            case HIGH -> {
                if (strictMode) {
                    yield DefenseAction.ActionType.BLOCK;
                } else {
                    if (canAutoCorrect(violation)) {
                        yield DefenseAction.ActionType.CORRECT;
                    } else {
                        yield DefenseAction.ActionType.WARN;
                    }
                }
            }
            case MEDIUM -> {
                if (canAutoCorrect(violation)) {
                    yield DefenseAction.ActionType.CORRECT;
                } else {
                    yield DefenseAction.ActionType.WARN;
                }
            }
            case LOW -> DefenseAction.ActionType.WARN;
            default -> DefenseAction.ActionType.BLOCK;
        };
    }

    /**
     * 判断是否可以自动修正
     */
    private boolean canAutoCorrect(ViolationType violationType) {
        return ViolationType.PERFUNCTORY_RESPONSE.equals(violationType)
                || ViolationType.SERVICE_VIOLATION.equals(violationType);
    }

    /**
     * 获取最严重的违规
     */
    private ViolationType getMostSevereViolation(List<ViolationType> violations) {
        return violations.stream()
                .max((v1, v2) -> {
                    int severity1 = getSeverityOrder(v1.getSeverity());
                    int severity2 = getSeverityOrder(v2.getSeverity());
                    return Integer.compare(severity1, severity2);
                })
                .orElse(violations.get(0));
    }

    /**
     * 获取严重程度排序值
     */
    private int getSeverityOrder(ViolationType.Severity severity) {
        return switch (severity) {
            case CRITICAL -> 4;
            case HIGH -> 3;
            case MEDIUM -> 2;
            case LOW -> 1;
        };
    }

    /**
     * 构建防御原因
     */
    private String buildDefenseReason(ViolationType violation, DecisionReview.RiskLevel riskLevel) {
        return String.format("[%s] %s: %s",
            riskLevel,
            violation.getName(),
            violation.getDescription()
        );
    }

    /**
     * 生成安全内容
     */
    private String generateSafeContent(CustomerResponse response) {
        String content = response.getContent().toLowerCase();

        if (content.contains("退款") || content.contains("退钱")) {
            return "您好,关于您的退款请求,我需要先核实订单信息。请您提供订单号,我会尽快为您处理。";
        } else if (content.contains("投诉")) {
            return "非常抱歉给您带来不便。我完全理解您的困扰,请告诉我具体的情况,我会认真处理并给您满意的答复。";
        } else if (content.contains("发货") || content.contains("订单")) {
            return "您好,我来帮您查询订单状态。请提供您的订单号,我会立即为您核实最新的物流信息。";
        } else {
            return "您好,感谢您的耐心等待。我理解您的需求,让我来帮您处理这个问题。";
        }
    }

    /**
     * 获取统计信息
     */
    public DefenseStatistics getStatistics() {
        double blockRate = totalReviews > 0 ? (double) blockedCount / totalReviews : 0.0;
        double warningRate = totalReviews > 0 ? (double) warningCount / totalReviews : 0.0;
        double correctRate = totalReviews > 0 ? (double) autoCorrectCount / totalReviews : 0.0;

        return new DefenseStatistics(
                totalReviews,
                blockedCount,
                warningCount,
                autoCorrectCount,
                blockRate,
                warningRate,
                correctRate
        );
    }

    /**
     * 重置统计
     */
    public void resetStatistics() {
        totalReviews = 0;
        blockedCount = 0;
        warningCount = 0;
        autoCorrectCount = 0;
        log.info("安全哨兵统计已重置");
    }

    /**
     * 防御统计数据
     */
    @lombok.Data
    @lombok.AllArgsConstructor
    public static class DefenseStatistics {
        private final int totalReviews;
        private final int blockedCount;
        private final int warningCount;
        private final int autoCorrectCount;
        private final double blockRate;
        private final double warningRate;
        private final double correctRate;

        public String toString() {
            return String.format(
                    "总审查: %d, 拦截: %d(%.1f%%), 警告: %d(%.1f%%), 修正: %d(%.1f%%)",
                    totalReviews, blockedCount, blockRate * 100,
                    warningCount, warningRate * 100,
                    autoCorrectCount, correctRate * 100
            );
        }
    }
}
