"""
数据提取工具 —— JSON 提取 + SQL 提取，写入全局变量池

两条提取逻辑（均为可选执行，局部 with allure.step()）:
  1. do_extract_json() — 从接口响应 JSON 中按 JSONPath 提取变量
  2. do_extract_sql()  — 从数据库查询结果中提取变量

触发条件:
  - jsonExData 列非空 → do_extract_json()
  - sqlExData  列非空 → do_extract_sql()
"""
import json
import allure
import jsonpath
import requests
import mysql.connector
from utils.logger import logger
from utils.db_utils import DbClient


# ===================================================================
# JSON 数据提取（可选执行，局部 with allure.step()）
# ===================================================================


def do_extract_json(case: dict, res, global_vars: dict):
    """
    从接口响应 JSON 中提取变量 → 全局变量池

    触发条件: jsonExData 列非空时执行，空白跳过
    字段格式: {"变量名": "JSONPath表达式"}
    Allure:   局部 with allure.step()，仅在代码真实执行时显示步骤
    异常分层:
      - JSON 解析异常    → logger.error + ValueError（阻断）
      - JSONPath 无匹配  → logger.warning（跳过，不影响主流程）
    """
    raw = case.get("jsonExData")
    if not raw:
        return

    with allure.step("JSON 数据提取"):
        if isinstance(raw, str):
            try:
                ex_dict = json.loads(raw)
            except json.JSONDecodeError as e:
                logger.error(f"jsonExData JSON 解析失败 | {raw} | {e}")
                raise ValueError(
                    f"\n  [JSON 提取格式错误] jsonExData 列非合法 JSON 字典"
                    f"\n  内容: {raw}"
                    f"\n  错误: {e}"
                ) from e
        else:
            ex_dict = raw

        if not isinstance(ex_dict, dict):
            logger.error(f"jsonExData 须为 JSON 字典 | 实际类型: {type(ex_dict).__name__}")
            raise ValueError(
                f"\n  [JSON 提取格式错误] jsonExData 须为 JSON 字典（key-value 格式）"
                f"\n  内容: {raw}"
            )

        body = res.json() if isinstance(res, requests.Response) else res
        for var_name, jp_expr in ex_dict.items():
            vals = jsonpath.jsonpath(body, jp_expr)
            if vals:
                global_vars[var_name] = vals[0]
                logger.info(f"JSON 提取 | {var_name} = {vals[0]} (from {jp_expr})")
            else:
                logger.warning(f"JSON 提取无匹配 | {var_name} | {jp_expr}")


# ===================================================================
# SQL 数据提取（可选执行，局部 with allure.step()）
# ===================================================================


def do_extract_sql(case: dict, global_vars: dict):
    """
    从数据库查询结果中提取变量 → 全局变量池

    触发条件: sqlExData 列非空时执行，空白跳过
    字段格式: {"变量名": "查询SQL语句"}
    Allure:   局部 with allure.step()，仅在代码真实执行时显示步骤
    异常分层:
      - JSON 解析异常  → logger.error + ValueError（阻断）
      - SQL 执行异常   → logger.error（跳过，不影响主流程）
      - 查询无结果     → logger.warning
    """
    raw = case.get("sqlExData")
    if not raw:
        return

    with allure.step("SQL 数据提取"):
        if isinstance(raw, str):
            try:
                ex_dict = json.loads(raw)
            except json.JSONDecodeError as e:
                logger.error(f"sqlExData JSON 解析失败 | {raw} | {e}")
                raise ValueError(
                    f"\n  [SQL 提取格式错误] sqlExData 列非合法 JSON 字典"
                    f"\n  内容: {raw}"
                    f"\n  错误: {e}"
                ) from e
        else:
            ex_dict = raw

        if not isinstance(ex_dict, dict):
            logger.error(f"sqlExData 须为 JSON 字典 | 实际类型: {type(ex_dict).__name__}")
            raise ValueError(
                f"\n  [SQL 提取格式错误] sqlExData 须为 JSON 字典（key-value 格式）"
                f"\n  内容: {raw}"
            )

        db = DbClient()
        try:
            for var_name, sql in ex_dict.items():
                try:
                    row = db.query_one(sql)
                    if row:
                        val = list(row.values())[0]
                        global_vars[var_name] = val
                        logger.info(f"SQL 提取 | {var_name} = {val}")
                    else:
                        logger.warning(f"SQL 提取无结果 | {var_name} | {sql}")
                except mysql.connector.Error as e:
                    logger.error(f"SQL 提取执行异常 | {var_name} | {sql} | {e}")
                    continue
        finally:
            db.close()
