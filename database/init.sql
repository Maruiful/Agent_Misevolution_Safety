-- 客服智能体自进化风险分析系统 - 数据库初始化脚本

-- 创建数据库
CREATE DATABASE IF NOT EXISTS agent_evolution CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE agent_evolution;

-- 1. 实验记录表
CREATE TABLE IF NOT EXISTS experiments (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '实验ID',
    experiment_name VARCHAR(255) NOT NULL COMMENT '实验名称',
    scenario VARCHAR(50) NOT NULL DEFAULT 'customer_service' COMMENT '场景类型',
    config JSON COMMENT '实验配置(JSON格式)',
    status VARCHAR(20) NOT NULL COMMENT '状态:running/completed/failed',
    total_episodes INT NOT NULL COMMENT '总轮数',
    current_episode INT DEFAULT 0 COMMENT '当前轮数',
    start_time DATETIME COMMENT '开始时间',
    end_time DATETIME COMMENT '结束时间',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX idx_status (status),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='实验记录表';

-- 2. 服务经验表
CREATE TABLE IF NOT EXISTS service_experiences (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '经验ID',
    experiment_id BIGINT NOT NULL COMMENT '实验ID',
    episode INT NOT NULL COMMENT '轮次',
    customer_issue TEXT NOT NULL COMMENT '客户问题',
    agent_response TEXT NOT NULL COMMENT '智能体回复',
    ticket_closed BOOLEAN DEFAULT FALSE COMMENT '工单是否关闭',
    response_time DECIMAL(10,2) COMMENT '响应时间(秒)',
    customer_rating INT COMMENT '客户评分(1-5)',
    is_violation BOOLEAN DEFAULT FALSE COMMENT '是否违规',
    violation_types VARCHAR(255) COMMENT '违规类型(多个用逗号分隔)',
    reward DECIMAL(10,2) COMMENT '奖励值',
    strategy_type VARCHAR(50) COMMENT '策略类型',
    metadata JSON COMMENT '元数据',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    FOREIGN KEY (experiment_id) REFERENCES experiments(id) ON DELETE CASCADE,
    INDEX idx_experiment_episode (experiment_id, episode),
    INDEX idx_is_violation (is_violation),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='服务经验表';

-- 3. 违规记录表
CREATE TABLE IF NOT EXISTS violations (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '违规ID',
    experiment_id BIGINT NOT NULL COMMENT '实验ID',
    episode INT NOT NULL COMMENT '轮次',
    experience_id BIGINT NOT NULL COMMENT '经验ID',
    violation_type VARCHAR(50) NOT NULL COMMENT '违规类型:over_promise/unauthorized_refund/dismissive',
    agent_response TEXT NOT NULL COMMENT '智能体的违规回复',
    description TEXT COMMENT '违规描述',
    detected_by VARCHAR(50) COMMENT '检测方式:rule_based/llm_based/human',
    intercepted BOOLEAN DEFAULT FALSE COMMENT '是否被拦截',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    FOREIGN KEY (experiment_id) REFERENCES experiments(id) ON DELETE CASCADE,
    INDEX idx_experiment_violation_type (experiment_id, violation_type),
    INDEX idx_intercepted (intercepted)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='违规记录表';

-- 4. 实验指标表
CREATE TABLE IF NOT EXISTS experiment_metrics (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '指标ID',
    experiment_id BIGINT NOT NULL COMMENT '实验ID',
    episode INT NOT NULL COMMENT '轮次',
    metric_name VARCHAR(50) NOT NULL COMMENT '指标名称',
    metric_value DECIMAL(10,2) NOT NULL COMMENT '指标值',
    metric_group VARCHAR(50) COMMENT '指标分组:performance/safety/evolution/defense',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    FOREIGN KEY (experiment_id) REFERENCES experiments(id) ON DELETE CASCADE,
    UNIQUE KEY uk_experiment_episode_metric (experiment_id, episode, metric_name),
    INDEX idx_metric_group (metric_group)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='实验指标表';

-- 5. 对话日志表
CREATE TABLE IF NOT EXISTS conversation_logs (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '日志ID',
    experiment_id BIGINT NOT NULL COMMENT '实验ID',
    episode INT NOT NULL COMMENT '轮次',
    customer_issue TEXT NOT NULL COMMENT '客户问题',
    agent_response TEXT NOT NULL COMMENT '智能体回复',
    has_violation BOOLEAN DEFAULT FALSE COMMENT '是否违规',
    reward DECIMAL(10,2) COMMENT '奖励值',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    FOREIGN KEY (experiment_id) REFERENCES experiments(id) ON DELETE CASCADE,
    INDEX idx_experiment_episode (experiment_id, episode)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='对话日志表';

-- 插入测试数据
INSERT INTO experiments (experiment_name, scenario, status, total_episodes, current_episode) VALUES
('基线实验-测试', 'customer_service', 'running', 1000, 0);

SELECT '数据库初始化完成!' AS message;
