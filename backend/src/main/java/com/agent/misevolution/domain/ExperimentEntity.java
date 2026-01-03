package com.agent.misevolution.domain;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;

/**
 * 实验实体类
 *
 * 对应数据库 experiments 表
 *
 * @author Maruiful
 * @version 1.0.0
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class ExperimentEntity {

    /**
     * 实验ID（数据库自增主键）
     */
    private Long id;

    /**
     * 实验名称
     */
    private String experimentName;

    /**
     * 场景类型
     */
    private String scenario;

    /**
     * 实验配置（JSON格式）
     */
    private String config;

    /**
     * 状态: running/completed/failed/stopped
     */
    private String status;

    /**
     * 总轮数
     */
    private Integer totalEpisodes;

    /**
     * 当前轮数
     */
    private Integer currentEpisode;

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
}
