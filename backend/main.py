"""
FastAPI主应用
自进化客服智能体风险分析平台后端服务
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from core.config import settings
from utils.logger import logger
from api.routes import chat, stats, data


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时执行
    logger.info("=" * 60)
    logger.info("🚀 后端服务启动中...")
    logger.info(f"API服务: http://{settings.api.host}:{settings.api.port}")
    logger.info(f"LLM模型: {settings.llm.model}")
    logger.info(f"记忆缓冲区大小: {settings.experiment.memory_size}")
    logger.info("=" * 60)

    yield

    # 关闭时执行
    logger.info("👋 后端服务关闭")


# 创建FastAPI应用
app = FastAPI(
    title="CS-Safety Guard API",
    description="自进化客服智能体错误进化风险分析平台",
    version="1.0.0",
    lifespan=lifespan,
)


# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 注册路由
app.include_router(chat.router)
app.include_router(stats.router)
app.include_router(data.router)


# 根路径
@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "CS-Safety Guard API",
        "description": "自进化客服智能体错误进化风险分析平台",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }


# 健康检查
@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "service": "CS-Safety Guard API",
        "version": "1.0.0"
    }


if __name__ == "__main__":
    import uvicorn

    # 运行服务
    uvicorn.run(
        "main:app",
        host=settings.api.host,
        port=settings.api.port,
        reload=settings.api.reload,
        log_level=settings.log.level.lower(),
    )
