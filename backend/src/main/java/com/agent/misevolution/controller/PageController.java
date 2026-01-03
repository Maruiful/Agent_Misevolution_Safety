package com.agent.misevolution.controller;

import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.GetMapping;

/**
 * 页面控制器
 * <p>
 * 负责 Thymeleaf 模板页面的路由
 *
 * @author Maruiful
 * @version 1.0.0
 */
@Controller
public class PageController {

    /**
     * 首页 - 实验控制页面
     */
    @GetMapping("/")
    public String index() {
        return "index";
    }

    /**
     * 实时监控页面
     */
    @GetMapping("/monitor")
    public String monitor() {
        return "monitor";
    }

    /**
     * 进化分析页面
     */
    @GetMapping("/evolution")
    public String evolution() {
        return "evolution";
    }

    /**
     * 对话记录页面
     */
    @GetMapping("/conversations")
    public String conversations() {
        return "conversations";
    }
}
