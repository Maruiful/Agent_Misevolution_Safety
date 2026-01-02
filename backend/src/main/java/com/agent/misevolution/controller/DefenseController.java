package com.agent.misevolution.controller;

import com.agent.misevolution.dto.Result;
import com.agent.misevolution.service.defense.SafetySentry;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

/**
 * 防御机制控制器
 *
 * 提供防御机制相关的 REST API
 *
 * @author Maruiful
 * @version 1.0.0
 */
@Slf4j
@RestController
@RequestMapping("/api/defense")
@CrossOrigin(origins = "*")
public class DefenseController {

    @Autowired(required = false)
    private SafetySentry safetySentry;

    /**
     * 查询防御统计信息
     *
     * GET /api/defense/statistics
     *
     * @return 防御统计数据
     */
    @GetMapping("/statistics")
    public Result<SafetySentry.DefenseStatistics> getDefenseStatistics() {
        log.debug("查询防御统计信息");

        try {
            if (safetySentry == null) {
                return Result.error("安全哨兵未启用");
            }

            SafetySentry.DefenseStatistics statistics = safetySentry.getStatistics();
            return Result.success("查询成功", statistics);

        } catch (Exception e) {
            log.error("查询防御统计失败", e);
            return Result.error("查询防御统计失败: " + e.getMessage());
        }
    }

    /**
     * 重置防御统计
     *
     * POST /api/defense/statistics/reset
     *
     * @return 结果
     */
    @PostMapping("/statistics/reset")
    public Result<Void> resetDefenseStatistics() {
        log.info("重置防御统计");

        try {
            if (safetySentry == null) {
                return Result.error("安全哨兵未启用");
            }

            safetySentry.resetStatistics();
            return Result.success("防御统计已重置", null);

        } catch (Exception e) {
            log.error("重置防御统计失败", e);
            return Result.error("重置防御统计失败: " + e.getMessage());
        }
    }

    /**
     * 获取防御配置
     *
     * GET /api/defense/config
     *
     * @return 防御配置信息
     */
    @GetMapping("/config")
    public Result<Map<String, Object>> getDefenseConfig() {
        log.debug("获取防御配置");

        try {
            // 从配置文件读取防御配置
            Map<String, Object> config = Map.of(
                "safetySentryEnabled", true,
                "redTeamEnabled", false,
                "policyCheckerEnabled", false,
                "strictMode", false
            );

            return Result.success("查询成功", config);

        } catch (Exception e) {
            log.error("获取防御配置失败", e);
            return Result.error("获取防御配置失败: " + e.getMessage());
        }
    }

    /**
     * 健康检查
     *
     * GET /api/defense/health
     *
     * @return 健康状态
     */
    @GetMapping("/health")
    public Result<Map<String, Object>> healthCheck() {
        log.debug("防御机制健康检查");

        try {
            boolean healthy = safetySentry != null;

            Map<String, Object> health = Map.of(
                "status", healthy ? "UP" : "DOWN",
                "safetySentry", healthy ? "enabled" : "disabled",
                "timestamp", System.currentTimeMillis()
            );

            return Result.success("查询成功", health);

        } catch (Exception e) {
            log.error("健康检查失败", e);
            return Result.error("健康检查失败: " + e.getMessage());
        }
    }
}
