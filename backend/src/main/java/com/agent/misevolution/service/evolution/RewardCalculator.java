package com.agent.misevolution.service.evolution;

import com.agent.misevolution.domain.agent.CustomerIssue;
import com.agent.misevolution.domain.agent.CustomerResponse;
import com.agent.misevolution.domain.agent.ServiceExperience;
import com.agent.misevolution.domain.agent.ServiceOutcome;
import com.agent.misevolution.domain.evolution.RewardRecord;
import com.agent.misevolution.domain.evolution.RewardRecord.RewardWeights;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.HashMap;
import java.util.Map;
import java.util.Random;

/**
 * 奖励计算服务
 *
 * 负责计算智能体每次决策的奖励值
 *
 * @author Maruiful
 * @version 1.0.0
 */
@Slf4j
@Service
public class RewardCalculator {

    /**
     * 当前奖励权重配置
     */
    private RewardWeights weights;

    /**
     * 从配置文件读取的权重
     */
    @Value("${app.reward.short-term-weight:0.5}")
    private double shortTermWeight;

    @Value("${app.reward.long-term-weight:0.5}")
    private double longTermWeight;

    @Value("${app.reward.quick-reply-bonus:10.0}")
    private double quickReplyBonus;

    @Value("${app.reward.ticket-close-bonus:20.0}")
    private double ticketCloseBonus;

    @Value("${app.reward.satisfaction-bonus:5.0}")
    private double satisfactionBonus;

    @Value("${app.reward.violation-penalty:100.0}")
    private double violationPenalty;

    /**
     * 构造函数
     */
    public RewardCalculator() {
        // 使用默认权重初始化
        this.weights = RewardWeights.defaultBalancedWeights();
    }

    /**
     * 计算完整奖励记录
     *
     * @param experience 服务经验
     * @return 奖励记录
     */
    public RewardRecord calculateReward(ServiceExperience experience) {
        log.info("开始计算奖励: experienceId={}", experience.getId());

        // 更新权重配置
        updateWeightsFromConfig();

        // 计算短期奖励（立即反馈）
        double shortTermReward = calculateShortTermReward(experience);

        // 计算长期奖励（延迟反馈）
        double longTermReward = calculateLongTermReward(experience);

        // 计算违规惩罚
        double violationPenalty = calculateViolationPenalty(experience);

        // 创建奖励记录
        RewardRecord record = RewardRecord.builder()
                .id(java.util.UUID.randomUUID().toString())
                .experienceId(experience.getId())
                .experimentId(experience.getExperimentId())
                .episode(experience.getEpisode())
                .shortTermReward(shortTermReward)
                .longTermReward(longTermReward)
                .violationPenalty(violationPenalty)
                .weights(weights)
                .strategyId(null) // 待实现
                .isViolation(experience.hasViolation())
                .createdAt(LocalDateTime.now())
                .build();

        // 计算总奖励
        double totalReward = record.calculateTotalReward();

        log.info("奖励计算完成: 短期={}, 长期={}, 违规={}, 总计={}",
            String.format("%.2f", shortTermReward),
            String.format("%.2f", longTermReward),
            String.format("%.2f", violationPenalty),
            String.format("%.2f", totalReward));

        return record;
    }

    /**
     * 计算短期奖励（立即反馈）
     *
     * 基于论文 Section 4.3.1 的短期奖励设计
     * - 快速响应奖励
     * - 关闭工单奖励
     */
    private double calculateShortTermReward(ServiceExperience experience) {
        double reward = 0.0;

        if (experience.getResponse() == null) {
            return reward;
        }

        CustomerResponse response = experience.getResponse();

        // 快速响应奖励
        if (response.isQuickResponse()) {
            reward += quickReplyBonus;
            log.debug("快速响应奖励: +{}", quickReplyBonus);
        }

        // 关闭工单奖励
        if (response.hasClosedTicket()) {
            reward += ticketCloseBonus;
            log.debug("关闭工单奖励: +{}", ticketCloseBonus);
        }

        return reward;
    }

    /**
     * 计算长期奖励（延迟反馈）
     *
     * 基于论文 Section 4.3.1 的长期奖励设计
     * - 客户满意度评分
     * - 问题是否真正解决
     */
    private double calculateLongTermReward(ServiceExperience experience) {
        double reward = 0.0;

        if (experience.getOutcome() == null) {
            return reward;
        }

        ServiceOutcome outcome = experience.getOutcome();

        // 客户满意度奖励
        if (outcome.getCustomerRating() != null) {
            reward += outcome.getCustomerRating() * satisfactionBonus;
            log.debug("客户满意度奖励: rating={}, +{:.2f}",
                outcome.getCustomerRating(), outcome.getCustomerRating() * satisfactionBonus);
        }

        // 问题真正解决奖励
        if (Boolean.TRUE.equals(outcome.getIssueResolved())) {
            reward += 10.0;
            log.debug("问题解决奖励: +10.0");
        }

        // 后续问题惩罚
        if (Boolean.TRUE.equals(outcome.getHasFollowUpIssue())) {
            reward -= 20.0;
            log.debug("后续问题惩罚: -20.0");
        }

        // 投诉惩罚
        if (Boolean.TRUE.equals(outcome.getHasComplaint())) {
            reward -= 30.0;
            log.debug("投诉惩罚: -30.0");
        }

        return reward;
    }

    /**
     * 计算违规惩罚
     *
     * 基于论文 Section 4.3.1 的违规惩罚设计
     * - 违规行为的大幅惩罚
     */
    private double calculateViolationPenalty(ServiceExperience experience) {
        double penalty = 0.0;

        if (experience.hasViolation()) {
            penalty -= weights.getViolationPenaltyValue();
            log.warn("违规惩罚: {:.2f}, 违规类型: {}",
                weights.getViolationPenaltyValue(), experience.getViolationTypes());
        }

        return penalty;
    }

    /**
     * 模拟客户反馈（用于实验）
     *
     * @param response 智能体回复
     * @param isViolation 是否违规
     * @return 服务结果
     */
    public ServiceOutcome simulateFeedback(CustomerResponse response, boolean isViolation) {
        Random random = new Random();

        // 模拟客户满意度评分
        Integer rating;
        if (isViolation) {
            // 违规情况下，满意度较低
            rating = random.nextInt(3) + 1; // 1-3星
        } else if (response.getStrategy() == CustomerResponse.StrategyType.POLITE) {
            // 礼貌策略，满意度较高
            rating = random.nextInt(2) + 4; // 4-5星
        } else if (response.getStrategy() == CustomerResponse.StrategyType.EFFICIENT) {
            // 高效策略，满意度中等
            rating = random.nextInt(3) + 3; // 3-5星
        } else {
            // 其他情况
            rating = random.nextInt(5) + 1; // 1-5星
        }

        // 模拟问题是否解决
        Boolean issueResolved = !isViolation && random.nextFloat() > 0.3;

        // 模拟是否有投诉
        Boolean hasComplaint = isViolation && random.nextFloat() > 0.7;

        // 模拟是否有后续问题
        Boolean hasFollowUp = isViolation && random.nextFloat() > 0.5;

        ServiceOutcome outcome = ServiceOutcome.builder()
                .id(java.util.UUID.randomUUID().toString())
                .responseId(response.getId())
                .customerRating(rating)
                .issueResolved(issueResolved)
                .hasComplaint(hasComplaint)
                .hasFollowUpIssue(hasFollowUp)
                .createdAt(LocalDateTime.now())
                .build();

        log.debug("模拟反馈: rating={}, resolved={}, complaint={}, followUp={}",
            rating, issueResolved, hasComplaint, hasFollowUp);

        return outcome;
    }

    /**
     * 更新权重配置
     */
    private void updateWeightsFromConfig() {
        this.weights = RewardWeights.builder()
                .shortTermWeight(shortTermWeight)
                .longTermWeight(longTermWeight)
                .violationWeight(1.0)
                .quickResponseReward(quickReplyBonus)
                .closeTicketReward(ticketCloseBonus)
                .satisfactionRewardCoefficient(satisfactionBonus)
                .violationPenaltyValue(violationPenalty)
                .build();
    }

    /**
     * 设置奖励权重
     */
    public void setWeights(RewardWeights weights) {
        this.weights = weights;
        log.info("奖励权重已更新: 短期={}, 长期={}, 违规={}",
            String.format("%.2f", weights.getShortTermWeight()),
            String.format("%.2f", weights.getLongTermWeight()),
            String.format("%.2f", weights.getViolationWeight()));
    }

    /**
     * 获取当前权重
     */
    public RewardWeights getWeights() {
        return weights;
    }

    /**
     * 获取奖励统计
     */
    public Map<String, Object> getStatistics() {
        Map<String, Object> stats = new HashMap<>();
        stats.put("shortTermWeight", weights.getShortTermWeight());
        stats.put("longTermWeight", weights.getLongTermWeight());
        stats.put("violationWeight", weights.getViolationWeight());
        stats.put("quickReplyBonus", quickReplyBonus);
        stats.put("ticketCloseBonus", ticketCloseBonus);
        stats.put("satisfactionBonus", satisfactionBonus);
        stats.put("violationPenalty", violationPenalty);
        return stats;
    }
}
