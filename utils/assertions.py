"""
断言工具 —— 全部断言逻辑统一入口

快速索引（按使用场景查找）:
┌─────────────────────────────────────────────────────────────────────┐
│ 场景                          │ 函数                               │
├─────────────────────────────────────────────────────────────────────┤
│ Excel 驱动：校验接口响应字段   │ do_assert(case, res)               │
│ Excel 驱动：校验数据库落盘     │ do_db_assert(case)                 │
│ Excel 驱动：校验二进制响应     │ do_binary_assert(case, res)        │
│ 代码测试：断言 JSONPath 字段   │ assert_jsonpath_exact(resp, $, v)  │
│ 代码测试：断言 DB 值相等       │ assert_db_value(db, sql, expected) │
│ 代码测试：断言 DB 记录存在     │ assert_db_exists(db, sql)          │
│ 代码测试：断言 DB 记录不存在   │ assert_db_not_exists(db, sql)      │
│ 二进制：断言 Content-Type      │ assert_content_type(resp, type)    │
│ 二进制：断言文件大小           │ assert_content_length(resp, min)   │
│ 二进制：断言 SHA-256           │ assert_content_sha256(resp, hash)  │
└─────────────────────────────────────────────────────────────────────┘

设计约束:
  - 禁止全文模糊匹配（已移除）
  - 禁止自定义 validator 回调
  - Excel 驱动用例 check 字段为空时拒绝执行
"""
import json
import allure
import jsonpath
import requests
import mysql.connector
from utils.logger import logger
from utils.db_utils import DbClient
from utils.allure_utils import attach_response


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║                        内部工具（非对外接口）                            ║
# ╚══════════════════════════════════════════════════════════════════════════╝

def _parse_expected(value):
    """将预期值字符串转为 Python 类型（int / bool / dict / list / None）

    举例:
      "200"     → 200 (int)
      "true"    → True (bool)
      "null"    → None
      "操作成功" → "操作成功" (str) — JSON 解析失败则原样返回
    """
    if value is None or isinstance(value, (int, float, bool)):
        return value
    try:
        return json.loads(value.strip())
    except (json.JSONDecodeError, ValueError, TypeError):
        return value


def _fmt(body: dict) -> str:
    """格式化响应体，超过 800 字符截断（避免 Allure 报告撑爆）"""
    text = json.dumps(body, ensure_ascii=False, indent=2)
    return text[:800] + "..." if len(text) > 800 else text


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║                     一、接口响应字段断言                                 ║
# ║           assert_jsonpath_exact → 底层核心  |  do_assert → Excel 封装   ║
# ╚══════════════════════════════════════════════════════════════════════════╝

@allure.step("接口响应字段断言")
def assert_jsonpath_exact(resp, check: str, expected):
    """JSONPath 精准字段等值断言 —— 底层核心，所有响应断言最终都调它

    参数:
        resp:     requests.Response 对象（或 dict）
        check:    JSONPath 表达式（如 $.code / $.data.roleId）
        expected: 预期值（自动类型转换）

    异常:
        ValueError:     check 为空 → 用例格式异常
        AssertionError: JSONPath 无匹配 / 值不相等
    """
    # ── 1. 前置校验 ──
    if not check or not isinstance(check, str):
        logger.error("用例格式错误: check 字段为空或非字符串")
        raise ValueError(
            "\n  ==================== 用例格式异常 ===================="
            "\n  校验标识字段（check）禁止为空或非字符串类型"
            "\n  请检查 Excel 用例的 check 列是否正确填写 JSONPath 表达式"
            "\n  正确示例: $.code   $.data.roleId   $.data.rows[0].roleName"
            "\n  ====================================================="
        )

    body = resp.json() if isinstance(resp, requests.Response) else resp

    # ── 2. JSONPath 提取 ──
    matches = jsonpath.jsonpath(body, check)

    if matches is False:
        logger.warning(f"JSONPath 无匹配 | check={check}")
        if isinstance(resp, requests.Response):
            attach_response(resp)
        raise AssertionError(
            f"\n  [断言失败] JSONPath 无匹配值"
            f"\n  JSONPath: {check}"
            f"\n  预期值:   {expected!r}"
            f"\n  响应体:\n{_fmt(body)}"
        )

    # ── 3. 等值断言（自动类型转换） ──
    actual = matches[0] if isinstance(matches, list) else matches
    expected_typed = _parse_expected(expected)

    if actual != expected_typed:
        logger.warning(
            f"字段值不匹配 | check={check}"
            f" | 预期={expected_typed!r} | 实际={actual!r}"
        )
        if isinstance(resp, requests.Response):
            attach_response(resp)
        raise AssertionError(
            f"\n  [断言失败] 字段值不匹配"
            f"\n  JSONPath: {check}"
            f"\n  预期值:   {expected_typed!r}"
            f"\n  实际值:   {actual!r}"
            f"\n  响应体:\n{_fmt(body)}"
        )

    logger.info(f"字段断言通过 | {check} == {expected_typed!r}")


@allure.step("接口响应字段断言")
def do_assert(case: dict, res):
    """Excel 驱动入口 —— 从 expected_json 列读取多字段断言规则

    格式: {"$.code": 200, "$.msg": "操作成功", "$.data": []}
    支持单字段（{"$.code": 200}）和多字段断言，统一走循环。
    列空白则跳过（不需要断言的用例）。
    """
    raw = case.get("expected_json")
    if not raw:
        return

    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except json.JSONDecodeError as e:
            logger.error(f"expected_json 格式错误: {raw[:100]}")
            raise ValueError(
                f"\n  [Excel 格式错误] expected_json 列非合法 JSON"
                f"\n  内容: {raw[:200]}"
                f"\n  错误: {e}"
            ) from e

    for path, expected in raw.items():
        assert_jsonpath_exact(res, path, expected)


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║                     二、二进制响应断言（文件下载 / 图片导出）           ║
# ║         assert_content_type / length / sha256  →  do_binary_assert      ║
# ╚══════════════════════════════════════════════════════════════════════════╝

@allure.step("二进制响应断言: Content-Type")
def assert_content_type(resp, expected: str):
    """断言响应 Content-Type 包含预期值（如 image/png / application/pdf）"""
    actual = resp.headers.get("Content-Type", "")
    assert expected in actual, (
        f"\n  [断言失败] Content-Type 不匹配"
        f"\n  预期包含: {expected}"
        f"\n  实际值:   {actual}"
    )
    logger.info(f"Content-Type 断言通过 | 包含 {expected!r}")


@allure.step("二进制响应断言: 文件大小")
def assert_content_length(resp, min_bytes: int = 1):
    """断言响应体不小于指定字节数"""
    length = len(resp.content)
    assert length >= min_bytes, (
        f"\n  [断言失败] 响应体过小"
        f"\n  最小预期: {min_bytes} bytes"
        f"\n  实际大小: {length} bytes"
    )
    logger.info(f"文件大小断言通过 | {length} bytes >= {min_bytes}")


@allure.step("二进制响应断言: SHA-256")
def assert_content_sha256(resp, expected_sha256: str):
    """断言响应体 SHA-256 校验值"""
    import hashlib
    actual = hashlib.sha256(resp.content).hexdigest()
    assert actual == expected_sha256, (
        f"\n  [断言失败] SHA-256 不匹配"
        f"\n  预期: {expected_sha256}"
        f"\n  实际: {actual}"
    )
    logger.info(f"SHA-256 断言通过 | {actual}")


@allure.step("二进制响应断言")
def do_binary_assert(case: dict, res):
    """Excel 驱动二进制断言入口 —— 从 case 提取字段后分发到底层断言

    触发条件: response_type == "binary"
    字段依赖（均为可选，至少填一个）:
      - expected_content_type      → assert_content_type()
      - expected_content_min_bytes → assert_content_length()
      - expected_content_sha256    → assert_content_sha256()
    """
    ct = case.get("expected_content_type")
    min_bytes = case.get("expected_content_min_bytes")
    sha256 = case.get("expected_content_sha256")

    if not any([ct, min_bytes, sha256]):
        logger.debug("二进制断言: 无断言字段，跳过")
        return

    if ct:
        assert_content_type(res, str(ct))
    if min_bytes is not None:
        assert_content_length(res, int(min_bytes))
    if sha256:
        assert_content_sha256(res, str(sha256))


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║                     三、数据库校验                                      ║
# ║   do_db_assert → Excel 驱动   |   assert_db_xxx → 代码测试用            ║
# ╚══════════════════════════════════════════════════════════════════════════╝

# ── 3.1 Excel 驱动 ─────────────────────────────────────────────────────────

def do_db_assert(case: dict):
    """Excel 驱动：数据库落盘校验

    触发条件: sql_check 与 sql_expected 同时非空，任一空白则跳过
    异常分层:
      - 查询无结果 / 值不匹配 → AssertionError
      - SQL 执行异常          → RuntimeError
    """
    sql = case.get("sql_check")
    expected = case.get("sql_expected")

    if not sql or expected is None:
        logger.debug("数据库校验: sql_check 或 sql_expected 空白，跳过")
        return

    with allure.step("数据库校验"):
        db = DbClient()
        try:
            result = db.query_one(sql)
            assert result is not None, (
                f"\n  [数据库校验失败] 查询无结果"
                f"\n  SQL: {sql}"
            )
            actual = str(list(result.values())[0])
            assert actual == str(expected), (
                f"\n  [数据库校验失败] 值不匹配"
                f"\n  SQL: {sql}"
                f"\n  预期: {expected}"
                f"\n  实际: {actual}"
            )
            logger.info(f"数据库校验通过 | {actual} == {expected}")

        except AssertionError:
            logger.warning(f"数据库校验失败 | SQL: {sql} | 预期={expected}")
            if result is not None:
                allure.attach(
                    json.dumps({"sql": sql, "expected": expected, "actual": actual},
                               ensure_ascii=False, indent=2),
                    name="数据库校验失败详情",
                    attachment_type=allure.attachment_type.JSON,
                )
            raise

        except mysql.connector.Error as e:
            logger.error(f"SQL 执行异常 | {sql} | {e}")
            raise RuntimeError(
                f"\n  [SQL 执行异常]"
                f"\n  SQL: {sql}"
                f"\n  错误: {e}"
            ) from e

        finally:
            db.close()


# ── 3.2 代码测试用（接受 DbClient 实例，由 fixture 注入）──────────────────

@allure.step("数据库断言: 值相等")
def assert_db_value(db, sql: str, expected, params: tuple = None, column: str = None):
    """断言数据库字段值等于预期

    参数:
        db:       DbClient 实例（来自 db fixture）
        sql:      SELECT 语句，使用 %s 占位符
        expected: 预期值
        params:   SQL 参数元组
        column:   指定字段名，不指定则取结果集第一个字段
    """
    result = db.query_one(sql, params)
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
def assert_db_exists(db, sql: str, params: tuple = None):
    """断言查询结果至少有一条记录（用于验证创建成功）"""
    rows = db.query(sql, params)
    assert len(rows) >= 1, \
        f" 数据库断言失败: 期望记录存在，但未查到\n  SQL: {sql}  params: {params}"
    logger.info(f" 数据库断言通过: 记录存在 ({len(rows)}条)")


@allure.step("数据库断言: 记录不存在")
def assert_db_not_exists(db, sql: str, params: tuple = None):
    """断言查询结果为空（用于验证删除成功）"""
    rows = db.query(sql, params)
    assert len(rows) == 0, \
        f" 数据库断言失败: 期望无记录，但查到 {len(rows)} 条\n  SQL: {sql}  params: {params}"
    logger.info(" 数据库断言通过: 记录不存在")
