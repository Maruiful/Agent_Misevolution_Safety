package com.agent.misevolution.controller;

import com.agent.misevolution.domain.experiment.Experiment;
import com.agent.misevolution.dto.*;
import com.agent.misevolution.service.ExperimentService;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

/**
 * 实验控制器
 *
 * 提供实验控制的 REST API
 *
 * @author Maruiful
 * @version 1.0.0
 */
@Slf4j
@RestController
@RequestMapping("/api/experiment")
public class ExperimentController {

    @Autowired
    private ExperimentService experimentService;

    /**
     * 启动实验
     *
     * POST /api/experiment/start
     *
     * @param request 启动请求
     * @return 实验信息
     */
    @PostMapping("/start")
    public Result<Experiment> startExperiment(@RequestBody StartExperimentRequest request) {
        log.info("收到启动实验请求: name={}", request.getName());
        log.info("实验的轮数: episodes={}",request.config.getEpisodes());
        try {
            // 使用请求中的配置,或者使用默认配置
            ExperimentConfig config = request.getConfig();
            if (config == null) {
                config = ExperimentConfig.defaultBaselineConfig();
            }

            // 启动实验
            Experiment experiment = experimentService.startExperiment(config, request.getName());

            return Result.success("实验启动成功", experiment);

        } catch (Exception e) {
            log.error("启动实验失败", e);
            return Result.error("启动实验失败: " + e.getMessage());
        }
    }

    /**
     * 暂停实验
     *
     * POST /api/experiment/pause
     *
     * @param request 暂停请求
     * @return 结果
     */
    @PostMapping("/pause")
    public Result<Void> pauseExperiment(@RequestBody PauseExperimentRequest request) {
        log.info("收到暂停实验请求: uuid={}", request.getExperimentUuid());

        try {
            boolean success = experimentService.pauseExperiment(request.getExperimentUuid());

            if (success) {
                return Result.success("实验已暂停", null);
            } else {
                return Result.error("暂停实验失败: 实验不存在或当前状态不允许暂停");
            }

        } catch (Exception e) {
            log.error("暂停实验失败", e);
            return Result.error("暂停实验失败: " + e.getMessage());
        }
    }

    /**
     * 恢复实验
     *
     * POST /api/experiment/resume
     *
     * @param request 恢复请求
     * @return 结果
     */
    @PostMapping("/resume")
    public Result<Void> resumeExperiment(@RequestBody ResumeExperimentRequest request) {
        log.info("收到恢复实验请求: uuid={}", request.getExperimentUuid());

        try {
            boolean success = experimentService.resumeExperiment(request.getExperimentUuid());

            if (success) {
                return Result.success("实验已恢复", null);
            } else {
                return Result.error("恢复实验失败: 实验不存在或当前状态不允许恢复");
            }

        } catch (Exception e) {
            log.error("恢复实验失败", e);
            return Result.error("恢复实验失败: " + e.getMessage());
        }
    }

    /**
     * 停止实验
     *
     * POST /api/experiment/stop
     *
     * @param request 停止请求
     * @return 结果
     */
    @PostMapping("/stop")
    public Result<Void> stopExperiment(@RequestBody StopExperimentRequest request) {
        log.info("收到停止实验请求: uuid={}", request.getExperimentUuid());

        try {
            boolean success = experimentService.stopExperiment(request.getExperimentUuid());

            if (success) {
                return Result.success("实验已停止", null);
            } else {
                return Result.error("停止实验失败: 实验不存在或当前状态不允许停止");
            }

        } catch (Exception e) {
            log.error("停止实验失败", e);
            return Result.error("停止实验失败: " + e.getMessage());
        }
    }

    /**
     * 重置实验
     *
     * POST /api/experiment/reset
     *
     * @param request 重置请求
     * @return 结果
     */
    @PostMapping("/reset")
    public Result<Void> resetExperiment(@RequestBody ResetExperimentRequest request) {
        log.info("收到重置实验请求: uuid={}", request.getExperimentUuid());

        try {
            boolean success = experimentService.resetExperiment(request.getExperimentUuid());

            if (success) {
                return Result.success("实验已重置", null);
            } else {
                return Result.error("重置实验失败: 实验不存在");
            }

        } catch (Exception e) {
            log.error("重置实验失败", e);
            return Result.error("重置实验失败: " + e.getMessage());
        }
    }

    /**
     * 查询实验状态
     *
     * GET /api/experiment/status?experimentUuid=xxx
     *
     * @param experimentUuid 实验UUID
     * @return 实验状态
     */
    @GetMapping("/status")
    public Result<Experiment> getExperimentStatus(@RequestParam String experimentUuid) {
        log.debug("查询实验状态: uuid={}", experimentUuid);

        try {
            Experiment experiment = experimentService.getExperiment(experimentUuid);

            if (experiment != null) {
                return Result.success("查询成功", experiment);
            } else {
                return Result.error("实验不存在: " + experimentUuid);
            }

        } catch (Exception e) {
            log.error("查询实验状态失败", e);
            return Result.error("查询实验状态失败: " + e.getMessage());
        }
    }

    /**
     * 查询实验指标
     *
     * GET /api/experiment/metrics?experimentUuid=xxx
     *
     * @param experimentUuid 实验UUID
     * @return 实验指标
     */
    @GetMapping("/metrics")
    public Result<Map<String, Object>> getExperimentMetrics(@RequestParam String experimentUuid) {
        log.debug("查询实验指标: uuid={}", experimentUuid);

        try {
            Map<String, Object> metrics = experimentService.getExperimentStatistics(experimentUuid);

            if (metrics.containsKey("error")) {
                return Result.error((String) metrics.get("error"));
            }

            return Result.success("查询成功", metrics);

        } catch (Exception e) {
            log.error("查询实验指标失败", e);
            return Result.error("查询实验指标失败: " + e.getMessage());
        }
    }

    /**
     * 查询所有运行中的实验
     *
     * GET /api/experiment/list
     *
     * @return 实验列表
     */
    @GetMapping("/list")
    public Result<List<Experiment>> listRunningExperiments() {
        log.debug("查询所有运行中的实验");

        try {
            List<Experiment> experiments = experimentService.getAllRunningExperiments();
            return Result.success("查询成功", experiments);

        } catch (Exception e) {
            log.error("查询实验列表失败", e);
            return Result.error("查询实验列表失败: " + e.getMessage());
        }
    }

    // ==================== 请求 DTO ====================

    /**
     * 启动实验请求
     */
    @lombok.Data
    public static class StartExperimentRequest {
        /**
         * 实验名称
         */
        private String name;

        /**
         * 实验配置
         */
        private ExperimentConfig config;
    }

    /**
     * 暂停实验请求
     */
    @lombok.Data
    public static class PauseExperimentRequest {
        /**
         * 实验UUID
         */
        private String experimentUuid;
    }

    /**
     * 恢复实验请求
     */
    @lombok.Data
    public static class ResumeExperimentRequest {
        /**
         * 实验UUID
         */
        private String experimentUuid;
    }

    /**
     * 停止实验请求
     */
    @lombok.Data
    public static class StopExperimentRequest {
        /**
         * 实验UUID
         */
        private String experimentUuid;
    }

    /**
     * 重置实验请求
     */
    @lombok.Data
    public static class ResetExperimentRequest {
        /**
         * 实验UUID
         */
        private String experimentUuid;
    }
}
