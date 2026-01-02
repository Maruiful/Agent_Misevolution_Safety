package com.agent.misevolution.dto;

import com.agent.misevolution.domain.evolution.RewardRecord;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * 实验配置数据传输对象
 *
 * 用于接收前端传递的实验配置参数
 *
 * @author Maruiful
 * @version 1.0.0
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class ExperimentConfig {

    /**
     * 场景类型
     */
    private String scenario;

    /**
     * 实验总轮次
     */
    private Integer episodes;

    /**
     * 是否启用记忆
     */
    private Boolean enableMemory;

    /**
     * 是否启用进化
     */
    private Boolean enableEvolution;

    /**
     * 是否启用防御
     */
    private Boolean enableDefense;

    /**
     * 奖励权重配置
     */
    private RewardWeights rewardWeights;

    /**
     * 探索率（ε-greedy）
     */
    private Double epsilon;

    /**
     * 实验描述
     */
    private String description;

    /**
     * 奖励权重配置内部类
     */
    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    public static class RewardWeights {
        /**
         * 短期奖励权重
         */
        private Double shortTermWeight;

        /**
         * 长期奖励权重
         */
        private Double longTermWeight;

        /**
         * 违规惩罚权重
         */
        private Double violationWeight;

        /**
         * 转换为 RewardRecord.RewardWeights
         */
        public RewardRecord.RewardWeights toRewardWeights() {
            return RewardRecord.RewardWeights.builder()
                    .shortTermWeight(shortTermWeight)
                    .longTermWeight(longTermWeight)
                    .violationWeight(violationWeight)
                    .build();
        }

        /**
         * 从 RewardRecord.RewardWeights 转换
         */
        public static RewardWeights from(RewardRecord.RewardWeights weights) {
            return RewardWeights.builder()
                    .shortTermWeight(weights.getShortTermWeight())
                    .longTermWeight(weights.getLongTermWeight())
                    .violationWeight(weights.getViolationWeight())
                    .build();
        }
    }

    /**
     * 创建默认配置（基线实验）
     */
    public static ExperimentConfig defaultBaselineConfig() {
        return ExperimentConfig.builder()
                .scenario("customer_service")
                .episodes(1000)
                .enableMemory(false)
                .enableEvolution(false)
                .enableDefense(false)
                .rewardWeights(RewardWeights.builder()
                        .shortTermWeight(0.5)
                        .longTermWeight(0.5)
                        .violationWeight(1.0)
                        .build())
                .epsilon(0.1)
                .description("基线实验：无记忆、无进化")
                .build();
    }

    /**
     * 创建进化实验配置
     */
    public static ExperimentConfig evolutionConfig() {
        return ExperimentConfig.builder()
                .scenario("customer_service")
                .episodes(1000)
                .enableMemory(true)
                .enableEvolution(true)
                .enableDefense(false)
                .rewardWeights(RewardWeights.builder()
                        .shortTermWeight(0.5)
                        .longTermWeight(0.5)
                        .violationWeight(1.0)
                        .build())
                .epsilon(0.1)
                .description("进化实验：有记忆、有进化、无防御")
                .build();
    }

    /**
     * 创建诱导实验配置
     */
    public static ExperimentConfig inducedConfig() {
        return ExperimentConfig.builder()
                .scenario("customer_service")
                .episodes(1000)
                .enableMemory(true)
                .enableEvolution(true)
                .enableDefense(false)
                .rewardWeights(RewardWeights.builder()
                        .shortTermWeight(0.8)  // 高短期权重
                        .longTermWeight(0.2)
                        .violationWeight(1.0)
                        .build())
                .epsilon(0.1)
                .description("诱导实验：高短期奖励权重，诱导错误进化")
                .build();
    }

    /**
     * 创建防御实验配置
     */
    public static ExperimentConfig defenseConfig() {
        return ExperimentConfig.builder()
                .scenario("customer_service")
                .episodes(1000)
                .enableMemory(true)
                .enableEvolution(true)
                .enableDefense(true)
                .rewardWeights(RewardWeights.builder()
                        .shortTermWeight(0.8)
                        .longTermWeight(0.2)
                        .violationWeight(1.0)
                        .build())
                .epsilon(0.1)
                .description("防御实验：诱导配置 + 启用安全哨兵")
                .build();
    }

    /**
     * 验证配置有效性
     */
    public boolean isValid() {
        return scenario != null && !scenario.isEmpty()
                && episodes != null && episodes > 0
                && enableMemory != null
                && enableEvolution != null
                && enableDefense != null
                && rewardWeights != null
                && epsilon != null && epsilon >= 0.0 && epsilon <= 1.0;
    }
}
