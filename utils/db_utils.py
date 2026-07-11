"""
数据库工具 —— 基于 mysql-connector-python

核心功能:
1. DbClient 封装连接管理（支持 with 语法）
2. query / query_one / execute 三件套
3. assert_value / assert_exists / assert_not_exists 数据库断言
4. 所有操作自动写 Allure 步骤和日志

用法:
    with DbClient() as db:
        user = db.query_one("SELECT * FROM sys_user WHERE user_name=%s", ("admin",))
        db.assert_value("SELECT status FROM sys_user WHERE user_id=%s", expected="0", params=(1,))

注意事项:
    - 所有SQL参数使用 %s 占位符传参（防SQL注入）
    - 查询返回 list[dict]（dictionary=True）
    - 断言失败会抛出 AssertionError + 详细的 Allure 附件
"""
import time
import json
import allure
import mysql.connector
from config.config import DB_CONFIG
from utils.logger import logger


class DbClient:
    """数据库客户端 —— 连接复用，支持 with 上下文"""

    def __init__(self, config: dict = None):
        self.config = config or {**DB_CONFIG}
        # mysql.connector 的 database 参数名是 database，不用改
        self._conn = None

    # ---------------------------------------------------------
    # 连接管理
    # ---------------------------------------------------------
    def connect(self):
        """建立数据库连接（首次调用时创建，后续复用）"""
        if self._conn is None or not self._conn.is_connected():
            self._conn = mysql.connector.connect(
                host=self.config["host"],
                port=self.config["port"],
                database=self.config["database"],
                user=self.config["user"],
                password=self.config["password"],
                charset=self.config.get("charset", "utf8"),
                use_pure=True,
                autocommit=True,  # 必须！否则 SELECT 看不到其他连接的写入
                consume_results=True,
            )
            logger.info(
                f"DB 已连接: {self.config['host']}:{self.config['port']}/{self.config['database']}"
            )
        return self._conn

    def close(self):
        """关闭数据库连接"""
        if self._conn and self._conn.is_connected():
            self._conn.close()
            self._conn = None
            logger.info("DB 连接已关闭")

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
    def execute(self, sql: str, params: tuple = None) -> int:
        """
        执行 INSERT / UPDATE / DELETE
        返回受影响行数，自动 commit
        """
        conn = self.connect()
        start = time.time()
        cur = conn.cursor()
        cur.execute(sql, params)
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
                     column: str = None, msg: str = None):
        """
        断言数据库中的某个字段值等于预期
        - sql: 查询语句
        - expected: 预期值
        - params: SQL参数
        - column: 指定字段名（不指定则取第一个字段）
        """
        result = self.query_one(sql, params)
        assert result is not None, \
            f"❌ 数据库断言失败: 查询无结果\n  SQL: {sql}  params: {params}"

        if column:
            actual = result.get(column)
        else:
            actual = list(result.values())[0] if result else None

        assert actual == expected, (
            f"❌ 数据库断言失败: 值不匹配\n"
            f"  SQL: {sql}\n"
            f"  参数: {params}\n"
            f"  字段: {column or '(自动取第一个字段)'}\n"
            f"  预期: {repr(expected)}\n"
            f"  实际: {repr(actual)}"
        )

        logger.info(f"✅ 数据库断言通过: {actual} == {expected}")
        return actual

    @allure.step("数据库断言: 记录存在")
    def assert_exists(self, sql: str, params: tuple = None):
        """断言查询结果至少有一条记录"""
        rows = self.query(sql, params)
        assert len(rows) >= 1, \
            f"❌ 数据库断言失败: 期望记录存在，但未查到\n  SQL: {sql}  params: {params}"
        logger.info(f"✅ 数据库断言通过: 记录存在 ({len(rows)}条)")

    @allure.step("数据库断言: 记录不存在")
    def assert_not_exists(self, sql: str, params: tuple = None):
        """断言查询结果为空（用于验证删除成功）"""
        rows = self.query(sql, params)
        assert len(rows) == 0, \
            f"❌ 数据库断言失败: 期望无记录，但查到 {len(rows)} 条\n  SQL: {sql}  params: {params}"
        logger.info("✅ 数据库断言通过: 记录不存在")

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
