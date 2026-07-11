"""
日志配置 —— 基于 loguru
控制台彩色输出 + 文件日志（按天滚动）
"""
import sys
from loguru import logger
from config.config import LOG_DIR, LOG_LEVEL

# 移除默认 handler
logger.remove()

# 控制台输出（彩色）
logger.add(
    sys.stdout,
    format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | "
           "<cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
    level=LOG_LEVEL,
    colorize=True,
)

# 文件日志（全部）
logger.add(
    LOG_DIR / "ruoyi_api_{time:YYYY-MM-DD}.log",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
    level="DEBUG",
    rotation="100 MB",
    retention="30 days",
    encoding="utf-8",
)

# 文件日志（错误）
logger.add(
    LOG_DIR / "ruoyi_api_error_{time:YYYY-MM-DD}.log",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
    level="ERROR",
    rotation="100 MB",
    retention="30 days",
    encoding="utf-8",
    backtrace=True,
    diagnose=True,
)

__all__ = ["logger"]
