"""
数据库工具 —— 连接池 + 查询/执行

功能:
  1. 全局连接池（MySQLConnectionPool），避免反复建连
  2. query / query_one / execute 三件套
  3. 所有操作自动写 Allure 步骤和日志

数据库断言已移至 utils.assertions:
    assert_db_value / assert_db_exists / assert_db_not_exists

用法:
    with DbClient() as db:
        user = db.query_one("SELECT * FROM sys_user WHERE user_name=%s", ("admin",))
"""
import time
import json
import allure
from mysql.connector.pooling import MySQLConnectionPool
from config.config import DB_CONFIG
from utils.logger import logger

_POOL = None


def _get_pool():
    """连接池单例（pool_size=10）"""
    global _POOL
    if _POOL is None:
        config = {**DB_CONFIG}
        _POOL = MySQLConnectionPool(
            pool_name="ry_pool", pool_size=10, pool_reset_session=True,
            host=config["host"], port=config["port"],
            database=config["database"], user=config["user"],
            password=config["password"], charset=config.get("charset", "utf8"),
            use_pure=True, autocommit=True, consume_results=True,
        )
        logger.info(f"连接池已创建: {config['host']}:{config['port']}/{config['database']}")
    return _POOL


class DbClient:
    """数据库客户端 —— 从连接池取连接，用后归还"""

    def __init__(self, config: dict = None):
        self.config = config or {**DB_CONFIG}
        self._conn = None

    def connect(self):
        """从连接池取一个连接（池满时阻塞等待）"""
        if self._conn is None or not self._conn.is_connected():
            self._conn = _get_pool().get_connection()
        return self._conn

    def close(self):
        """归还连接到池"""
        if self._conn:
            try:
                self._conn.close()
            except Exception:
                pass
            self._conn = None

    # ── SQL 操作 ──────────────────────────────────────

    @allure.step("SQL 查询")
    def query(self, sql: str, params: tuple = None) -> list:
        """执行查询，返回 list[dict]"""
        conn = self.connect()
        cur = conn.cursor(dictionary=True)
        cur.execute(sql, params)
        rows = cur.fetchall()
        cur.close()
        result = list(rows) if rows else []
        # Allure 附件
        body = self._fmt(sql, params, result)
        allure.attach(body, name="查询结果", attachment_type=allure.attachment_type.TEXT)
        logger.debug(f"  SQL → {len(result)} 条结果")
        return result

    def query_one(self, sql: str, params: tuple = None) -> dict:
        """查询单条记录，返回 dict 或 None"""
        rows = self.query(sql, params)
        return rows[0] if rows else None

    @allure.step("SQL 执行")
    def execute(self, sql: str, params: tuple = None, commit: bool = True) -> int:
        """执行 INSERT / UPDATE / DELETE，返回受影响行数"""
        conn = self.connect()
        cur = conn.cursor()
        cur.execute(sql, params)
        if commit:
            conn.commit()
        affected = cur.rowcount
        cur.close()
        allure.attach(
            f"SQL: {sql}\n参数: {params}\n影响行数: {affected}",
            name="执行结果",
        )
        logger.debug(f"  SQL → {affected} 行受影响")
        return affected

    # ── 辅助 ──────────────────────────────────────────

    @staticmethod
    def _fmt(sql: str, params: tuple, rows: list) -> str:
        lines = [f"SQL: {sql}", f"参数: {params}", f"结果数: {len(rows)}", ""]
        for i, row in enumerate(rows[:10], 1):
            lines.append(f"[{i}] {json.dumps(row, ensure_ascii=False, default=str, indent=2)}")
        if len(rows) > 10:
            lines.append(f"\n... 共 {len(rows)} 条，仅显示前 10 条")
        return "\n".join(lines)

    # ── 上下文支持 ────────────────────────────────────

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
