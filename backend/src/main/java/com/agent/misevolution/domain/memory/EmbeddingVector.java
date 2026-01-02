package com.agent.misevolution.domain.memory;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.Arrays;

/**
 * 向量表示模型
 *
 * 用于文本的向量化存储和相似度计算
 *
 * @author Maruiful
 * @version 1.0.0
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class EmbeddingVector {

    /**
     * 向量ID
     */
    private String id;

    /**
     * 向量数据（浮点数数组）
     */
    private double[] vector;

    /**
     * 向量维度
     */
    private int dimension;

    /**
     * 向量对应的原始文本
     */
    private String text;

    /**
     * 向量模型名称
     */
    private String modelName;

    /**
     * 创建时间
     */
    private long createdAt;

    /**
     * 构造函数
     */
    public EmbeddingVector(String id, double[] vector, String text, String modelName) {
        this.id = id;
        this.vector = vector;
        this.dimension = vector != null ? vector.length : 0;
        this.text = text;
        this.modelName = modelName;
        this.createdAt = System.currentTimeMillis();
    }

    /**
     * 计算与另一个向量的余弦相似度
     *
     * @param other 另一个向量
     * @return 相似度（0-1之间，1表示完全相同）
     */
    public double cosineSimilarity(EmbeddingVector other) {
        if (vector == null || other.vector == null) {
            return 0.0;
        }

        if (vector.length != other.vector.length) {
            throw new IllegalArgumentException("向量维度不匹配");
        }

        double dotProduct = 0.0;
        double norm1 = 0.0;
        double norm2 = 0.0;

        for (int i = 0; i < vector.length; i++) {
            dotProduct += vector[i] * other.vector[i];
            norm1 += vector[i] * vector[i];
            norm2 += other.vector[i] * other.vector[i];
        }

        if (norm1 == 0.0 || norm2 == 0.0) {
            return 0.0;
        }

        return dotProduct / (Math.sqrt(norm1) * Math.sqrt(norm2));
    }

    /**
     * 计算欧几里得距离
     *
     * @param other 另一个向量
     * @return 距离值（越小越相似）
     */
    public double euclideanDistance(EmbeddingVector other) {
        if (vector == null || other.vector == null) {
            return Double.MAX_VALUE;
        }

        if (vector.length != other.vector.length) {
            throw new IllegalArgumentException("向量维度不匹配");
        }

        double sum = 0.0;
        for (int i = 0; i < vector.length; i++) {
            double diff = vector[i] - other.vector[i];
            sum += diff * diff;
        }

        return Math.sqrt(sum);
    }

    /**
     * 判断向量是否有效
     */
    public boolean isValid() {
        return vector != null && vector.length > 0 && dimension == vector.length;
    }

    /**
     * 获取向量归一化后的副本
     */
    public double[] normalized() {
        if (vector == null) {
            return new double[0];
        }

        double[] normalized = new double[vector.length];
        double norm = 0.0;

        for (double v : vector) {
            norm += v * v;
        }

        norm = Math.sqrt(norm);

        if (norm == 0.0) {
            return Arrays.copyOf(vector, vector.length);
        }

        for (int i = 0; i < vector.length; i++) {
            normalized[i] = vector[i] / norm;
        }

        return normalized;
    }

    @Override
    public String toString() {
        return String.format("EmbeddingVector{id=%s, dimension=%d, text='%s...'}",
            id, dimension, text != null && text.length() > 50 ? text.substring(0, 50) : text);
    }
}
