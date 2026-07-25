"""Mock 规则匹配引擎 —— 匹配请求路径和方法，返回预设响应"""
import json
import re
import time
from ..database import list_mock_rules, insert_mock_log


def _wildcard_match(pattern: str, actual: str) -> bool:
    """通配符匹配：* 匹配任意路径段，支持 /user/* /api/*/info"""
    # 将 * 替换为正则 [^/]+（匹配单段路径）
    regex = "^" + re.escape(pattern).replace(r"\*", r"[^/]+") + "$"
    return bool(re.match(regex, actual))


def match_and_respond(path: str, method: str, body: str = "",
                      headers: str = "") -> tuple:
    """
    匹配 Mock 规则并返回响应

    匹配规则:
      1. 只查 enabled=1 的规则
      2. 先精确匹配 path + method，再通配符 * 匹配
      3. 未命中返回 404

    通配符: /user/* 匹配 /user/123, /api/*/info 匹配 /api/order/info

    返回:
      (status_code, response_body, matched_rule_name, match_result)
    """
    rules = list_mock_rules()
    enabled = [r for r in rules if r.get("enabled")]

    normalized = path.lstrip("/")

    # 第一轮：精确匹配
    matched = None
    for rule in enabled:
        if rule["path"].lstrip("/") == normalized and rule["http_method"].upper() == method.upper():
            matched = rule
            break

    # 第二轮：通配符匹配
    if not matched:
        for rule in enabled:
            rule_path = rule["path"].lstrip("/")
            if "*" in rule_path and rule["http_method"].upper() == method.upper():
                if _wildcard_match(rule_path, normalized):
                    matched = rule
                    break

    if matched:
        # 模拟延迟
        delay = matched.get("delay_ms", 0) or 0
        if delay > 0:
            time.sleep(delay / 1000.0)

        status_code = matched["status_code"]
        response_body = matched.get("response_body", "{}")
        rule_name = matched["name"]
        rule_id = matched["id"]

        # 记录日志
        insert_mock_log(
            rule_id=rule_id, rule_name=rule_name, path=path,
            http_method=method, request_body=body, request_headers=headers,
            status_code=status_code, response_body=response_body, matched=1,
        )

        return (status_code, response_body, True)

    # 未命中
    insert_mock_log(
        rule_id=None, rule_name="", path=path, http_method=method,
        request_body=body, request_headers=headers,
        status_code=404, response_body=json.dumps({"error": "no mock rule matched", "path": path, "method": method}),
        matched=0,
    )

    return (404, json.dumps({"error": "no mock rule matched", "path": path, "method": method}), False)
