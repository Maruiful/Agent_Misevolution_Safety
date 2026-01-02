package com.agent.misevolution.service.memory;

import dev.langchain4j.model.embedding.EmbeddingModel;
import dev.langchain4j.model.output.Response;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import java.util.HashMap;
import java.util.Map;

/**
 * 文本嵌入生成服务
 *
 * 使用 LLM 生成文本的向量表示
 *
 * @author Maruiful
 * @version 1.0.0
 */
@Slf4j
@Service
public class EmbeddingService {

    /**
     * 嵌入模型（使用智谱 AI 或其他国内模型）
     * 注意：需要在配置类中配置对应的 EmbeddingModel Bean
     */
    private final EmbeddingModel embeddingModel;

    /**
     * 是否启用嵌入缓存
     */
    @Value("${memory.embedding.cache-enabled:true}")
    private boolean cacheEnabled;

    /**
     * 嵌入缓存
     * Key: 文本内容, Value: 向量数组
     */
    private final Map<String, float[]> embeddingCache;

    /**
     * 缓存命中统计
     */
    private int cacheHits = 0;
    private int cacheMisses = 0;

    /**
     * 构造函数
     */
    public EmbeddingService(EmbeddingModel embeddingModel) {
        this.embeddingModel = embeddingModel;
        this.embeddingCache = new HashMap<>();
        log.info("EmbeddingService 初始化完成，缓存状态: {}", cacheEnabled ? "启用" : "禁用");
    }

    /**
     * 生成文本的向量表示
     *
     * @param text 输入文本
     * @return 向量数组
     */
    public float[] embed(String text) {
        if (text == null || text.trim().isEmpty()) {
            log.warn("尝试嵌入空文本");
            return new float[0];
        }

        // 检查缓存
        if (cacheEnabled && embeddingCache.containsKey(text)) {
            cacheHits++;
            log.debug("嵌入缓存命中: text='{}...'", text.substring(0, Math.min(50, text.length())));
            return embeddingCache.get(text);
        }

        cacheMisses++;

        try {
            // 调用 LLM 生成嵌入
            Response<float[]> response = embeddingModel.embed(text);
            float[] embedding = response.content();

            // 存入缓存
            if (cacheEnabled && embedding != null && embedding.length > 0) {
                embeddingCache.put(text, embedding);
                log.debug("嵌入已缓存: text='{}...', vector={}",
                    text.substring(0, Math.min(50, text.length())), embedding.length);
            }

            return embedding != null ? embedding : new float[0];

        } catch (Exception e) {
            log.error("生成嵌入失败: text='{}...'", text.substring(0, Math.min(50, text.length())), e);
            return new float[0];
        }
    }

    /**
     * 批量生成向量表示
     *
     * @param texts 文本列表
     * @return 向量数组列表
     */
    public Map<String, float[]> embedBatch(java.util.List<String> texts) {
        Map<String, float[]> embeddings = new HashMap<>();

        for (String text : texts) {
            float[] embedding = embed(text);
            embeddings.put(text, embedding);
        }

        log.info("批量嵌入完成: {} 个文本", texts.size());
        return embeddings;
    }

    /**
     * 清空缓存
     */
    public void clearCache() {
        embeddingCache.clear();
        cacheHits = 0;
        cacheMisses = 0;
        log.info("嵌入缓存已清空");
    }

    /**
     * 获取缓存统计信息
     */
    public Map<String, Object> getCacheStats() {
        Map<String, Object> stats = new HashMap<>();
        stats.put("cacheEnabled", cacheEnabled);
        stats.put("cacheSize", embeddingCache.size());
        stats.put("cacheHits", cacheHits);
        stats.put("cacheMisses", cacheMisses);

        int total = cacheHits + cacheMisses;
        double hitRate = total > 0 ? (double) cacheHits / total : 0.0;
        stats.put("hitRate", hitRate);

        return stats;
    }

    /**
     * 获取缓存命中率
     */
    public double getCacheHitRate() {
        int total = cacheHits + cacheMisses;
        return total > 0 ? (double) cacheHits / total : 0.0;
    }

    /**
     * 预热缓存（为常用文本生成嵌入）
     *
     * @param commonTexts 常用文本列表
     */
    public void warmUpCache(java.util.List<String> commonTexts) {
        log.info("开始预热嵌入缓存: {} 个文本", commonTexts.size());

        for (String text : commonTexts) {
            if (!embeddingCache.containsKey(text)) {
                embed(text);
            }
        }

        log.info("嵌入缓存预热完成");
    }
}
