"""
数据库工具 —— 基于 mysql-connector-python（连接池版）

核心功能:
1. 全局连接池（MySQLConnectionPool），避免反复建连
2. query / query_one / execute 三件套
3. assert_value / assert_exists / assert_not_exists 数据库断言
4. 所有操作自动写 Allure 步骤和日志
5. transaction() 上下文管理器 + execute(commit=False) 支持事务回滚

连接池说明:
    - 池大小 = 10（pool_size=10），pytest-xdist 4 worker 足够用
    - 用完后自动归还池中，不会新建 TCP 连接
    - 池满时 get_connection() 会阻塞等待，不报错

用法:
    with DbClient() as db:
        user = db.query_one("SELECT * FROM sys_user WHERE user_name=%s", ("admin",))
        db.assert_value("SELECT status FROM sys_user WHERE user_id=%s", expected="0", params=(1,))

事务隔离:
    def test_with_transaction(db_transaction):
        db_transaction.execute("DELETE FROM sys_role WHERE ...", commit=False)
        # 用例结束后自动 rollback，不留痕迹

注意事项:
    - 所有SQL参数使用 %s 占位符传参（防SQL注入）
    - 查询返回 list[dict]（dictionary=True）
    - 断言失败会抛出 AssertionError + 详细的 Allure 附件
"""
import time
import json
from contextlib import contextmanager
import allure
import mysql.connector
from mysql.connector.pooling import MySQLConnectionPool
from config.config import DB_CONFIG
from utils.logger import logger

# ── 全局连接池（模块级，只初始化一次） ──
# pool_size=10: 支持 pytest-xdist 4 worker + 剩余给 fixture 预取
# pool_reset_session=True: 每次 get_connection() 重置会话状态，
#   避免上一个连接遗留的变量污染下一个请求
_POOL = None


def _get_pool():
    """获取连接池（单例，首次调用时创建）"""
    global _POOL
    if _POOL is None:
        config = {**DB_CONFIG}
        _POOL = MySQLConnectionPool(
            pool_name="ry_pool",
            pool_size=10,
            pool_reset_session=True,
            host=config["host"],
            port=config["port"],
            database=config["database"],
            user=config["user"],
            password=config["password"],
            charset=config.get("charset", "utf8"),
            use_pure=True,
            autocommit=True,
            consume_results=True,
        )
        logger.info(f"连接池已创建: size=10, db={config['host']}:{config['port']}/{config['database']}")
    return _POOL


class DbClient:
    """数据库客户端 —— 从连接池取连接，用后归还"""

    def __init__(self, config: dict = None):
        self.config = config or {**DB_CONFIG}
        self._conn = None

    # ---------------------------------------------------------
    # 连接管理
    # ---------------------------------------------------------
    def connect(self):
        """从连接池取一个连接（池满时阻塞等待）"""
        if self._conn is None or not self._conn.is_connected():
            pool = _get_pool()
            self._conn = pool.get_connection()
            logger.debug(
                f"DB 从池中获取: {self.config['host']}:{self.config['port']}/{self.config['database']}"
            )
        return self._conn

    def close(self):
        """归还连接到池（不关闭，只是标记为可重用）"""
        if self._conn:
            try:
                self._conn.close()  # 归还池中
            except Exception:
                pass
            self._conn = None

    # ---------------------------------------------------------
    # SQL 执行
    # ---------------------------------------------------------
    @allure.step("SQL 查询")
    def query(self, sql: str, params: tuple = None) -> list:
        """
        执行查询，返回所有结果行
        - sql: SELECT 语句，使用 %s 占位符
        - params: 参数元组
        - 返回 list[dict]
        """
        conn = self.connect()
        start = time.time()
        cur = conn.cursor(dictionary=True)
        cur.execute(sql, params)
        rows = cur.fetchall()
        cur.close()
        elapsed = time.time() - start

        result = list(rows) if rows else []
        attach_text = self._format_sql_result(sql, params, result, elapsed)
        allure.attach(attach_text, name="查询结果", attachment_type=allure.attachment_type.TEXT)
        logger.debug(f"  SQL ({elapsed:.2f}s) → {len(result)} 条结果")
        return result

    def query_one(self, sql: str, params: tuple = None) -> dict:
        """查询单条记录，返回 dict 或 None"""
        rows = self.query(sql, params)
        return rows[0] if rows else None

    @allure.step("SQL 执行")
    def execute(self, sql: str, params: tuple = None, commit: bool = True) -> int:
        """
        执行 INSERT / UPDATE / DELETE
        - commit=True:  自动提交（默认，兼容现有用例）
        - commit=False: 不提交（用于事务上下文，由外层控制提交/回滚）
        返回受影响行数
        """
        conn = self.connect()
        start = time.time()
        cur = conn.cursor()
        cur.execute(sql, params)
        if commit:
            conn.commit()
        affected = cur.rowcount
        cur.close()
        elapsed = time.time() - start

        allure.attach(
            f"SQL: {sql}\n参数: {params}\n影响行数: {affected}\n耗时: {elapsed:.2f}s",
            name="执行结果",
        )
        logger.debug(f"  SQL ({elapsed:.2f}s) → {affected} 行受影响")
        return affected

    # ---------------------------------------------------------
    # 数据库断言
    # ---------------------------------------------------------
    @allure.step("数据库断言: 值相等")
    def assert_value(self, sql: str, expected, params: tuple = None,
                     column: str = None):
        """
        断言数据库中的某个字段值等于预期
        - sql: 查询语句
        - expected: 预期值
        - params: SQL参数
        - column: 指定字段名（不指定则取第一个字段）
        """
        result = self.query_one(sql, params)
        assert result is not None, \
            f" 数据库断言失败: 查询无结果\n  SQL: {sql}  params: {params}"

        if column:
            actual = result.get(column)
        else:
            actual = list(result.values())[0] if result else None

        assert actual == expected, (
            " 数据库断言失败: 值不匹配\n"
            f"  SQL: {sql}\n"
            f"  参数: {params}\n"
            f"  字段: {column or '(自动取第一个字段)'}\n"
            f"  预期: {repr(expected)}\n"
            f"  实际: {repr(actual)}"
        )

        logger.info(f" 数据库断言通过: {actual} == {expected}")
        return actual

    @allure.step("数据库断言: 记录存在")
    def assert_exists(self, sql: str, params: tuple = None):
        """断言查询结果至少有一条记录"""
        rows = self.query(sql, params)
        assert len(rows) >= 1, \
            f" 数据库断言失败: 期望记录存在，但未查到\n  SQL: {sql}  params: {params}"
        logger.info(f" 数据库断言通过: 记录存在 ({len(rows)}条)")

    @allure.step("数据库断言: 记录不存在")
    def assert_not_exists(self, sql: str, params: tuple = None):
        """断言查询结果为空（用于验证删除成功）"""
        rows = self.query(sql, params)
        assert len(rows) == 0, \
            f" 数据库断言失败: 期望无记录，但查到 {len(rows)} 条\n  SQL: {sql}  params: {params}"
        logger.info(" 数据库断言通过: 记录不存在")

    # ---------------------------------------------------------
    # 事务管理
    # ---------------------------------------------------------
    @contextmanager
    def transaction(self):
        """
        事务上下文管理器 —— 自动回滚，实现用例间数据隔离

        用法:
            with db.transaction():
                db.execute("UPDATE sys_user SET status=%s WHERE user_id=%s", ("1", 1), commit=False)
                # 抛出异常或正常退出都会自动 rollback
        """
        conn = self.connect()
        conn.start_transaction()
        try:
            yield self
        except Exception:
            conn.rollback()
            logger.warning(" 事务回滚（异常）")
            raise
        else:
            conn.rollback()
            logger.debug(" 事务回滚（正常结束，数据已清理）")

    # ---------------------------------------------------------
    # 辅助
    # ---------------------------------------------------------
    @staticmethod
    def _format_sql_result(sql: str, params: tuple, rows: list, elapsed: float) -> str:
        """格式化查询结果用于 Allure 附件"""
        lines = [
            f"SQL: {sql}",
            f"参数: {params}",
            f"结果数: {len(rows)}",
            f"耗时: {elapsed:.2f}s",
            "",
        ]
        if rows:
            for i, row in enumerate(rows[:10], 1):
                lines.append(f"[{i}] {json.dumps(row, ensure_ascii=False, default=str, indent=2)}")
            if len(rows) > 10:
                lines.append(f"\n... 共 {len(rows)} 条，仅显示前10条")
        return "\n".join(lines)

    # with 上下文支持
    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
