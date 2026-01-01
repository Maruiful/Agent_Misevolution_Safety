package com.agent.misevolution;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.mybatis.spring.annotation.MapperScan;

/**
 * 客服智能体自进化风险分析系统 - 主启动类
 *
 * @author Maruiful
 * @version 1.0.0
 */
@SpringBootApplication
@MapperScan("com.agent.misevolution.repository")
public class CustomerServiceAgentApplication {

    public static void main(String[] args) {
        SpringApplication.run(CustomerServiceAgentApplication.class, args);
        System.out.println("========================================");
        System.out.println("客服智能体系统启动成功！");
        System.out.println("访问地址: http://localhost:8080");
        System.out.println("========================================");
    }
}
