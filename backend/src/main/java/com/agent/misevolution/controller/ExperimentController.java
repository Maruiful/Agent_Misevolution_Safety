package com.agent.misevolution.controller;

import lombok.Data;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

/**
 * 实验控制接口
 *
 * @author Maruiful
 * @version 1.0.0
 */
@RestController
@RequestMapping("/api/experiment")
@CrossOrigin(origins = "*")
public class ExperimentController {

    /**
     * 启动实验
     */
    @PostMapping("/start")
    public ApiResponse startExperiment(@RequestBody ExperimentConfig config) {
        // TODO: 实现实验启动逻辑
        return ApiResponse.success("实验启动成功", null);
    }

    /**
     * 暂停实验
     */
    @PostMapping("/pause")
    public ApiResponse pauseExperiment(@RequestBody Map<String, Long> request) {
        // TODO: 实现实验暂停逻辑
        return ApiResponse.success("实验暂停成功", null);
    }

    /**
     * 重置实验
     */
    @PostMapping("/reset")
    public ApiResponse resetExperiment(@RequestBody Map<String, Long> request) {
        // TODO: 实现实验重置逻辑
        return ApiResponse.success("实验重置成功", null);
    }

    /**
     * 查询实验状态
     */
    @GetMapping("/status")
    public ApiResponse getExperimentStatus(@RequestParam Long experimentId) {
        // TODO: 实现状态查询逻辑
        return ApiResponse.success("查询成功", Map.of(
                "experimentId", experimentId,
                "status", "running",
                "currentEpisode", 0,
                "totalEpisodes", 1000
        ));
    }

    /**
     * 查询实验指标
     */
    @GetMapping("/metrics")
    public ApiResponse getExperimentMetrics(@RequestParam Long experimentId) {
        // TODO: 实现指标查询逻辑
        return ApiResponse.success("查询成功", Map.of(
                "totalEpisodes", 0,
                "successCount", 0,
                "violationCount", 0,
                "avgReward", 0.0
        ));
    }

    /**
     * 统一响应格式
     */
    @Data
    public static class ApiResponse {
        private int code;
        private String message;
        private Object data;

        public static ApiResponse success(String message, Object data) {
            ApiResponse response = new ApiResponse();
            response.setCode(200);
            response.setMessage(message);
            response.setData(data);
            return response;
        }

        public static ApiResponse error(String message, int code) {
            ApiResponse response = new ApiResponse();
            response.setCode(code);
            response.setMessage(message);
            return response;
        }
    }

    /**
     * 实验配置
     */
    @Data
    public static class ExperimentConfig {
        private String scenario;
        private Integer episodes;
        private Boolean enableMemory;
        private Boolean enableEvolution;
        private Boolean enableDefense;
        private RewardWeights rewardWeights;
    }

    /**
     * 奖励权重配置
     */
    @Data
    public static class RewardWeights {
        private Double shortTerm;
        private Double longTerm;
    }
}
