"""
SQLite 数据库 —— 建表 + 连接管理 + CRUD

表结构 (一期):
  case_cache     — pytest --collect-only 用例缓存
  runs           — 执行记录
  run_results    — 单条用例执行结果

数据库文件位置: cache/test_platform.db (由 config.py 统一管理)
"""
import sqlite3
import json
import threading
from typing import Optional
from datetime import datetime
from .config import DB_PATH, CACHE_DIR

# ============================================================
# 连接管理
# ============================================================
_local = threading.local()


def _get_conn() -> sqlite3.Connection:
    if not hasattr(_local, "conn") or _local.conn is None:
        _local.conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        _local.conn.row_factory = sqlite3.Row
        _local.conn.execute("PRAGMA journal_mode=WAL")
        _local.conn.execute("PRAGMA foreign_keys=ON")
    return _local.conn


def init_db():
    """初始化所有表（幂等操作）"""
    conn = _get_conn()
    conn.executescript("""
        -- 用例缓存表
        CREATE TABLE IF NOT EXISTS case_cache (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            nodeid       TEXT UNIQUE NOT NULL,
            module       TEXT NOT NULL,
            class_name   TEXT DEFAULT '',
            func_name    TEXT NOT NULL,
            markers      TEXT DEFAULT '[]',
            collected_at TEXT DEFAULT (datetime('now','localtime'))
        );
        CREATE INDEX IF NOT EXISTS idx_case_module ON case_cache(module);

        -- 执行记录表
        CREATE TABLE IF NOT EXISTS runs (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            run_tag       TEXT UNIQUE NOT NULL,
            status        TEXT DEFAULT 'pending',
            environment   TEXT DEFAULT 'dev',
            markers       TEXT DEFAULT '',
            test_path     TEXT DEFAULT 'tests/',
            keyword       TEXT DEFAULT '',
            extra_args    TEXT DEFAULT '',
            total_tests   INTEGER DEFAULT 0,
            passed_tests  INTEGER DEFAULT 0,
            failed_tests  INTEGER DEFAULT 0,
            skipped_tests INTEGER DEFAULT 0,
            error_tests   INTEGER DEFAULT 0,
            duration_sec  REAL,
            started_at    TEXT,
            finished_at   TEXT,
            created_at    TEXT DEFAULT (datetime('now','localtime')),
            output_log    TEXT DEFAULT '',
            allure_dir    TEXT DEFAULT ''
        );
        CREATE INDEX IF NOT EXISTS idx_runs_created ON runs(created_at);

        -- 单条用例结果表
        CREATE TABLE IF NOT EXISTS run_results (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id       INTEGER NOT NULL REFERENCES runs(id) ON DELETE CASCADE,
            test_name    TEXT NOT NULL,
            nodeid       TEXT DEFAULT '',
            outcome      TEXT DEFAULT 'unknown',
            duration_sec REAL DEFAULT 0,
            message      TEXT DEFAULT '',
            ai_analysis  TEXT DEFAULT ''
        );
        CREATE INDEX IF NOT EXISTS idx_results_run ON run_results(run_id);

        -- 环境管理表
        CREATE TABLE IF NOT EXISTS environments (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT UNIQUE NOT NULL,
            base_url    TEXT NOT NULL,
            description TEXT DEFAULT '',
            is_active   INTEGER DEFAULT 1,
            created_at  TEXT DEFAULT (datetime('now','localtime'))
        );

        -- Mock 规则表
        CREATE TABLE IF NOT EXISTS mock_rules (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            name            TEXT NOT NULL,
            path            TEXT NOT NULL,
            http_method     TEXT NOT NULL DEFAULT 'GET',
            status_code     INTEGER NOT NULL DEFAULT 200,
            response_body   TEXT NOT NULL DEFAULT '{}',
            delay_ms        INTEGER DEFAULT 0,
            enabled         INTEGER DEFAULT 1,
            description     TEXT DEFAULT '',
            created_at      TEXT DEFAULT (datetime('now','localtime')),
            updated_at      TEXT DEFAULT (datetime('now','localtime'))
        );

        -- Mock 调用日志表
        CREATE TABLE IF NOT EXISTS mock_logs (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            rule_id         INTEGER REFERENCES mock_rules(id) ON DELETE SET NULL,
            rule_name       TEXT DEFAULT '',
            path            TEXT NOT NULL,
            http_method     TEXT NOT NULL,
            request_body    TEXT DEFAULT '',
            request_headers TEXT DEFAULT '',
            status_code     INTEGER NOT NULL,
            response_body   TEXT DEFAULT '',
            matched         INTEGER DEFAULT 1,
            created_at      TEXT DEFAULT (datetime('now','localtime'))
        );
        CREATE INDEX IF NOT EXISTS idx_mock_logs_created ON mock_logs(created_at);

        -- 钉钉通知配置表
        CREATE TABLE IF NOT EXISTS dingtalk_config (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            webhook_url TEXT NOT NULL DEFAULT '',
            secret      TEXT NOT NULL DEFAULT '',
            enabled     INTEGER DEFAULT 0,
            notify_on   TEXT DEFAULT 'all'
        );
    """)
    conn.commit()


def close_db():
    """关闭当前线程的数据库连接"""
    if hasattr(_local, "conn") and _local.conn:
        _local.conn.close()
        _local.conn = None


# ============================================================
# 用例缓存 CRUD
# ============================================================

def clear_case_cache():
    """清空用例缓存表"""
    conn = _get_conn()
    conn.execute("DELETE FROM case_cache")
    conn.commit()


def insert_case(nodeid: str, module: str, class_name: str,
                func_name: str, markers: list):
    """插入单条用例缓存"""
    conn = _get_conn()
    conn.execute(
        """INSERT OR REPLACE INTO case_cache (nodeid, module, class_name, func_name, markers)
           VALUES (?, ?, ?, ?, ?)""",
        (nodeid, module, class_name, func_name, json.dumps(markers)),
    )
    conn.commit()


def get_modules() -> list[dict]:
    """获取模块列表（含用例数量统计）"""
    conn = _get_conn()
    rows = conn.execute("""
        SELECT module, COUNT(*) as case_count
        FROM case_cache
        GROUP BY module
        ORDER BY module
    """).fetchall()
    return [{"module": r["module"], "case_count": r["case_count"]} for r in rows]


def get_cases_by_module(module: str) -> list[dict]:
    """获取指定模块下的所有用例"""
    conn = _get_conn()
    rows = conn.execute(
        "SELECT * FROM case_cache WHERE module=? ORDER BY id",
        (module,),
    ).fetchall()
    result = []
    for r in rows:
        d = dict(r)
        d["markers"] = json.loads(d.get("markers", "[]"))
        result.append(d)
    return result


# ============================================================
# 执行记录 CRUD
# ============================================================

def create_run(environment: str = "dev", markers: str = "",
               test_path: str = "tests/", keyword: str = "",
               extra_args: str = "") -> dict:
    """创建执行记录，返回 dict"""
    tag = _gen_tag()
    conn = _get_conn()
    cur = conn.execute(
        """INSERT INTO runs (run_tag, environment, markers, test_path, keyword, extra_args)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (tag, environment, markers, test_path, keyword, extra_args),
    )
    conn.commit()
    return get_run(cur.lastrowid)


def update_run(run_id: int, **kwargs) -> dict:
    """更新执行记录的部分字段"""
    allowed = {
        "status", "total_tests", "passed_tests", "failed_tests",
        "skipped_tests", "error_tests", "duration_sec",
        "started_at", "finished_at", "output_log", "allure_dir",
    }
    updates = {k: v for k, v in kwargs.items() if k in allowed}
    if not updates:
        return get_run(run_id)
    sets = ", ".join(f"{k}=?" for k in updates)
    vals = list(updates.values()) + [run_id]
    conn = _get_conn()
    conn.execute(f"UPDATE runs SET {sets} WHERE id=?", vals)
    conn.commit()
    return get_run(run_id)


def get_run(run_id: int) -> Optional[dict]:
    """获取单条执行记录"""
    row = _get_conn().execute("SELECT * FROM runs WHERE id=?", (run_id,)).fetchone()
    return dict(row) if row else None


def list_runs(page: int = 1, page_size: int = 20) -> dict:
    """分页获取执行记录列表（按创建时间倒序）"""
    conn = _get_conn()
    offset = (page - 1) * page_size
    rows = conn.execute(
        "SELECT * FROM runs ORDER BY created_at DESC LIMIT ? OFFSET ?",
        (page_size, offset),
    ).fetchall()
    total = conn.execute("SELECT COUNT(*) FROM runs").fetchone()[0]
    return {"items": [dict(r) for r in rows], "total": total}


def delete_run(run_id: int):
    """删除执行记录及关联结果"""
    conn = _get_conn()
    conn.execute("DELETE FROM run_results WHERE run_id=?", (run_id,))
    conn.execute("DELETE FROM runs WHERE id=?", (run_id,))
    conn.commit()


def is_running() -> bool:
    """检查是否有正在执行的任务"""
    row = _get_conn().execute(
        "SELECT COUNT(*) FROM runs WHERE status='running'"
    ).fetchone()
    return row[0] > 0


# ============================================================
# 用例结果 CRUD
# ============================================================

def insert_result(run_id: int, test_name: str, outcome: str,
                  nodeid: str = "", duration_sec: float = 0,
                  message: str = "", ai_analysis: str = ""):
    """插入单条用例结果"""
    conn = _get_conn()
    conn.execute(
        """INSERT INTO run_results (run_id, test_name, nodeid, outcome, duration_sec, message, ai_analysis)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (run_id, test_name, nodeid, outcome, duration_sec, message, ai_analysis),
    )
    conn.commit()


def update_result_analysis(result_id: int, ai_analysis: str):
    _get_conn().execute("UPDATE run_results SET ai_analysis=? WHERE id=?", (ai_analysis, result_id))
    _get_conn().commit()


def get_results(run_id: int, outcome: str = None) -> list[dict]:
    """获取某次执行的所有用例结果"""
    conn = _get_conn()
    if outcome:
        rows = conn.execute(
            "SELECT * FROM run_results WHERE run_id=? AND outcome=? ORDER BY id",
            (run_id, outcome),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM run_results WHERE run_id=? ORDER BY id",
            (run_id,),
        ).fetchall()
    return [dict(r) for r in rows]


# ============================================================
# 仪表盘统计
# ============================================================

def get_dashboard_stats() -> dict:
    """聚合仪表盘统计数据"""
    conn = _get_conn()
    runs_total = conn.execute("SELECT COUNT(*) FROM runs").fetchone()[0]
    tests_total = conn.execute(
        "SELECT COALESCE(SUM(total_tests), 0) FROM runs"
    ).fetchone()[0]
    passed_total = conn.execute(
        "SELECT COALESCE(SUM(passed_tests), 0) FROM runs"
    ).fetchone()[0]
    pass_rate = round(passed_total / tests_total, 3) if tests_total > 0 else 0
    case_count = conn.execute("SELECT COUNT(*) FROM case_cache").fetchone()[0]

    latest = conn.execute(
        "SELECT * FROM runs WHERE status != 'pending' ORDER BY created_at DESC LIMIT 1"
    ).fetchone()

    recent = conn.execute(
        "SELECT * FROM runs ORDER BY created_at DESC LIMIT 10"
    ).fetchall()

    return {
        "runs_total": runs_total,
        "tests_total": tests_total,
        "pass_rate": pass_rate,
        "case_count": case_count,
        "latest_run": dict(latest) if latest else None,
        "recent_runs": [dict(r) for r in recent],
    }


# ============================================================
# 辅助
# ============================================================

def _gen_tag() -> str:
    """生成 run-YYYYMMDD-NNN 格式的执行标签"""
    today = datetime.now().strftime("%Y%m%d")
    conn = _get_conn()
    count = conn.execute(
        "SELECT COUNT(*) FROM runs WHERE run_tag LIKE ?",
        (f"run-{today}-%",),
    ).fetchone()[0]
    return f"run-{today}-{count + 1:03d}"


# ============================================================
# 环境管理 CRUD
# ============================================================

def list_environments() -> list[dict]:
    rows = _get_conn().execute("SELECT * FROM environments ORDER BY id").fetchall()
    return [dict(r) for r in rows]


def get_environment(env_id: int) -> Optional[dict]:
    row = _get_conn().execute("SELECT * FROM environments WHERE id=?", (env_id,)).fetchone()
    return dict(row) if row else None


def create_environment(name: str, base_url: str, description: str = "") -> int:
    conn = _get_conn()
    cur = conn.execute(
        "INSERT INTO environments (name, base_url, description) VALUES (?, ?, ?)",
        (name, base_url, description),
    )
    conn.commit()
    return cur.lastrowid


def update_environment(env_id: int, **kwargs) -> bool:
    allowed = {"name", "base_url", "description", "is_active"}
    updates = {k: v for k, v in kwargs.items() if k in allowed}
    if not updates:
        return False
    sets = ", ".join(f"{k}=?" for k in updates)
    vals = list(updates.values()) + [env_id]
    _get_conn().execute(f"UPDATE environments SET {sets} WHERE id=?", vals)
    _get_conn().commit()
    return True


def delete_environment(env_id: int):
    conn = _get_conn()
    conn.execute("DELETE FROM environments WHERE id=?", (env_id,))
    conn.commit()


# ============================================================
# 钉钉配置 CRUD
# ============================================================

def get_dingtalk_config() -> dict:
    from utils.crypto_utils import decrypt
    row = _get_conn().execute("SELECT * FROM dingtalk_config WHERE id=1").fetchone()
    if not row:
        # 首次自动创建默认行
        _get_conn().execute("INSERT INTO dingtalk_config (id) VALUES (1)")
        _get_conn().commit()
        row = _get_conn().execute("SELECT * FROM dingtalk_config WHERE id=1").fetchone()
    config = dict(row)
    for field in ("secret", "webhook_url"):
        config[field] = decrypt(config.get(field, ""))
    return config


def update_dingtalk_config(**kwargs) -> bool:
    from utils.crypto_utils import encrypt
    allowed = {"webhook_url", "secret", "enabled", "notify_on"}
    updates = {k: v for k, v in kwargs.items() if k in allowed}
    for field in ("secret", "webhook_url"):
        if field in updates and updates[field]:
            updates[field] = encrypt(updates[field])
    if not updates:
        return False
    sets = ", ".join(f"{k}=?" for k in updates)
    vals = list(updates.values()) + [1]
    _get_conn().execute(f"UPDATE dingtalk_config SET {sets} WHERE id=?", vals)
    _get_conn().commit()
    return True


# ============================================================
# Mock 规则 CRUD
# ============================================================

def list_mock_rules() -> list[dict]:
    rows = _get_conn().execute("SELECT * FROM mock_rules ORDER BY id").fetchall()
    return [dict(r) for r in rows]


def get_mock_rule(rule_id: int) -> Optional[dict]:
    row = _get_conn().execute("SELECT * FROM mock_rules WHERE id=?", (rule_id,)).fetchone()
    return dict(row) if row else None


def create_mock_rule(name: str, path: str, http_method: str = "GET",
                     status_code: int = 200, response_body: str = "{}",
                     delay_ms: int = 0, description: str = "") -> int:
    conn = _get_conn()
    cur = conn.execute(
        """INSERT INTO mock_rules (name, path, http_method, status_code, response_body, delay_ms, description)
           VALUES (?,?,?,?,?,?,?)""",
        (name, path, http_method, status_code, response_body, delay_ms, description),
    )
    conn.commit()
    return cur.lastrowid


def update_mock_rule(rule_id: int, **kwargs) -> bool:
    allowed = {"name", "path", "http_method", "status_code", "response_body", "delay_ms", "description"}
    updates = {k: v for k, v in kwargs.items() if k in allowed}
    if not updates:
        return False
    updates["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sets = ", ".join(f"{k}=?" for k in updates)
    vals = list(updates.values()) + [rule_id]
    _get_conn().execute(f"UPDATE mock_rules SET {sets} WHERE id=?", vals)
    _get_conn().commit()
    return True


def delete_mock_rule(rule_id: int):
    _get_conn().execute("DELETE FROM mock_rules WHERE id=?", (rule_id,))
    _get_conn().commit()


def toggle_mock_rule(rule_id: int) -> dict:
    rule = get_mock_rule(rule_id)
    if not rule:
        return None
    new_enabled = 0 if rule["enabled"] else 1
    _get_conn().execute("UPDATE mock_rules SET enabled=? WHERE id=?", (new_enabled, rule_id))
    _get_conn().commit()
    return get_mock_rule(rule_id)


# ============================================================
# Mock 日志
# ============================================================

def insert_mock_log(rule_id, rule_name, path, http_method, request_body,
                     request_headers, status_code, response_body, matched) -> int:
    conn = _get_conn()
    cur = conn.execute(
        """INSERT INTO mock_logs (rule_id, rule_name, path, http_method, request_body,
           request_headers, status_code, response_body, matched)
           VALUES (?,?,?,?,?,?,?,?,?)""",
        (rule_id, rule_name, path, http_method, request_body or "",
         request_headers or "", status_code, response_body or "", matched),
    )
    conn.commit()
    return cur.lastrowid


def list_mock_logs(page: int = 1, page_size: int = 50) -> dict:
    conn = _get_conn()
    offset = (page - 1) * page_size
    rows = conn.execute(
        "SELECT * FROM mock_logs ORDER BY created_at DESC LIMIT ? OFFSET ?",
        (page_size, offset),
    ).fetchall()
    total = conn.execute("SELECT COUNT(*) FROM mock_logs").fetchone()[0]
    return {"items": [dict(r) for r in rows], "total": total}


def clear_mock_logs():
    _get_conn().execute("DELETE FROM mock_logs")
    _get_conn().commit()
