-- 创建数据库
CREATE DATABASE IF NOT EXISTS agent_evolution DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE agent_evolution;

-- 服务经验表
CREATE TABLE IF NOT EXISTS service_experiences (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '经验ID',
    experiment_id BIGINT NOT NULL COMMENT '实验ID',
    episode INT NOT NULL COMMENT '轮次',
    customer_issue VARCHAR(2000) COMMENT '客户问题描述',
    agent_response VARCHAR(4000) COMMENT '智能体响应',
    ticket_closed BOOLEAN DEFAULT FALSE COMMENT '工单是否关闭',
    response_time DECIMAL(10, 2) COMMENT '响应时间（秒）',
    customer_rating INT COMMENT '客户评分（1-5）',
    is_violation BOOLEAN DEFAULT FALSE COMMENT '是否违规',
    violation_types VARCHAR(500) COMMENT '违规类型（JSON数组）',
    reward DECIMAL(10, 2) COMMENT '奖励值',
    strategy_type VARCHAR(100) COMMENT '策略类型',
    metadata VARCHAR(2000) COMMENT '元数据（JSON格式）',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX idx_experiment_episode (experiment_id, episode),
    INDEX idx_violation (experiment_id, is_violation)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='服务经验表';
