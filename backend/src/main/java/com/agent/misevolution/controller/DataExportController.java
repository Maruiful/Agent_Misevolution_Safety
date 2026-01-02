package com.agent.misevolution.controller;

import com.agent.misevolution.dto.Result;
import com.agent.misevolution.domain.experiment.Experiment;
import com.agent.misevolution.service.ExperimentService;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.io.ByteArrayOutputStream;
import java.nio.charset.StandardCharsets;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.List;
import java.util.Map;

/**
 * 数据导出控制器
 *
 * 提供实验数据导出功能 (CSV/JSON)
 *
 * @author Maruiful
 * @version 1.0.0
 */
@Slf4j
@RestController
@RequestMapping("/api/export")
@CrossOrigin(origins = "*")
public class DataExportController {

    @Autowired
    private ExperimentService experimentService;

    /**
     * 导出实验数据为 JSON
     *
     * GET /api/export/experiment/json?experimentUuid=xxx
     *
     * @param experimentUuid 实验UUID
     * @return JSON 文件
     */
    @GetMapping("/experiment/json")
    public ResponseEntity<String> exportExperimentAsJson(@RequestParam String experimentUuid) {
        log.info("导出实验数据为 JSON: uuid={}", experimentUuid);

        try {
            Map<String, Object> statistics = experimentService.getExperimentStatistics(experimentUuid);

            if (statistics.containsKey("error")) {
                return ResponseEntity.badRequest().body((String) statistics.get("error"));
            }

            // 添加导出时间
            statistics.put("exportTime", LocalDateTime.now().format(DateTimeFormatter.ISO_LOCAL_DATE_TIME));

            // 转换为 JSON 字符串
            com.fasterxml.jackson.databind.ObjectMapper objectMapper = new com.fasterxml.jackson.databind.ObjectMapper();
            String json = objectMapper.writerWithDefaultPrettyPrinter().writeValueAsString(statistics);

            // 设置响应头
            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);
            headers.setContentDispositionFormData("attachment",
                String.format("experiment_%s_%s.json",
                    experimentUuid,
                    LocalDateTime.now().format(DateTimeFormatter.ofPattern("yyyyMMdd_HHmmss"))));

            return ResponseEntity.ok()
                    .headers(headers)
                    .body(json);

        } catch (Exception e) {
            log.error("导出 JSON 失败", e);
            return ResponseEntity.internalServerError().body("导出失败: " + e.getMessage());
        }
    }

    /**
     * 导出实验数据为 CSV
     *
     * GET /api/export/experiment/csv?experimentUuid=xxx
     *
     * @param experimentUuid 实验UUID
     * @return CSV 文件
     */
    @GetMapping("/experiment/csv")
    public ResponseEntity<byte[]> exportExperimentAsCsv(@RequestParam String experimentUuid) {
        log.info("导出实验数据为 CSV: uuid={}", experimentUuid);

        try {
            Map<String, Object> statistics = experimentService.getExperimentStatistics(experimentUuid);

            if (statistics.containsKey("error")) {
                return ResponseEntity.badRequest()
                        .body(((String) statistics.get("error")).getBytes(StandardCharsets.UTF_8));
            }

            // 构建 CSV 内容
            StringBuilder csv = new StringBuilder();

            // 添加基本信息
            csv.append("实验数据导出\n");
            csv.append("导出时间,").append(LocalDateTime.now().format(DateTimeFormatter.ISO_LOCAL_DATE_TIME)).append("\n");
            csv.append("实验UUID,").append(experimentUuid).append("\n");
            csv.append("\n");

            // 添加统计数据
            @SuppressWarnings("unchecked")
            Map<String, Object> stats = (Map<String, Object>) statistics.get("statistics");

            if (stats != null) {
                csv.append("统计数据\n");
                csv.append("指标,值\n");
                csv.append("当前轮次,").append(stats.get("currentEpisode")).append("\n");
                csv.append("总轮次,").append(stats.get("totalEpisodes")).append("\n");
                csv.append("进度,").append(String.format("%.2f%%", stats.get("progress"))).append("\n");
                csv.append("总奖励,").append(stats.get("totalReward")).append("\n");
                csv.append("平均奖励,").append(stats.get("averageReward")).append("\n");
                csv.append("成功次数,").append(stats.get("successCount")).append("\n");
                csv.append("违规次数,").append(stats.get("violationCount")).append("\n");
                csv.append("平均响应时间,").append(stats.get("averageResponseTime")).append("\n");
                csv.append("\n");

                // 策略分布
                Object strategyDist = stats.get("strategyDistribution");
                if (strategyDist instanceof Map) {
                    csv.append("策略分布\n");
                    csv.append("策略,次数\n");
                    @SuppressWarnings("unchecked")
                    Map<String, Integer> distribution = (Map<String, Integer>) strategyDist;
                    for (Map.Entry<String, Integer> entry : distribution.entrySet()) {
                        csv.append(entry.getKey()).append(",").append(entry.getValue()).append("\n");
                    }
                }
            }

            // 设置响应头
            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.parseMediaType("text/csv; charset=UTF-8"));
            headers.setContentDispositionFormData("attachment",
                String.format("experiment_%s_%s.csv",
                    experimentUuid,
                    LocalDateTime.now().format(DateTimeFormatter.ofPattern("yyyyMMdd_HHmmss"))));

            // 添加 UTF-8 BOM 以支持 Excel 正确显示中文
            byte[] bom = {(byte) 0xEF, (byte) 0xBB, (byte) 0xBF};
            byte[] csvBytes = csv.toString().getBytes(StandardCharsets.UTF_8);

            ByteArrayOutputStream outputStream = new ByteArrayOutputStream();
            outputStream.write(bom);
            outputStream.write(csvBytes);

            return ResponseEntity.ok()
                    .headers(headers)
                    .body(outputStream.toByteArray());

        } catch (Exception e) {
            log.error("导出 CSV 失败", e);
            return ResponseEntity.internalServerError()
                    .body(("导出失败: " + e.getMessage()).getBytes(StandardCharsets.UTF_8));
        }
    }

    /**
     * 导出所有运行中的实验列表
     *
     * GET /api/export/experiments/json
     *
     * @return JSON 文件
     */
    @GetMapping("/experiments/json")
    public ResponseEntity<String> exportAllExperiments() {
        log.info("导出所有实验列表");

        try {
            List<Experiment> experiments = experimentService.getAllRunningExperiments();

            com.fasterxml.jackson.databind.ObjectMapper objectMapper = new com.fasterxml.jackson.databind.ObjectMapper();
            String json = objectMapper.writerWithDefaultPrettyPrinter().writeValueAsString(experiments);

            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);
            headers.setContentDispositionFormData("attachment",
                String.format("experiments_%s.json",
                    LocalDateTime.now().format(DateTimeFormatter.ofPattern("yyyyMMdd_HHmmss"))));

            return ResponseEntity.ok()
                    .headers(headers)
                    .body(json);

        } catch (Exception e) {
            log.error("导出实验列表失败", e);
            return ResponseEntity.internalServerError().body("导出失败: " + e.getMessage());
        }
    }
}
