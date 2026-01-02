package com.agent.misevolution.domain.memory;

import com.agent.misevolution.domain.agent.ServiceExperience;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;

/**
 * 记忆条目模型
 *
 * 表示智能体的一条记忆，包含经验数据和向量表示
 *
 * @author Maruiful
 * @version 1.0.0
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class MemoryEntry {

    /**
     * 记忆ID
     */
    private String id;

    /**
     * 关联的经验ID
     */
    private String experienceId;

    /**
     * 经验数据（完整或简化）
     */
    private ServiceExperience experience;

    /**
     * 向量表示
     */
    private EmbeddingVector embedding;

    /**
     * 记忆重要性评分 (0-1)
     * 用于记忆淘汰和优先级排序
     */
    private Double importanceScore;

    /**
     * 访问次数
     */
    private Integer accessCount;

    /**
     * 最后访问时间
     */
    private LocalDateTime lastAccessTime;

    /**
     * 创建时间
     */
    private LocalDateTime createdAt;

    /**
     * 记忆摘要（用于快速浏览）
     */
    private String summary;

    /**
     * 记忆标签（用于分类检索）
     */
    private String tags;

    /**
     * 是否为成功经验
     */
    private Boolean isSuccessful;

    /**
     * 是否包含违规
     */
    private Boolean hasViolation;

    /**
     * 记忆类型
     */
    private MemoryType type;

    /**
     * 记忆类型枚举
     */
    public enum MemoryType {
        SUCCESS,           // 成功经验
        FAILURE,           // 失败经验
        VIOLATION,         // 违规经验
        WARNING            // 警示经验
    }

    /**
     * 构造函数
     */
    public MemoryEntry(String id, ServiceExperience experience, EmbeddingVector embedding) {
        this.id = id;
        this.experience = experience;
        this.embedding = embedding;
        this.importanceScore = 0.5;
        this.accessCount = 0;
        this.createdAt = LocalDateTime.now();
        this.lastAccessTime = LocalDateTime.now();

        // 自动推断记忆类型
        if (experience != null) {
            this.isSuccessful = experience.isSuccessful();
            this.hasViolation = experience.hasViolation();
            this.type = inferMemoryType();
        }

        // 生成摘要
        if (experience != null) {
            this.summary = experience.getSummary();
        }
    }

    /**
     * 推断记忆类型
     */
    private MemoryType inferMemoryType() {
        if (experience == null) {
            return MemoryType.WARNING;
        }

        if (experience.hasViolation()) {
            return MemoryType.VIOLATION;
        }

        if (experience.isFailed()) {
            return MemoryType.FAILURE;
        }

        if (experience.isSuccessful()) {
            return MemoryType.SUCCESS;
        }

        return MemoryType.WARNING;
    }

    /**
     * 记录访问
     */
    public void recordAccess() {
        this.accessCount = (this.accessCount == null ? 0 : this.accessCount) + 1;
        this.lastAccessTime = LocalDateTime.now();
    }

    /**
     * 更新重要性评分
     */
    public void updateImportanceScore(double score) {
        this.importanceScore = Math.max(0.0, Math.min(1.0, score));
    }

    /**
     * 判断是否为高重要性记忆
     */
    public boolean isHighImportance() {
        return importanceScore != null && importanceScore >= 0.7;
    }

    /**
     * 判断是否为低重要性记忆
     */
    public boolean isLowImportance() {
        return importanceScore != null && importanceScore < 0.3;
    }

    /**
     * 判断是否为最近访问（24小时内）
     */
    public boolean isRecentlyAccessed() {
        return lastAccessTime != null &&
               lastAccessTime.isAfter(LocalDateTime.now().minusDays(1));
    }

    /**
     * 获取记忆年龄（小时）
     */
    public long getAgeInHours() {
        if (createdAt == null) {
            return Long.MAX_VALUE;
        }
        return java.time.Duration.between(createdAt, LocalDateTime.now()).toHours();
    }

    @Override
    public String toString() {
        return String.format("MemoryEntry{id=%s, type=%s, importance=%.2f, summary='%s...'}",
            id, type, importanceScore, summary != null && summary.length() > 50 ?
                summary.substring(0, 50) : summary);
    }
}
