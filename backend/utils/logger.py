"""
日志工具模块
使用loguru实现统一的日志管理
"""
import sys
from pathlib import Path
from loguru import logger
from core.config import settings


def setup_logger():
    """配置日志系统"""

    # 移除默认的handler
    logger.remove()

    # 确保日志目录存在
    log_file = Path(settings.log.file)
    log_file.parent.mkdir(parents=True, exist_ok=True)

    # 控制台输出 - 格式化
    logger.add(
        sys.stdout,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
            "<level>{message}</level>"
        ),
        level=settings.log.level,
        colorize=True,
    )

    # 文件输出 - 按日期轮转
    logger.add(
        settings.log.file,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
        level=settings.log.level,
        rotation="00:00",  # 每天午夜轮转
        retention="30 days",  # 保留30天
        compression="zip",  # 压缩旧日志
        encoding="utf-8",
        enqueue=True,  # 异步写入
        backtrace=True,  # 完整回溯
        diagnose=True,  # 诊断信息
    )

    # 错误日志单独文件
    error_log_file = log_file.parent / f"{log_file.stem}_error{log_file.suffix}"
    logger.add(
        error_log_file,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
        level="ERROR",
        rotation="00:00",
        retention="90 days",
        compression="zip",
        encoding="utf-8",
        enqueue=True,
    )

    logger.info(f"日志系统初始化完成 - 级别: {settings.log.level}")
    logger.info(f"日志文件: {settings.log.file}")

    return logger


# 初始化日志
setup_logger()


# 导出logger
__all__ = ["logger", "setup_logger"]
