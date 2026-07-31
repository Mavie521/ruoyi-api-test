"""
日志配置 —— 基于 loguru

┌─────────────────────────────────────────────────────────────────────┐
│ 同时输出到 3 个地方：                                               │
│ 1. 控制台（彩色，INFO 级别）→ 开发时实时看                         │
│ 2. 文件（全量，DEBUG 级别，按天滚动）→ 排查问题时翻日志            │
│ 3. 文件（仅 ERROR，含完整堆栈 + 变量诊断）→ 快速定位错误根因      │
│                                                                     │
│ enqueue=True：异步写入磁盘，多线程安全，不阻塞测试执行              │
│ rotation="100 MB"：单文件超过 100MB 自动切新文件                    │
│ retention="30 days"：旧日志保留 30 天后自动删除                     │
└─────────────────────────────────────────────────────────────────────┘
"""
import sys
from loguru import logger
from config.config import LOG_DIR, LOG_LEVEL

# ── 第 1 步：移除 loguru 默认的 handler（我们要自己配置） ──
logger.remove()

# ── 第 2 步：控制台输出（开发时看的，带颜色，INFO 以上才显示） ──
logger.add(
    sys.stdout,
    format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | "
           "<cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
    level=LOG_LEVEL,
    colorize=True,
)

# ── 第 3 步：全量日志文件（所有 DEBUG 都记，用于排查问题） ──
logger.add(
    LOG_DIR / "ruoyi_api_{time:YYYY-MM-DD}.log",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
    level="DEBUG",
    rotation="100 MB",
    retention="30 days",
    encoding="utf-8",
    enqueue=True,
)

# ── 第 4 步：错误日志文件（仅 ERROR 级别，带完整调用链 + 变量值） ──
logger.add(
    LOG_DIR / "ruoyi_api_error_{time:YYYY-MM-DD}.log",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
    level="ERROR",
    rotation="100 MB",
    retention="30 days",
    encoding="utf-8",
    backtrace=True,  # 完整调用链：显示函数 A → B → C → 出错位置
    diagnose=True,   # 变量诊断：出错时把相关变量的值直接打印出来
    enqueue=True,
)

__all__ = ["logger"]
