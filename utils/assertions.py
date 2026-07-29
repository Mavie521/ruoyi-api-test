"""
断言工具 —— 全部断言逻辑统一入口

包含三大类断言（Allure 差异化装饰）:
  == 接口响应字段断言 ==
  1. assert_jsonpath_exact()   — 底层核心，@allure.step 装饰
  2. do_assert()               — Excel 驱动上层封装，@allure.step 装饰（强制执行）

  == 数据库校验 ==
  3. do_db_assert()            — Excel 驱动专用，局部 with allure.step()（可选执行）
  4. assert_db_value()         — 代码测试用，断言字段值相等
  5. assert_db_exists()        — 代码测试用，断言记录存在
  6. assert_db_not_exists()    — 代码测试用，断言记录不存在

不允许:
  - 全文模糊匹配（已彻底移除）
  - 自定义 validator 回调
  - 无 check 字段的断言执行
"""
import json
import allure
import jsonpath
import requests
import mysql.connector
from utils.logger import logger
from utils.db_utils import DbClient
from utils.allure_utils import attach_response


# ── 类型转换 ─────────────────────────────────────────


def _parse_expected(value):
    """将预期值转为 Python 类型（支持 int / bool / dict / list / None）

    举例:
      "200"       → 200 (int)
      "true"      → True (bool)
      "null"      → None
      "操作成功"   → "操作成功" (str)   ← JSON 解析失败原样返回
    """
    if value is None or isinstance(value, (int, float, bool)):
        return value
    try:
        return json.loads(value.strip())
    except (json.JSONDecodeError, ValueError, TypeError):
        return value


# ── 辅助 ─────────────────────────────────────────────


def _fmt(body: dict) -> str:
    """格式化响应体（截断过长的内容）"""
    text = json.dumps(body, ensure_ascii=False, indent=2)
    return text[:800] + "..." if len(text) > 800 else text


# ===================================================================
# 接口响应字段断言（强制执行，@allure.step 装饰整个函数）
# ===================================================================


@allure.step("接口响应字段断言")
def assert_jsonpath_exact(resp, check: str, expected):
    """
    JSONPath 精准字段等值断言（最底层核心函数）

    参数:
        resp:     requests.Response 对象（或 dict）
        check:    JSONPath 表达式（如 $.code / $.data.roleId）
        expected: 预期值（自动类型转换）

    异常:
        ValueError:     check 为空 → 用例格式异常
        AssertionError: JSONPath 无匹配 / 值不相等
    """
    # ── 前置校验 ──
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

    # ── JSONPath 提取 ──
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

    # ── 等值断言（自动类型转换） ──
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
    """
    Excel 驱动上层封装 —— 从 case 提取 check + expected 后调用 assert_jsonpath_exact

    触发条件: 所有用例（强制）
    字段依赖: check（JSONPath 表达式）+ expected（预期值），缺一不可
    异常分层:
      - check 为空  → logger.error + ValueError
      - expected 为空 → logger.error + ValueError
      - 断言不匹配   → logger.warning + AssertionError
    """
    check = case.get("check")
    expected = case.get("expected")

    if not check:
        logger.error("用例格式异常: check 字段为空")
        raise ValueError(
            "\n  ==================== 用例格式异常 ===================="
            "\n  Excel 用例的 check 列禁止为空"
            "\n  请填写 JSONPath 表达式，示例: $.code   $.data.roleId"
            "\n  ====================================================="
        )

    if expected is None:
        logger.error("用例格式异常: expected 字段为空")
        raise ValueError(
            "\n  ==================== 用例格式异常 ===================="
            "\n  Excel 用例的 expected 列禁止为空"
            "\n  请填写该 JSONPath 字段的预期值"
            "\n  ====================================================="
        )

    assert_jsonpath_exact(res, check, expected)


# ===================================================================
# 二进制响应断言（文件下载 / 图片导出等场景）
# ===================================================================


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
    """
    Excel 驱动二进制断言入口 —— 从 case 提取字段后调用对应底层断言

    触发条件: response_type == "binary" 时执行
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


# ===================================================================
# 数据库校验（可选执行，局部 with allure.step()）
# ===================================================================


def do_db_assert(case: dict):
    """
    数据库落盘校验

    触发条件: sql_check 与 sql_expected 同时非空时执行，任一空白跳过
    字段依赖: sql_check（查询 SQL）+ sql_expected（预期值）
    Allure:   局部 with allure.step()，仅在代码真实执行时显示步骤
    异常分层:
      - 查询无结果 / 值不匹配 → logger.warning + AssertionError
      - SQL 执行异常          → logger.error + RuntimeError
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


# ===================================================================
# 数据库断言（代码测试用，独立函数，接受 DbClient 实例）
# ===================================================================


@allure.step("数据库断言: 值相等")
def assert_db_value(db, sql: str, expected, params: tuple = None, column: str = None):
    """
    断言数据库中的某个字段值等于预期

    参数:
        db:       DbClient 实例（来自 fixture）
        sql:      查询语句（使用 %s 占位符）
        expected: 预期值
        params:   SQL 参数元组
        column:   指定字段名（不指定则取第一个字段）
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
    """断言查询结果至少有一条记录"""
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
