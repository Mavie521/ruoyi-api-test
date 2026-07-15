"""配置层 — 多环境配置加载与全局参数"""
from .config import *

__all__ = ["BASE_URL", "DB_CONFIG", "EXCEL_FILE", "LOG_DIR", "LOG_LEVEL",
           "REPORT_DIR", "ALLURE_RESULTS_DIR", "ensure_dirs"]
