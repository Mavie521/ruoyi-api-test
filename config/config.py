"""
若依接口测试框架 - 全局配置
支持多环境切换（dev / staging / prod），通过 .env 文件或环境变量覆盖
用法:
    # 默认读取 .env（开发环境）
    pytest tests/

    # 指定环境
    ENV=staging pytest tests/
    # 或创建 .env.staging 文件
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Python 3.11+ 使用 StrEnum 替代 str, Enum 混合
try:
    from enum import StrEnum as _StrEnum  # pylint: disable=unused-import
except ImportError:
    import enum as _enum
    class _StrEnum(str, _enum.Enum):  # pylint: disable=invalid-name
        """Python < 3.11 兼容：str + Enum 混合"""

BASE_DIR = Path(__file__).resolve().parent.parent


# =============================================
 # 初始赋值 多环境支持
# =============================================
class Env(_StrEnum):
    """运行环境枚举：限制只能填 dev/staging/prod/docker，防止手敲字符串输错"""
    DEV = "dev"
    STAGING = "staging"
    PROD = "prod"
    DOCKER = "docker"

# 优先级: --env 参数 > ENV 环境变量 > "dev"
#  1. 初始默认值
ACTIVE_ENV = Env.DEV  #默认 dev
# 2. 遍历所有启动命令行参数（sys.argv 就是你终端输入的整条命令）
#   本地开发
#   pytest tests/
#   # 指定环境
#   ENV=staging pytest tests/
#   # Docker 里
#   ENV=docker pytest tests/
for arg in sys.argv:
    if arg.startswith("--env="):  # 截取等号后面的值，赋值给ACTIVE_ENV
        ACTIVE_ENV = Env(arg.split("=")[1].lower())
        break
else:
    ACTIVE_ENV = Env(os.getenv("ENV", "dev")) #读取系统环境变量ENV，不存在就返回"dev"

# 加载对应环境的 .env 文件
# 优先级: .env.{env} > .env
#1. 根据选中的环境，拼接专属配置文件名
env_file = BASE_DIR / f".env.{ACTIVE_ENV.value}"
# 2. 如果这个【环境专属文件】存在，优先加载它
if env_file.exists():
    load_dotenv(env_file, override=True)
# 3. 永远加载公共兜底文件 .env
load_dotenv(BASE_DIR / ".env", override=False)  # .env 作为兜底


# =============================================
# 若依服务配置
# =============================================
# load_dotenv 把 .env 文件的内容注入到了 os.environ 里
# 所以下面 os.getenv 就能读到值了
# os.getenv("变量名", 默认值) 逻辑：
# 如果.env成功加载了该环境变量 → 使用.env 的值
BASE_URL = os.getenv("BASE_URL", "http://localhost:8080")

# 默认管理员账号（仅用于测试框架初始化）
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")

# =============================================
# 测试数据文件
# =============================================
EXCEL_FILE = os.getenv("EXCEL_FILE", str(BASE_DIR / "data" / "test_cases.xlsx"))
SHEET_NAME = os.getenv("SHEET_NAME", "Sheet")

# =============================================
# MySQL 数据库配置
# =============================================
DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
#类型转换.env 里面所有值全部是字符串！ 数据库端口必须是数字
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
DEFAULT_TIMEOUT = int(os.getenv("DEFAULT_TIMEOUT", "30"))


def ensure_dirs():
    """确保所有目录存在"""
    for d in [LOG_DIR, REPORT_DIR, ALLURE_RESULTS_DIR, ALLURE_REPORT_DIR]:
        d.mkdir(parents=True, exist_ok=True)


ensure_dirs()
