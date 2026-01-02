package com.agent.misevolution.service.memory;

import com.agent.misevolution.domain.agent.ServiceExperience;
import com.agent.misevolution.domain.memory.EmbeddingVector;
import com.agent.misevolution.domain.memory.MemoryEntry;
import com.agent.misevolution.domain.memory.MemorySummary;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.*;
import java.util.concurrent.ConcurrentHashMap;
import java.util.stream.Collectors;

/**
 * 经验记忆管理服务
 *
 * 负责智能体的经验存储、检索和管理
 *
 * @author Maruiful
 * @version 1.0.0
 */
@Slf4j
@Service
public class ExperienceMemory {

    /**
     * 嵌入生成服务
     */
    private final EmbeddingService embeddingService;

    /**
     * 记忆存储（Key: 记忆ID, Value: 记忆条目）
     */
    private final Map<String, MemoryEntry> memoryStore;

    /**
     * 文本到记忆ID的索引（用于快速查找）
     */
    private final Map<String, String> textIndex;

    /**
     * 最大记忆容量
     */
    @Value("${memory.max-size:1000}")
    private int maxSize;

    /**
     * 检索时返回的Top-K数量
     */
    @Value("${memory.retrieval-top-k:5}")
    private int topK;

    /**
     * 相似度阈值
     */
    @Value("${memory.similarity-threshold:0.7}")
    private double similarityThreshold;

    /**
     * LRU访问队列（用于淘汰策略）
     */
    private final LinkedHashMap<String, Long> accessQueue;

    /**
     * 记忆统计
     */
    private int totalAdded = 0;
    private int totalEvicted = 0;
    private int totalRetrieved = 0;

    /**
     * 构造函数
     */
    public ExperienceMemory(EmbeddingService embeddingService) {
        this.embeddingService = embeddingService;
        this.memoryStore = new ConcurrentHashMap<>();
        this.textIndex = new ConcurrentHashMap<>();

        // LRU队列：按访问时间排序
        this.accessQueue = new LinkedHashMap<>(16, 0.75f, true) {
            @Override
            protected boolean removeEldestEntry(Map.Entry<String, Long> eldest) {
                return size() > maxSize;
            }
        };

        log.info("ExperienceMemory 初始化完成，最大容量: {}", maxSize);
    }

    /**
     * 添加新经验到记忆
     *
     * @param experience 服务经验
     * @return 创建的记忆条目
     */
    public MemoryEntry addExperience(ServiceExperience experience) {
        if (experience == null) {
            log.warn("尝试添加空经验");
            return null;
        }

        // 检查是否已存在相似经验（去重）
        String summary = experience.getSummary();
        if (textIndex.containsKey(summary)) {
            log.debug("经验已存在，跳过添加: {}", summary.substring(0, Math.min(50, summary.length())));
            return memoryStore.get(textIndex.get(summary));
        }

        // 检查容量限制
        if (memoryStore.size() >= maxSize) {
            evictMemory();
        }

        try {
            // 生成嵌入向量
            float[] embedding = embeddingService.embed(summary);
            double[] vector = new double[embedding.length];
            for (int i = 0; i < embedding.length; i++) {
                vector[i] = embedding[i];
            }

            // 创建向量对象
            EmbeddingVector embeddingVector = new EmbeddingVector(
                UUID.randomUUID().toString(),
                vector,
                summary,
                "zhipu-embedding-2"
            );

            // 创建记忆条目
            String memoryId = UUID.randomUUID().toString();
            MemoryEntry entry = new MemoryEntry(memoryId, experience, embeddingVector);

            // 计算重要性评分
            double importanceScore = calculateImportanceScore(experience);
            entry.updateImportanceScore(importanceScore);

            // 存储记忆
            memoryStore.put(memoryId, entry);
            textIndex.put(summary, memoryId);
            accessQueue.put(memoryId, System.currentTimeMillis());

            totalAdded++;

            log.info("经验已添加到记忆: id={}, 重要性={:.2f}, 当前容量={}/{}",
                memoryId, importanceScore, memoryStore.size(), maxSize);

            return entry;

        } catch (Exception e) {
            log.error("添加经验到记忆失败: experience={}", experience.getId(), e);
            return null;
        }
    }

    /**
     * 基于向量相似度检索相关经验
     *
     * @param query 查询文本
     * @param topK 返回Top-K个结果
     * @return 相关经验列表
     */
    public List<MemoryEntry> retrieveSimilar(String query, int topK) {
        if (query == null || query.trim().isEmpty()) {
            log.warn("检索查询为空");
            return new ArrayList<>();
        }

        long startTime = System.currentTimeMillis();

        try {
            // 生成查询向量
            float[] queryEmbedding = embeddingService.embed(query);
            double[] queryVector = new double[queryEmbedding.length];
            for (int i = 0; i < queryEmbedding.length; i++) {
                queryVector[i] = queryEmbedding[i];
            }

            EmbeddingVector queryEmbeddingVector = new EmbeddingVector(
                UUID.randomUUID().toString(),
                queryVector,
                query,
                "zhipu-embedding-2"
            );

            // 计算所有记忆的相似度
            Map<MemoryEntry, Double> similarities = new HashMap<>();
            for (MemoryEntry entry : memoryStore.values()) {
                double similarity = entry.getEmbedding().cosineSimilarity(queryEmbeddingVector);
                if (similarity >= similarityThreshold) {
                    similarities.put(entry, similarity);
                }
            }

            // 按相似度排序，取Top-K
            int k = Math.min(topK, similarities.size());
            List<MemoryEntry> results = similarities.entrySet().stream()
                    .sorted((e1, e2) -> Double.compare(e2.getValue(), e1.getValue())) // 降序
                    .limit(k)
                    .map(Map.Entry::getKey)
                    .collect(Collectors.toList());

            // 更新访问记录
            for (MemoryEntry entry : results) {
                entry.recordAccess();
                accessQueue.put(entry.getId(), System.currentTimeMillis());
            }

            totalRetrieved++;

            long duration = System.currentTimeMillis() - startTime;
            log.debug("检索完成: query='{}...', 找到 {} 个相关经验, 耗时 {}ms",
                query.substring(0, Math.min(30, query.length())), results.size(), duration);

            return results;

        } catch (Exception e) {
            log.error("检索相关经验失败: query='{}...'", query.substring(0, Math.min(30, query.length())), e);
            return new ArrayList<>();
        }
    }

    /**
     * 使用默认Top-K检索
     */
    public List<MemoryEntry> retrieveSimilar(String query) {
        return retrieveSimilar(query, topK);
    }

    /**
     * 总结经验（将相似经验聚合为摘要）
     *
     * @param experiences 需要总结的经验列表
     * @return 经验摘要
     */
    public MemorySummary summarizeExperiences(List<ServiceExperience> experiences) {
        if (experiences == null || experiences.isEmpty()) {
            log.warn("尝试总结空经验列表");
            return null;
        }

        try {
            // 统计信息
            List<String> memoryIds = new ArrayList<>();
            Map<String, Integer> strategyCounts = new HashMap<>();
            double totalReward = 0.0;
            int successCount = 0;
            int violationCount = 0;

            for (ServiceExperience exp : experiences) {
                String memoryId = textIndex.get(exp.getSummary());
                if (memoryId != null) {
                    memoryIds.add(memoryId);
                }

                // 统计策略
                if (exp.getStrategyType() != null) {
                    strategyCounts.merge(exp.getStrategyType().name(), 1, Integer::sum);
                }

                // 统计奖励
                if (exp.getReward() != null) {
                    totalReward += exp.getReward();
                }

                // 统计成功和违规
                if (exp.isSuccessful()) {
                    successCount++;
                }
                if (exp.hasViolation()) {
                    violationCount++;
                }
            }

            // 确定主导策略
            String dominantStrategy = strategyCounts.entrySet().stream()
                    .max(Map.Entry.comparingByValue())
                    .map(Map.Entry::getKey)
                    .orElse(null);

            // 创建摘要
            MemorySummary summary = MemorySummary.builder()
                    .id(UUID.randomUUID().toString())
                    .title(String.format("经验摘要: %d 条经验", experiences.size()))
                    .content(String.format("包含 %d 条相关经验，主导策略: %s", experiences.size(), dominantStrategy))
                    .memoryEntryIds(memoryIds)
                    .experienceCount(experiences.size())
                    .averageReward(totalReward / experiences.size())
                    .successRate((double) successCount / experiences.size())
                    .violationRate((double) violationCount / experiences.size())
                    .createdAt(LocalDateTime.now())
                    .build();

            log.info("经验摘要已创建: 包含 {} 条经验, 成功率: %.2f%%, 违规率: %.2f%%",
                experiences.size(), summary.getSuccessRate() * 100, summary.getViolationRate() * 100);

            return summary;

        } catch (Exception e) {
            log.error("总结经验失败", e);
            return null;
        }
    }

    /**
     * 计算重要性评分
     */
    private double calculateImportanceScore(ServiceExperience experience) {
        double score = 0.5; // 基础分

        // 基于奖励值
        if (experience.getReward() != null) {
            score += Math.max(-0.5, Math.min(0.5, experience.getReward() / 100.0));
        }

        // 基于是否违规（违规经验更重要）
        if (experience.hasViolation()) {
            score += 0.3;
        }

        // 基于是否成功
        if (experience.isSuccessful()) {
            score += 0.1;
        }

        return Math.max(0.0, Math.min(1.0, score));
    }

    /**
     * LRU淘汰策略
     */
    private void evictMemory() {
        // 找到最久未访问的记忆
        String eldestMemoryId = accessQueue.entrySet().stream()
                .min(Map.Entry.comparingByValue())
                .map(Map.Entry::getKey)
                .orElse(null);

        if (eldestMemoryId != null) {
            MemoryEntry removed = memoryStore.remove(eldestMemoryId);
            if (removed != null) {
                textIndex.remove(removed.getExperience().getSummary());
                accessQueue.remove(eldestMemoryId);
                totalEvicted++;

                log.info("记忆已淘汰: id={}, 原因=LRU, 重要性={:.2f}",
                    eldestMemoryId, removed.getImportanceScore());
            }
        }
    }

    /**
     * 获取记忆统计信息
     */
    public Map<String, Object> getStatistics() {
        Map<String, Object> stats = new HashMap<>();
        stats.put("currentSize", memoryStore.size());
        stats.put("maxSize", maxSize);
        stats.put("totalAdded", totalAdded);
        stats.put("totalEvicted", totalEvicted);
        stats.put("totalRetrieved", totalRetrieved);
        stats.put("utilization", (double) memoryStore.size() / maxSize);

        // 计算平均重要性
        double avgImportance = memoryStore.values().stream()
                .mapToDouble(e -> e.getImportanceScore() == null ? 0.0 : e.getImportanceScore())
                .average()
                .orElse(0.0);
        stats.put("averageImportance", avgImportance);

        // 统计记忆类型
        Map<String, Long> typeCounts = memoryStore.values().stream()
                .collect(Collectors.groupingBy(
                    e -> e.getType() != null ? e.getType().name() : "UNKNOWN",
                    Collectors.counting()
                ));
        stats.put("typeDistribution", typeCounts);

        return stats;
    }

    /**
     * 清空所有记忆
     */
    public void clear() {
        memoryStore.clear();
        textIndex.clear();
        accessQueue.clear();
        totalAdded = 0;
        totalEvicted = 0;
        totalRetrieved = 0;
        log.info("所有记忆已清空");
    }

    /**
     * 获取所有记忆
     */
    public List<MemoryEntry> getAllMemories() {
        return new ArrayList<>(memoryStore.values());
    }

    /**
     * 根据ID获取记忆
     */
    public MemoryEntry getMemory(String memoryId) {
        MemoryEntry entry = memoryStore.get(memoryId);
        if (entry != null) {
            entry.recordAccess();
            accessQueue.put(memoryId, System.currentTimeMillis());
        }
        return entry;
    }
}
