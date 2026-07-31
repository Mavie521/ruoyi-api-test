"""
数据库工具 —— 连接池 + 查询/执行

┌─────────────────────────────────────────────────────────────────────┐
│ 这个文件做了什么？                                                  │
├─────────────────────────────────────────────────────────────────────┤
│ 1. 维护一个全局连接池 _POOL（整个测试会话只有 1 个，不会反复建连） │
│ 2. DbClient 从池里借用连接，用完归还（不是真正关闭）               │
│ 3. 提供 query / query_one / execute 三个方法，自动写 Allure 报告   │
│                                                                     │
│ 面试可以这样讲：                                                    │
│ "连接池 singleton 模式，避免每条用例都建连/断连，                    │
│  10 个连接足够应付 xdist 并行。每次查询自动 attach 到 Allure。"    │
└─────────────────────────────────────────────────────────────────────┘

用法:
    # 方式1：fixture 注入（推荐，测试用例里用这个）
    def test_xxx(db):
        user = db.query_one("SELECT * FROM sys_user WHERE user_name=%s", ("admin",))

    # 方式2：with 语句（工具函数内部用）
    with DbClient() as db:
        rows = db.query("SELECT * FROM sys_role")

数据库断言已移至 utils.assertions:
    assert_db_value / assert_db_exists / assert_db_not_exists
"""
import time
import json
import allure
from mysql.connector.pooling import MySQLConnectionPool
from config.config import DB_CONFIG
from utils.logger import logger

# ═══════════════════════════════════════════════════════════════════════════
# 全局连接池（单例模式）
# ═══════════════════════════════════════════════════════════════════════════

_POOL = None  # 模块级私有变量，整个 Python 进程只有这一个池


def _get_pool():
    """获取全局唯一的连接池（第一次调用时创建，之后直接返回）

    为什么用连接池而不是每次 new 连接？
      - 创建/销毁 TCP 连接很慢（~50ms），连接池预建 10 个放着
      - pool_reset_session=True：每次借出前自动重置会话状态
      - autocommit=True：每条 SQL 自动提交，不用手动 commit
      - consume_results=True：自动消费未读结果，防止"Unread result"报错
    """
    global _POOL  # 告诉 Python：我要修改模块级的 _POOL 变量
    if _POOL is None:
        config = {**DB_CONFIG}  # 解包复制一份，防止意外修改原配置
        _POOL = MySQLConnectionPool(
            pool_name="ry_pool",
            pool_size=10,           # 最多同时 10 个连接（配合 xdist 并行）
            pool_reset_session=True,
            host=config["host"],
            port=config["port"],
            database=config["database"],
            user=config["user"],
            password=config["password"],
            charset=config.get("charset", "utf8"),
            use_pure=True,          # 纯 Python 实现，不需要装 MySQL C 客户端
            autocommit=True,
            consume_results=True,
        )
        logger.info(f"连接池已创建: {config['host']}:{config['port']}/{config['database']}")
    return _POOL


# ═══════════════════════════════════════════════════════════════════════════
# DbClient —— 数据库操作统一入口
# ═══════════════════════════════════════════════════════════════════════════

class DbClient:
    """数据库客户端：从连接池借连接 → 执行 SQL → 归还连接

    设计要点：
      - connect() 不是真建连，是从池里"借"一个
      - close()  不是真断连，是"还"回池里
      - __enter__ / __exit__ 支持 with 语法
    """

    def __init__(self, config: dict = None):
        self.config = config or {**DB_CONFIG}
        self._conn = None  # 当前持有的连接引用

    # ── 连接管理 ──────────────────────────────────────────

    def connect(self):
        """从连接池借一个连接（如果之前的断了就重新借）"""
        if self._conn is None or not self._conn.is_connected():
            self._conn = _get_pool().get_connection()
        return self._conn

    def close(self):
        """归还连接到池（不是真正关闭 TCP）"""
        if self._conn:
            try:
                self._conn.close()  # 连接池的 close() = 归还
            except Exception:
                pass  # 归还不成功就算了，不影响测试
            self._conn = None

    # ── SQL 操作 ──────────────────────────────────────────

    @allure.step("SQL 查询")
    def query(self, sql: str, params: tuple = None) -> list:
        """执行 SELECT 查询，返回 list[dict]

        参数:
            sql:    SQL 语句，用 %s 做占位符（不是 f-string，防注入）
            params: 占位符对应的值，如 ("admin",)
        返回:
            list[dict]，每行是一个 {"列名": 值} 的字典
            查不到返回空列表 []

        为什么用 %s 而不是 f-string？
          f"WHERE name='{name}'" → 用户输入 ' OR 1=1-- 就 SQL 注入了
          cursor.execute(sql, (name,)) → 驱动自动转义，安全
        """
        conn = self.connect()
        cur = conn.cursor(dictionary=True)  # dictionary=True → 返回 dict 而非 tuple
        cur.execute(sql, params)
        rows = cur.fetchall()
        cur.close()
        result = list(rows) if rows else []
        # 写 Allure 报告附件
        body = self._fmt(sql, params, result)
        allure.attach(body, name="查询结果", attachment_type=allure.attachment_type.TEXT)
        logger.debug(f"  SQL → {len(result)} 条结果")
        return result

    def query_one(self, sql: str, params: tuple = None) -> dict:
        """查询单条记录，返回 dict 或 None

        本质就是调 query() 然后取第一行。
        查不到时返回 None 而不是抛异常，方便调用方做 if row: ... 判断。
        """
        rows = self.query(sql, params)
        return rows[0] if rows else None

    @allure.step("SQL 执行")
    def execute(self, sql: str, params: tuple = None, commit: bool = True) -> int:
        """执行 INSERT / UPDATE / DELETE，返回受影响行数

        commit=True（默认）：自动提交。MySQL 连接池的 autocommit 已开启，
        这里再 commit 一次是为了兼容某些需要显式提交的场景。
        """
        conn = self.connect()
        cur = conn.cursor()  # 不需要 dictionary=True，写操作不读数据
        cur.execute(sql, params)
        if commit:
            conn.commit()
        affected = cur.rowcount  # 受影响的行数（如 UPDATE 了 3 行 → 3）
        cur.close()
        allure.attach(
            f"SQL: {sql}\n参数: {params}\n影响行数: {affected}",
            name="执行结果",
        )
        logger.debug(f"  SQL → {affected} 行受影响")
        return affected

    # ── 辅助方法 ──────────────────────────────────────────

    @staticmethod
    def _fmt(sql: str, params: tuple, rows: list) -> str:
        """把查询结果格式化成可读文本（Allure 附件用，最多显示前 10 条）"""
        lines = [f"SQL: {sql}", f"参数: {params}", f"结果数: {len(rows)}", ""]
        for i, row in enumerate(rows[:10], 1):
            lines.append(f"[{i}] {json.dumps(row, ensure_ascii=False, default=str, indent=2)}")
        if len(rows) > 10:
            lines.append(f"\n... 共 {len(rows)} 条，仅显示前 10 条")
        return "\n".join(lines)

    # ── with 语句支持 ─────────────────────────────────────
    # 有了这两个方法，就可以写:
    #   with DbClient() as db:
    #       db.query("SELECT ...")
    # 退出 with 块时自动调用 close() 归还连接

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
