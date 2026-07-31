"""
utils 工具层 —— 对外暴露的公共接口

使用方式:
    from utils import logger, read_excel, allure_init, DbClient

各文件职责:
    logger.py       → 日志（基于 loguru，控制台 + 文件双输出）
    db_utils.py     → 数据库（连接池 + query/query_one/execute）
    allure_utils.py → Allure 报告（请求/响应挂载 + 敏感信息自动脱敏）
    excel_utils.py  → Excel 数据驱动（读取 + Jinja2 变量渲染）
    assertions.py   → 断言工具（接口字段 + 数据库校验）
    extract_utils.py→ 数据提取（JSONPath + SQL 提取到全局变量池）
    crypto_utils.py → 加密（Fernet AES-128-CBC，密钥不进代码）
"""
from .logger import logger
from .excel_utils import read_excel
from .allure_utils import allure_init
from .db_utils import DbClient

__all__ = ["logger", "read_excel", "allure_init", "DbClient"]
