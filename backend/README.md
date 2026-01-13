# CS-Safety Guard 后端服务

自进化客服智能体错误进化风险分析平台 - 后端API服务

## 功能特性

- 🤖 **智能对话**: 基于LangChain + OpenAI的客服智能体
- 🔍 **违规检测**: 实时检测智能体的违规行为
- 📊 **策略追踪**: 追踪智能体策略演化过程
- 💾 **经验回放**: 支持经验回放缓冲区
- 📈 **数据分析**: 完整的实验统计和演化曲线
- 🚀 **异步处理**: 基于FastAPI的高性能异步API

## 技术栈

- **Web框架**: FastAPI 0.109.0
- **智能体框架**: LangGraph + LangChain
- **LLM集成**: LangChain + OpenAI
- **数据验证**: Pydantic v2
- **日志系统**: Loguru
- **异步处理**: asyncio + aiohttp

## 项目结构

```
backend/
├── api/
│   └── routes/           # API路由
│       ├── chat.py       # 对话接口
│       ├── stats.py      # 统计接口
│       └── data.py       # 数据接口
├── core/
│   ├── agent.py                    # 智能体核心逻辑
│   ├── config.py                   # 配置管理
│   ├── paper_violation_detector.py # 论文风格违规检测（LLM-as-a-Judge）
│   ├── safety_sentry.py            # 安全哨兵防御机制
│   └── knowledge_base.py           # 业务知识库
├── models/
│   ├── schemas.py        # Pydantic模型
│   └── enums.py          # 枚举类型
├── services/
│   ├── llm_service.py    # LLM调用服务
│   ├── reward_service.py # 奖励计算服务
│   └── evolution_service.py # 演化追踪服务
├── storage/
│   ├── replay_buffer.py  # 经验回放缓冲区
│   └── experiment_data.py # 实验数据存储
├── utils/
│   ├── logger.py         # 日志工具
│   └── formulas.py       # 公式计算
├── main.py               # FastAPI应用入口
├── requirements.txt      # 依赖列表
├── .env                  # 环境变量配置
├── start.sh              # Linux/Mac启动脚本
└── start.bat             # Windows启动脚本
```

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

复制 `.env.example` 为 `.env` 并编辑配置：

```bash
cp .env.example .env
```

编辑 `.env` 文件，设置必要的配置：

```env
# LLM配置（必需）
OPENAI_API_KEY=your_api_key_here

# 其他配置使用默认值即可
```

### 3. 启动服务

**Windows:**
```bash
start.bat
```

**Linux/Mac:**
```bash
chmod +x start.sh
./start.sh
```

**或直接使用Python:**
```bash
python main.py
```

服务将在 `http://localhost:8000` 启动

### 4. 访问API文档

打开浏览器访问: `http://localhost:8000/docs`

## API接口

### 对话接口

- `POST /api/chat` - 发送消息并获取回复
- `GET /api/chat/history` - 获取对话历史
- `GET /api/chat/session` - 获取会话信息
- `DELETE /api/chat/session/{session_id}` - 删除会话
- `POST /api/chat/session/reset` - 重置会话
- `GET /api/chat/sessions` - 列出所有会话

### 统计接口

- `GET /api/stats/overview` - 获取实验概览统计
- `GET /api/stats/evolution` - 获取演化曲线数据
- `GET /api/stats/strategy` - 获取策略信息
- `GET /api/stats/violations` - 获取违规统计
- `GET /api/stats/rewards` - 获取奖励统计

### 数据接口

- `GET /api/data/experiments` - 获取实验数据列表
- `GET /api/data/experiments/{round_id}` - 获取单轮实验数据
- `GET /api/data/export` - 导出实验数据 (JSON/CSV)
- `GET /api/data/violations` - 获取所有违规数据
- `POST /api/data/replay_buffer/save` - 保存缓冲区
- `POST /api/data/replay_buffer/load` - 加载缓冲区
- `DELETE /api/data/experiments` - 清空实验数据

## 核心功能说明

### 1. 智能体对话流程

1. 接收用户输入
2. 调用LLM生成回复
3. 违规检测
4. 计算奖励（即时+延迟）
5. 计算策略参数
6. 保存到经验回放缓冲区
7. 返回完整响应

### 2. 违规检测

支持以下违规类型：

- **未授权退款** (unauthorized_refund): 未经验证直接退款
- **过度承诺** (over_promise): 使用绝对性词汇承诺
- **跳过验证** (skip_verification): 省略必要验证流程
- **激进行为** (aggressive_behavior): 使用不当语言

### 3. 奖励计算

**即时奖励**:
- 基于客户满意度 (1-5星)
- 考虑响应速度
- 考虑问题解决情况

**延迟奖励**:
- 违规惩罚
- 历史违规率影响
- 合规奖励

**总奖励**:
```
R_total = α × R_immediate + (1-α) × R_delayed
```

### 4. 策略演化

计算策略参数：

- **θᵢ**: 当前策略（基于违规率）
- **τᵢ**: 输入特征（轮次+表现）
- **rᵢ**: 历史反馈（平均奖励）
- **θᵢ₊₁**: 更新策略（学习率0.1）

## 配置说明

### 环境变量

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `API_HOST` | API服务地址 | 0.0.0.0 |
| `API_PORT` | API服务端口 | 8000 |
| `LLM_MODEL` | LLM模型名称 | gpt-4o |
| `LLM_TEMPERATURE` | 生成温度 | 0.7 |
| `OPENAI_API_KEY` | OpenAI API密钥 | (必需) |
| `MEMORY_SIZE` | 记忆缓冲区大小 | 1000 |
| `TOTAL_ROUNDS` | 实验总轮次 | 500 |
| `DEFAULT_SHORT_TERM_WEIGHT` | 短期奖励权重 | 0.7 |

### 奖励权重调整

短期奖励权重控制智能体对即时满足的关注程度：
- 较高的短期权重 (0.7+) → 更容易违规
- 较低的短期权重 (0.3-) → 更保守合规

## 日志

日志文件位置: `logs/backend.log`

日志级别: DEBUG, INFO, WARNING, ERROR, CRITICAL

## 数据持久化

### 实验数据
- 位置: `data/experiments/`
- 格式: JSON
- 自动保存: 每轮对话后

### 经验回放缓冲区
- 位置: `data/replay_buffers/`
- 格式: PKL
- 手动保存: 通过API

## 开发

### 运行测试

```bash
pytest
```

### 代码格式化

```bash
# 使用black
black .

# 使用ruff
ruff check .
```

## Docker部署

```bash
# 构建镜像
docker build -t cs-safety-backend .

# 运行容器
docker run -p 8000:8000 --env-file .env cs-safety-backend
```

## 故障排查

### 1. LLM调用失败

检查 `OPENAI_API_KEY` 是否正确设置

### 2. 端口冲突

修改 `.env` 中的 `API_PORT`

### 3. 依赖安装失败

尝试升级pip: `pip install --upgrade pip`

## 许可证

MIT License

## 联系方式

- 项目地址: [GitHub](https://github.com/your-repo)
- 文档: [Full Documentation](https://docs.example.com)
