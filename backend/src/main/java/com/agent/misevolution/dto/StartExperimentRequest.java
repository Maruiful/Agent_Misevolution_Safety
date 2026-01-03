package com.agent.misevolution.dto;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * 启动实验请求
 *
 * @author Maruiful
 * @version 1.0.0
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
public class StartExperimentRequest {

    /**
     * 实验名称
     */
    private String name;

    /**
     * 实验配置
     */
    private ExperimentConfig config;
}
