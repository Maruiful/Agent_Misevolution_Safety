package com.agent.misevolution.service;

import lombok.extern.slf4j.Slf4j;
import org.springframework.messaging.simp.SimpMessagingTemplate;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.HashMap;
import java.util.Map;

/**
 * WebSocket 消息发送服务
 *
 * 用于实时推送实验进度、违规事件等
 *
 * @author Maruiful
 * @version 1.0.0
 */
@Slf4j
@Service
public class WebSocketService {

    /**
     * 消息发送模板
     */
    private final SimpMessagingTemplate messagingTemplate;

    public WebSocketService(SimpMessagingTemplate messagingTemplate) {
        this.messagingTemplate = messagingTemplate;
    }

    /**
     * 发送实验进度更新
     *
     * @param experimentUuid 实验UUID
     * @param currentEpisode 当前轮次
     * @param totalEpisodes 总轮次
     * @param statistics 统计数据
     */
    public void sendExperimentProgress(
            String experimentUuid,
            int currentEpisode,
            int totalEpisodes,
            Object statistics) {

        Map<String, Object> message = new HashMap<>();
        message.put("type", "episode_completed");
        message.put("experimentUuid", experimentUuid);
        message.put("currentEpisode", currentEpisode);
        message.put("totalEpisodes", totalEpisodes);
        message.put("progress", calculateProgress(currentEpisode, totalEpisodes));
        message.put("statistics", statistics);
        message.put("timestamp", LocalDateTime.now());

        messagingTemplate.convertAndSend("/topic/experiment/" + experimentUuid, message);

        log.debug("发送实验进度: experimentUuid={}, episode={}/{}",
            experimentUuid, currentEpisode, totalEpisodes);
    }

    /**
     * 发送违规检测通知
     *
     * @param experimentUuid 实验UUID
     * @param episode 轮次
     * @param violationType 违规类型
     * @param severity 严重程度
     * @param description 描述
     */
    public void sendViolationDetected(
            String experimentUuid,
            int episode,
            String violationType,
            String severity,
            String description) {

        Map<String, Object> message = new HashMap<>();
        message.put("type", "violation_detected");
        message.put("experimentUuid", experimentUuid);
        message.put("episode", episode);
        message.put("violationType", violationType);
        message.put("severity", severity);
        message.put("description", description);
        message.put("timestamp", LocalDateTime.now());

        messagingTemplate.convertAndSend("/topic/experiment/" + experimentUuid + "/violations", message);

        log.warn("发送违规通知: experimentUuid={}, episode={}, type={}, severity={}",
            experimentUuid, episode, violationType, severity);
    }

    /**
     * 发送实验完成通知
     *
     * @param experimentUuid 实验UUID
     * @param totalEpisodes 总轮次
     * @param statistics 最终统计数据
     */
    public void sendExperimentCompleted(
            String experimentUuid,
            int totalEpisodes,
            Object statistics) {

        Map<String, Object> message = new HashMap<>();
        message.put("type", "experiment_completed");
        message.put("experimentUuid", experimentUuid);
        message.put("totalEpisodes", totalEpisodes);
        message.put("statistics", statistics);
        message.put("timestamp", LocalDateTime.now());

        messagingTemplate.convertAndSend("/topic/experiment/" + experimentUuid, message);

        log.info("发送实验完成通知: experimentUuid={}, totalEpisodes={}",
            experimentUuid, totalEpisodes);
    }

    /**
     * 发送实验状态变更通知
     *
     * @param experimentUuid 实验UUID
     * @param oldStatus 旧状态
     * @param newStatus 新状态
     */
    public void sendExperimentStatusChanged(
            String experimentUuid,
            String oldStatus,
            String newStatus) {

        Map<String, Object> message = new HashMap<>();
        message.put("type", "status_changed");
        message.put("experimentUuid", experimentUuid);
        message.put("oldStatus", oldStatus);
        message.put("newStatus", newStatus);
        message.put("timestamp", LocalDateTime.now());

        messagingTemplate.convertAndSend("/topic/experiment/" + experimentUuid, message);

        log.info("发送状态变更通知: experimentUuid={}, {} -> {}",
            experimentUuid, oldStatus, newStatus);
    }

    /**
     * 发送防御动作通知
     *
     * @param experimentUuid 实验UUID
     * @param episode 轮次
     * @param actionType 动作类型
     * @param reason 原因
     */
    public void sendDefenseAction(
            String experimentUuid,
            int episode,
            String actionType,
            String reason) {

        Map<String, Object> message = new HashMap<>();
        message.put("type", "defense_action");
        message.put("experimentUuid", experimentUuid);
        message.put("episode", episode);
        message.put("actionType", actionType);
        message.put("reason", reason);
        message.put("timestamp", LocalDateTime.now());

        messagingTemplate.convertAndSend("/topic/experiment/" + experimentUuid + "/defense", message);

        log.info("发送防御动作通知: experimentUuid={}, episode={}, action={}",
            experimentUuid, episode, actionType);
    }

    /**
     * 发送错误通知
     *
     * @param experimentUuid 实验UUID
     * @param error 错误信息
     */
    public void sendError(String experimentUuid, String error) {
        Map<String, Object> message = new HashMap<>();
        message.put("type", "error");
        message.put("experimentUuid", experimentUuid);
        message.put("error", error);
        message.put("timestamp", LocalDateTime.now());

        messagingTemplate.convertAndSend("/topic/experiment/" + experimentUuid + "/errors", message);

        log.error("发送错误通知: experimentUuid={}, error={}", experimentUuid, error);
    }

    /**
     * 计算进度百分比
     */
    private double calculateProgress(int current, int total) {
        if (total == 0) {
            return 0.0;
        }
        return (double) current / total * 100;
    }
}
