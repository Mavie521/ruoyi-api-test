"""
若依接口测试框架 - 全局配置
支持通过 .env 文件或环境变量覆盖
"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

# =============================================
# 若依服务配置
# =============================================
BASE_URL = os.getenv("BASE_URL", "http://localhost:8080")

# 默认管理员账号（仅用于测试框架初始化）
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")

# =============================================
# 测试数据文件
# =============================================
EXCEL_FILE = os.getenv("EXCEL_FILE", str(BASE_DIR / "data" / "test_cases.xlsx"))
SHEET_NAME = os.getenv("SHEET_NAME", "Sheet1")

# =============================================
# MySQL 数据库配置（若依后端数据库）
# =============================================
DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = int(os.getenv("DB_PORT", "3307"))
DB_NAME = os.getenv("DB_NAME", "ry-vue")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "root")
DB_CHARSET = os.getenv("DB_CHARSET", "utf8")

DB_CONFIG = {
    "host": DB_HOST,
    "port": DB_PORT,
    "database": DB_NAME,
    "user": DB_USER,
    "password": DB_PASSWORD,
    "charset": DB_CHARSET,
}

# =============================================
# 日志配置
# =============================================
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_DIR = BASE_DIR / "logs"

# =============================================
# 报告目录
# =============================================
REPORT_DIR = BASE_DIR / "reports"
ALLURE_RESULTS_DIR = REPORT_DIR / "allure-results"
ALLURE_REPORT_DIR = REPORT_DIR / "allure-report"

# =============================================
# 请求配置
# =============================================
DEFAULT_TIMEOUT = int(os.getenv("DEFAULT_TIMEOUT", "30"))  # 秒


def ensure_dirs():
    """确保所有目录存在"""
    for d in [LOG_DIR, REPORT_DIR, ALLURE_RESULTS_DIR, ALLURE_REPORT_DIR]:
        d.mkdir(parents=True, exist_ok=True)


ensure_dirs()
