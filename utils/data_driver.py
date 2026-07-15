"""
Excel数据驱动核心引擎

三层架构：
  HTTP请求层: method/path/headers/params/json/data/files
  校验层:     check+expected(JSONPath) / sql_check+sql_expected(DB)
  提取层:     jsonExData(响应) / sqlExData(数据库) → 后续用例复用

一条Excel用例执行流程:
  render_case({{TOKEN}}) → send_request() → do_assert() + do_db_assert() → do_extract()
"""
import json
import allure
import requests
import jsonpath
import mysql.connector
from jinja2 import Template
from config.config import BASE_URL
from utils.logger import logger
from utils.db_utils import DbClient
from utils.allure_utils import attach_request, attach_response


def render_case(case: dict, global_vars: dict) -> dict:
    """Jinja2渲染 {{变量}}"""
    case_str = json.dumps(case, ensure_ascii=False)
    return json.loads(Template(case_str).render(global_vars))


def _parse_field(value):
    """Excel 字符串JSON → Python对象"""
    if isinstance(value, str):
        value = value.strip()
        if value.startswith(("{", "[")):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
    return value


def send_request(case: dict) -> requests.Response:
    """
    发送HTTP请求
    支持: method/path/headers/params/json/data/files
    """
    url = BASE_URL.rstrip("/") + case.get("path", "")
    headers = _parse_field(case.get("headers"))
    params = _parse_field(case.get("params"))
    json_body = _parse_field(case.get("json"))
    form_data = _parse_field(case.get("data"))
    files = _parse_field(case.get("files"))
    method = case.get("method", "get").lower()

    kwargs = {"headers": headers, "params": params, "timeout": 10}
    if json_body:
        kwargs["json"] = json_body
    if form_data:
        kwargs["data"] = form_data
    if files:
        kwargs["files"] = files

    logger.info(f"请求: {method.upper()} {url}")
    res = requests.request(method, url, **kwargs)
    attach_request(method, url, headers=headers, params=params, json=json_body, data=form_data)
    attach_response(res)
    return res


@allure.step("HTTP响应断言")
def do_assert(case: dict, res: requests.Response):
    """JSONPath断言 / 包含断言"""
    check = case.get("check")
    expected = str(case.get("expected", ""))
    if check:
        actual_list = jsonpath.jsonpath(res.json(), check)
        assert actual_list is not False, f"JSONPath未匹配: {check}"
        actual = str(actual_list[0])
        assert actual == expected, f"JSONPath断言失败: {check} 预期={expected} 实际={actual}"
        logger.info(f"   JSONPath断言通过: {check} == {expected}")
    else:
        assert expected in res.text, f"包含断言失败: 未找到'{expected}'"
        logger.info("   包含断言通过")


@allure.step("数据库断言")
def do_db_assert(case: dict):
    """sql_check + sql_expected 数据库落盘校验"""
    sql = case.get("sql_check")
    expected = case.get("sql_expected")
    if not sql:
        return
    db = DbClient()
    try:
        result = db.query_one(sql)
        assert result is not None, f"数据库查询无结果: {sql}"
        actual = str(list(result.values())[0])
        assert actual == str(expected), f"数据库断言失败: 预期={expected} 实际={actual}"
        logger.info(f"   数据库断言通过: {actual} == {expected}")
    finally:
        db.close()


def do_extract(case: dict, res: requests.Response, global_vars: dict):
    """
    提取变量到全局变量供后续用例复用
    - jsonExData: 从响应JSON提取 {"VAR_NAME": "$..jsonpath"}
    - sqlExData:  从数据库提取   {"VAR_NAME": "SELECT ..."}
    """
    db = DbClient() if case.get("sqlExData") else None

    # jsonExData: 从响应提取
    ex_json = case.get("jsonExData")
    if isinstance(ex_json, str):
        ex_json = json.loads(ex_json)
    if ex_json:
        for var_name, jp_expr in ex_json.items():
            vals = jsonpath.jsonpath(res.json(), jp_expr)
            if vals:
                global_vars[var_name] = vals[0]
                logger.info(f"   提取(JSON): {var_name} = {vals[0]}")

    # sqlExData: 从数据库提取
    ex_sql = case.get("sqlExData")
    if isinstance(ex_sql, str):
        ex_sql = json.loads(ex_sql)
    if ex_sql:
        for var_name, sql in ex_sql.items():
            try:
                row = db.query_one(sql)
                if row:
                    val = list(row.values())[0]
                    global_vars[var_name] = val
                    logger.info(f"   提取(SQL): {var_name} = {val}")
            except (ValueError, TypeError, mysql.connector.Error) as e:
                logger.warning(f"   SQL提取失败: {var_name} - {e}")

    if db:
        db.close()
