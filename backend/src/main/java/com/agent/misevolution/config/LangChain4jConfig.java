package com.agent.misevolution.config;

import dev.langchain4j.model.chat.ChatLanguageModel;
import dev.langchain4j.model.zhipu.ZhipuAiChatModel;
import dev.langchain4j.model.zhipu.ZhipuAiClient;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

import java.time.Duration;

/**
 * LangChain4j 配置类
 *
 * 支持智谱 GLM 模型
 *
 * @author Maruiful
 * @version 1.0.0
 */
@Configuration
public class LangChain4jConfig {

    @Value("${langchain4j.zhipu-ai.api-key}")
    private String apiKey;

    @Value("${langchain4j.zhipu-ai.model-name:glm-4-flash}")
    private String modelName;

    @Value("${langchain4j.zhipu-ai.temperature:0.7}")
    private Double temperature;

    @Value("${langchain4j.zhipu-ai.max-tokens:2000}")
    private Integer maxTokens;

    @Bean
    public ChatLanguageModel chatLanguageModel() {
        return ZhipuAiChatModel.builder()
                .apiKey(apiKey)
                .model(modelName)
                .temperature(temperature)
                .build();
    }
}
