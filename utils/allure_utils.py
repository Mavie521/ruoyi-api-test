"""Allure 报告附件工具（自动过滤敏感字段）"""
import json
import allure
import requests

_SENSITIVE_HEADERS = {"authorization", "cookie", "set-cookie", "token", "x-auth-token"}
_SENSITIVE_BODY_FIELDS = {"token", "access_token", "refresh_token", "password", "secret"}


def _mask(val: str) -> str:
    """脱敏：显示前4+后4，中间变 *"""
    s = str(val)
    return s[:4] + "****" + s[-4:] if len(s) > 12 else s[:2] + "****" + s[-2:]


def _clean_headers(headers: dict) -> dict:
    """脱敏请求头中的敏感字段"""
    return {k: (_mask(v) if k.lower() in _SENSITIVE_HEADERS else v) for k, v in headers.items()}


def _clean_body(body) -> dict:
    """脱敏 JSON 体中的敏感字段"""
    if isinstance(body, dict):
        return {k: (_mask(v) if k in _SENSITIVE_BODY_FIELDS else _clean_body(v)) for k, v in body.items()}
    if isinstance(body, list):
        return [_clean_body(i) for i in body]
    return body


def allure_init(case: dict):
    allure.dynamic.feature(case.get("feature", "未分类模块"))
    allure.dynamic.story(case.get("story", "未分类场景"))
    allure.dynamic.title(f"TC{case.get('id', 'N/A')} - {case.get('title', '未命名用例')}")


def attach_request(method: str, url: str, **kwargs):
    """将 HTTP 请求 attach 到 Allure 报告（敏感请求头自动脱敏）"""
    parts = [f"{method.upper()} {url}"]
    if kwargs.get("headers"):
        parts.append(f"\n Headers:\n{_pretty_json(_clean_headers(kwargs['headers']))}")
    for key in ("params", "json", "data"):
        if kwargs.get(key):
            parts.append(f"\n {key.capitalize()}:\n{_pretty_json(kwargs[key])}")
    allure.attach("\n".join(parts), name=f" 请求 ({method})", attachment_type=allure.attachment_type.TEXT)


def attach_response(res: requests.Response):
    """将 HTTP 响应 attach 到 Allure 报告（敏感字段自动脱敏）"""
    try:
        body = json.loads(res.content.decode("utf-8"))
        body_str = _pretty_json(_clean_body(body))
    except (ValueError, TypeError, json.JSONDecodeError, UnicodeDecodeError):
        body_str = res.text[:2000]
    allure.attach(
        f" 状态码: {res.status_code}\n 耗时: {res.elapsed.total_seconds():.2f}s\n\n Response Body:\n{body_str}",
        name=" 响应", attachment_type=allure.attachment_type.TEXT,
    )


def attach_db_result(sql: str, results: list, elapsed: float = 0):
    """将数据库查询结果 attach 到 Allure 报告"""
    lines = [f"SQL: {sql}", f"结果数: {len(results)}", f"耗时: {elapsed:.3f}s", ""]
    for i, row in enumerate(results[:10], 1):
        lines.append(f"[{i}] {json.dumps(row, ensure_ascii=False, default=str)}")
    if len(results) > 10:
        lines.append(f"\n... 共 {len(results)} 条，仅显示前10条")
    allure.attach("\n".join(lines), name=" 数据库查询", attachment_type=allure.attachment_type.TEXT)


def _pretty_json(data) -> str:
    if isinstance(data, str):
        try:
            data = json.loads(data)
        except json.JSONDecodeError:
            return data[:1000]
    try:
        return json.dumps(data, ensure_ascii=False, indent=2)[:2000]
    except (ValueError, TypeError, OverflowError):
        return str(data)[:2000]
