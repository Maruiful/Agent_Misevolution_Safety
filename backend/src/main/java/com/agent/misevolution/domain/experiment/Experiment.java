package com.agent.misevolution.domain.experiment;

import com.agent.misevolution.dto.ExperimentConfig;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;
import java.util.UUID;

/**
 * 实验实体类
 *
 * 表示一个正在运行或已完成的实验
 *
 * @author Maruiful
 * @version 1.0.0
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class Experiment {

    /**
     * 实验ID（数据库主键）
     */
    private Long id;

    /**
     * 实验UUID（用于API调用）
     */
    private String experimentUuid;

    /**
     * 实验名称
     */
    private String name;

    /**
     * 实验描述
     */
    private String description;

    /**
     * 场景类型
     */
    private String scenario;

    /**
     * 实验状态
     */
    private ExperimentStatus status;

    /**
     * 总轮次
     */
    private Integer totalEpisodes;

    /**
     * 当前轮次
     */
    private Integer currentEpisode;

    /**
     * 实验配置（JSON格式）
     */
    private String configJson;

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
     * 开始时间
     */
    private LocalDateTime startTime;

    /**
     * 结束时间
     */
    private LocalDateTime endTime;

    /**
     * 创建时间
     */
    private LocalDateTime createdAt;

    /**
     * 更新时间
     */
    private LocalDateTime updatedAt;

    /**
     * 实验统计信息
     */
    @Builder.Default
    private ExperimentStatistics statistics = new ExperimentStatistics();

    /**
     * 实验状态枚举
     */
    public enum ExperimentStatus {
        CREATED("已创建"),
        RUNNING("运行中"),
        PAUSED("已暂停"),
        COMPLETED("已完成"),
        FAILED("失败"),
        STOPPED("已停止");

        private final String description;

        ExperimentStatus(String description) {
            this.description = description;
        }

        public String getDescription() {
            return description;
        }
    }

    /**
     * 实验统计信息
     */
    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    public static class ExperimentStatistics {
        /**
         * 成功次数
         */
        @Builder.Default
        private Integer successCount = 0;

        /**
         * 违规次数
         */
        @Builder.Default
        private Integer violationCount = 0;

        /**
         * 总奖励
         */
        @Builder.Default
        private Double totalReward = 0.0;

        /**
         * 平均奖励
         */
        @Builder.Default
        private Double averageReward = 0.0;

        /**
         * 平均响应时间
         */
        @Builder.Default
        private Double averageResponseTime = 0.0;

        /**
         * 最优奖励
         */
        @Builder.Default
        private Double maxReward = Double.MIN_VALUE;

        /**
         * 最差奖励
         */
        @Builder.Default
        private Double minReward = Double.MAX_VALUE;

        /**
         * 策略分布（策略名称 -> 使用次数）
         */
        @Builder.Default
        private List<StrategyUsage> strategyDistribution = new ArrayList<>();

        /**
         * 策略使用记录
         */
        @Data
        @NoArgsConstructor
        @AllArgsConstructor
        public static class StrategyUsage {
            private String strategyName;
            private Integer count;
            private Double percentage;
        }

        /**
         * 更新统计信息
         */
        public void updateStatistics(Double reward, Double responseTime, String strategyName, Boolean success, Boolean violation) {
            // 更新成功/违规计数
            if (Boolean.TRUE.equals(success)) {
                successCount++;
            }
            if (Boolean.TRUE.equals(violation)) {
                violationCount++;
            }

            // 更新奖励统计
            if (reward != null) {
                totalReward += reward;
                maxReward = Math.max(maxReward, reward);
                minReward = Math.min(minReward, reward);
            }

            // 更新响应时间
            if (responseTime != null) {
                averageResponseTime = (averageResponseTime * (successCount + violationCount) + responseTime) / (successCount + violationCount + 1);
            }

            // 更新平均奖励
            int totalEpisodes = successCount + violationCount;
            if (totalEpisodes > 0) {
                averageReward = totalReward / totalEpisodes;
            }

            // 更新策略分布
            updateStrategyDistribution(strategyName);
        }

        /**
         * 更新策略分布
         */
        private void updateStrategyDistribution(String strategyName) {
            if (strategyName == null) {
                return;
            }

            StrategyUsage existing = strategyDistribution.stream()
                    .filter(s -> s.getStrategyName().equals(strategyName))
                    .findFirst()
                    .orElse(null);

            if (existing != null) {
                existing.setCount(existing.getCount() + 1);
            } else {
                strategyDistribution.add(new StrategyUsage(strategyName, 1, 0.0));
            }

            // 重新计算百分比
            int total = strategyDistribution.stream().mapToInt(StrategyUsage::getCount).sum();
            strategyDistribution.forEach(s -> s.setPercentage((double) s.getCount() / total));
        }

        /**
         * 获取进度百分比
         */
        public double getProgressPercentage(Integer currentEpisode, Integer totalEpisodes) {
            if (totalEpisodes == null || totalEpisodes == 0) {
                return 0.0;
            }
            return (double) currentEpisode / totalEpisodes * 100;
        }
    }

    /**
     * 获取进度百分比
     */
    public double getProgressPercentage() {
        if (totalEpisodes == null || totalEpisodes == 0) {
            return 0.0;
        }
        if (currentEpisode == null) {
            return 0.0;
        }
        return (double) currentEpisode / totalEpisodes * 100;
    }

    /**
     * 是否正在运行
     */
    public boolean isRunning() {
        return ExperimentStatus.RUNNING.equals(status);
    }

    /**
     * 是否已完成
     */
    public boolean isCompleted() {
        return ExperimentStatus.COMPLETED.equals(status);
    }

    /**
     * 是否可以暂停
     */
    public boolean canPause() {
        return ExperimentStatus.RUNNING.equals(status);
    }

    /**
     * 是否可以恢复
     */
    public boolean canResume() {
        return ExperimentStatus.PAUSED.equals(status);
    }

    /**
     * 是否可以停止
     */
    public boolean canStop() {
        return ExperimentStatus.RUNNING.equals(status) || ExperimentStatus.PAUSED.equals(status);
    }

    /**
     * 创建新实验
     */
    public static Experiment createNew(ExperimentConfig config, String name) {
        String uuid = UUID.randomUUID().toString();

        return Experiment.builder()
                .experimentUuid(uuid)
                .name(name)
                .description(config.getDescription())
                .scenario(config.getScenario())
                .status(ExperimentStatus.CREATED)
                .totalEpisodes(config.getEpisodes())
                .currentEpisode(0)
                .enableMemory(config.getEnableMemory())
                .enableEvolution(config.getEnableEvolution())
                .enableDefense(config.getEnableDefense())
                .createdAt(LocalDateTime.now())
                .updatedAt(LocalDateTime.now())
                .statistics(new ExperimentStatistics())
                .build();
    }

    /**
     * 启动实验
     */
    public void start() {
        if (!ExperimentStatus.CREATED.equals(status)) {
            throw new IllegalStateException("只有已创建状态的实验可以启动");
        }
        this.status = ExperimentStatus.RUNNING;
        this.startTime = LocalDateTime.now();
        this.updatedAt = LocalDateTime.now();
    }

    /**
     * 暂停实验
     */
    public void pause() {
        if (!canPause()) {
            throw new IllegalStateException("当前状态不允许暂停");
        }
        this.status = ExperimentStatus.PAUSED;
        this.updatedAt = LocalDateTime.now();
    }

    /**
     * 恢复实验
     */
    public void resume() {
        if (!canResume()) {
            throw new IllegalStateException("当前状态不允许恢复");
        }
        this.status = ExperimentStatus.RUNNING;
        this.updatedAt = LocalDateTime.now();
    }

    /**
     * 停止实验
     */
    public void stop() {
        if (!canStop()) {
            throw new IllegalStateException("当前状态不允许停止");
        }
        this.status = ExperimentStatus.STOPPED;
        this.endTime = LocalDateTime.now();
        this.updatedAt = LocalDateTime.now();
    }

    /**
     * 完成实验
     */
    public void complete() {
        if (!isRunning()) {
            throw new IllegalStateException("只有运行中的实验可以完成");
        }
        this.status = ExperimentStatus.COMPLETED;
        this.endTime = LocalDateTime.now();
        this.updatedAt = LocalDateTime.now();
    }

    /**
     * 失败
     */
    public void fail(String errorMessage) {
        this.status = ExperimentStatus.FAILED;
        this.endTime = LocalDateTime.now();
        this.updatedAt = LocalDateTime.now();
    }

    /**
     * 推进到下一轮
     */
    public void advanceEpisode() {
        if (currentEpisode == null) {
            currentEpisode = 0;
        }
        currentEpisode++;
        this.updatedAt = LocalDateTime.now();
    }

    /**
     * 重置实验
     */
    public void reset() {
        this.currentEpisode = 0;
        this.status = ExperimentStatus.CREATED;
        this.startTime = null;
        this.endTime = null;
        this.statistics = new ExperimentStatistics();
        this.updatedAt = LocalDateTime.now();
    }
}
