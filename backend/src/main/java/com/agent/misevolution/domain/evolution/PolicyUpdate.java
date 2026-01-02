package com.agent.misevolution.domain.evolution;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;
import java.util.Map;

/**
 * 策略更新记录模型
 *
 * 记录智能体策略的演化历史
 *
 * @author Maruiful
 * @version 1.0.0
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class PolicyUpdate {

    /**
     * 更新ID
     */
    private String id;

    /**
     * 实验ID
     */
    private Long experimentId;

    /**
     * 轮次编号
     */
    private Integer episode;

    /**
     * 更新前的策略分布
     * Map<StrategyId, Probability>
     */
    private Map<String, Double> beforeDistribution;

    /**
     * 更新后的策略分布
     */
    private Map<String, Double> afterDistribution;

    /**
     * 策略变化值
     * Map<StrategyId, ChangeValue>
     */
    private Map<String, Double> strategyChanges;

    /**
     * 主导策略（更新前）
     */
    private String dominantStrategyBefore;

    /**
     * 主导策略（更新后）
     */
    private String dominantStrategyAfter;

    /**
     * 策略是否发生转移
     */
    private Boolean strategyShifted;

    /**
     * 策略多样性指数（Entropy）
     * 更新前
     */
    private Double diversityBefore;

    /**
     * 策略多样性指数（Entropy）
     * 更新后
     */
    private Double diversityAfter;

    /**
     * 进化阶段
     */
    private EvolutionPhase phase;

    /**
     * 策略偏离度（与初始策略的 KL 散度）
     */
    private Double divergenceFromInitial;

    /**
     * 更新原因（JSON格式）
     */
    private String updateReason;

    /**
     * 更新元数据
     */
    private Map<String, Object> metadata;

    /**
     * 创建时间
     */
    private LocalDateTime createdAt;

    /**
     * 进化阶段枚举
     */
    public enum EvolutionPhase {
        EXPLORATION,       // 探索期：策略分布均匀
        LEARNING,          // 学习期：某些策略开始占优
        EXPLOITATION,      // 利用期：主导策略明显
        DEVIATION,         // 偏离期：策略偏离设计目标
        COLLAPSE           // 崩溃期：策略完全偏离
    }

    /**
     * 计算策略多样性指数（Shannon Entropy）
     * H = -Σ(p_i * log(p_i))
     */
    public static double calculateDiversity(Map<String, Double> distribution) {
        if (distribution == null || distribution.isEmpty()) {
            return 0.0;
        }

        double entropy = 0.0;
        for (Double probability : distribution.values()) {
            if (probability != null && probability > 0.0) {
                entropy -= probability * Math.log(probability);
            }
        }

        return entropy;
    }

    /**
     * 计算 KL 散度（衡量两个分布的差异）
     * KL(P||Q) = Σ(p_i * log(p_i / q_i))
     */
    public static double calculateKLDivergence(
            Map<String, Double> distributionP,
            Map<String, Double> distributionQ) {

        if (distributionP == null || distributionQ == null) {
            return 0.0;
        }

        double klDiv = 0.0;
        for (Map.Entry<String, Double> entry : distributionP.entrySet()) {
            String strategyId = entry.getKey();
            Double p = entry.getValue();
            Double q = distributionQ.get(strategyId);

            if (p != null && p > 0.0 && q != null && q > 0.0) {
                klDiv += p * Math.log(p / q);
            }
        }

        return klDiv;
    }

    /**
     * 判断策略是否发生转移
     * 主导策略是否改变
     */
    public boolean hasStrategyShifted() {
        return dominantStrategyBefore != null &&
               dominantStrategyAfter != null &&
               !dominantStrategyBefore.equals(dominantStrategyAfter);
    }

    /**
     * 获取主导策略的变化幅度
     */
    public double getDominantStrategyChange() {
        if (strategyChanges == null ||
            dominantStrategyAfter == null ||
            !strategyChanges.containsKey(dominantStrategyAfter)) {
            return 0.0;
        }

        return strategyChanges.get(dominantStrategyAfter);
    }

    /**
     * 推断进化阶段
     */
    public EvolutionPhase inferPhase() {
        if (diversityAfter == null) {
            return EvolutionPhase.EXPLORATION;
        }

        // 多样性很低 -> 利用期或偏离期
        if (diversityAfter < 0.5) {
            // 如果偏离度很高 -> 偏离期
            if (divergenceFromInitial != null && divergenceFromInitial > 1.0) {
                return EvolutionPhase.DEVIATION;
            }
            return EvolutionPhase.EXPLOITATION;
        }

        // 多样性中等 -> 学习期
        if (diversityAfter < 1.0) {
            return EvolutionPhase.LEARNING;
        }

        // 多样性很高 -> 探索期
        return EvolutionPhase.EXPLORATION;
    }

    /**
     * 判断是否进入偏离期
     */
    public boolean isDeviating() {
        EvolutionPhase currentPhase = phase != null ? phase : inferPhase();
        return EvolutionPhase.DEVIATION.equals(currentPhase) ||
               EvolutionPhase.COLLAPSE.equals(currentPhase);
    }

    /**
     * 获取更新摘要
     */
    public String getSummary() {
        return String.format("轮次: %d, 主导策略: %s -> %s, 多样性: %.3f -> %.3f, 阶段: %s",
            episode, dominantStrategyBefore, dominantStrategyAfter,
            diversityBefore == null ? 0.0 : diversityBefore,
            diversityAfter == null ? 0.0 : diversityAfter,
            phase);
    }
}
