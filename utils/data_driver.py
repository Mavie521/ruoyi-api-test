"""
Excel数据驱动核心引擎

一条Excel用例的执行流程:
  案例数据 → 模板渲染(替换{{变量}}) → 发HTTP请求 → 断言 → 提取变量
"""
import json
import allure
import requests
import jsonpath
from jinja2 import Template
from config.config import BASE_URL
from utils.logger import logger
from utils.allure_utils import attach_request, attach_response


def render_case(case: dict, global_vars: dict) -> dict:
    """
    用 Jinja2 渲染Excel用例中的 {{变量}}
    比如 json={{"token": "{{TOKEN}}"}} → json={{"token": "eyJxxx..."}}
    """
    case_str = json.dumps(case, ensure_ascii=False)
    rendered = Template(case_str).render(global_vars)
    return json.loads(rendered)


def _parse_field(value):
    """
    把Excel中存成字符串的JSON字段转成Python对象
    比如 '{"key": "val"}' → {"key": "val"}
    """
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
    根据Excel用例数据发HTTP请求
    支持: method, path, headers, params, json, data
    自动解析Excel中存为字符串的JSON字段
    """
    url = BASE_URL.rstrip("/") + case.get("path", "")

    # 解析JSON字符串字段 → Python对象
    headers = _parse_field(case.get("headers"))
    params = _parse_field(case.get("params"))
    json_body = _parse_field(case.get("json"))
    form_data = _parse_field(case.get("data"))

    method = case.get("method", "get").lower()

    logger.info(f"请求: {method.upper()} {url}")
    res = requests.request(
        method=method, url=url,
        headers=headers, params=params,
        json=json_body, data=form_data,
        timeout=10,
    )
    return res


def do_assert(case: dict, res: requests.Response):
    """
    断言:
    - check 有值 → JSONPath精确断言
    - check 无值 → 文本包含断言
    """
    check = case.get("check")
    expected = str(case.get("expected", ""))

    if check:
        # JSONPath精确断言: check="$..code" expected="200"
        actual_list = jsonpath.jsonpath(res.json(), check)
        assert actual_list is not False, f"JSONPath未匹配: {check}"
        actual = str(actual_list[0])
        assert actual == expected, \
            f"JSONPath断言失败: {check} 预期={expected} 实际={actual}"
        logger.info(f"   JSONPath断言通过: {check} == {expected}")
    else:
        # 包含断言: expected在响应文本中即可
        assert expected in res.text, \
            f"包含断言失败: 未找到'{expected}'"
        logger.info(f"   包含断言通过: 响应包含'{expected}'")


def do_extract(case: dict, res: requests.Response, global_vars: dict):
    """
    从响应中提取值到全局变量，供后续用例使用
    Excel字段 jsonExData = {"TOKEN": "$..token"}
    """
    ex_data = case.get("jsonExData")
    if not ex_data:
        return

    if isinstance(ex_data, str):
        ex_data = json.loads(ex_data)

    for var_name, jsonpath_expr in ex_data.items():
        actual_list = jsonpath.jsonpath(res.json(), jsonpath_expr)
        if actual_list:
            global_vars[var_name] = actual_list[0]
            logger.info(f"   提取: {var_name} = {actual_list[0]}")
