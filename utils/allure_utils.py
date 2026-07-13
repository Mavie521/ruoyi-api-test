"""
Allure 动态报告工具

功能:
1. allure_init() —— Excel 数据驱动模式下的动态属性初始化
2. attach_request() —— 格式化 attach HTTP 请求（已脱敏）
3. attach_response() —— 格式化 attach HTTP 响应（已脱敏）
4. step() —— 更清晰的分步装饰器
"""
import json
import re
import allure
import requests


# ============================================================
# 敏感数据脱敏
# ============================================================
SENSITIVE_FIELDS = ["password", "token", "secret", "Authorization"]


def mask_sensitive(data) -> str:
    """
    递归脱敏 JSON 中的敏感字段（password / token / secret 等）
    例如: {"password": "admin123"} → {"password": "******"}
    """
    if isinstance(data, dict):
        masked = {}
        for k, v in data.items():
            if any(s in k.lower() for s in SENSITIVE_FIELDS):
                masked[k] = "******" if v else v
            else:
                masked[k] = mask_sensitive(v) if isinstance(v, (dict, list)) else v
        return masked
    elif isinstance(data, list):
        return [mask_sensitive(item) if isinstance(item, (dict, list)) else item for item in data]
    return data


def mask_sensitive_text(text: str) -> str:
    """
    对纯文本中的敏感字段做正则替换（防御性兜底）
    匹配 "password": "任意内容" 和 "token": "任意内容"
    """
    text = re.sub(r'"(password|token|secret)"\s*:\s*"[^"]+"', r'"\1": "******"', text)
    text = re.sub(r'(Authorization|Bearer)\s+[\w\-\.]+', r'\1 ******', text)
    return text


def _pretty_json(data) -> str:
    """JSON 格式化输出（已脱敏）"""
    if isinstance(data, str):
        try:
            data = json.loads(data)
        except json.JSONDecodeError:
            return mask_sensitive_text(data[:1000])
    # 先脱敏再格式化
    masked = mask_sensitive(data)
    try:
        return json.dumps(masked, ensure_ascii=False, indent=2)[:2000]
    except Exception:
        return str(data)[:2000]


# ============================================================
# Allure 初始化
# ============================================================
def allure_init(case: dict):
    """
    根据 Excel 用例行数据动态初始化 Allure 属性
    参数 case 支持的 key: feature, story, title, severity
    """
    allure.dynamic.feature(case.get("feature", "未分类模块"))
    allure.dynamic.story(case.get("story", "未分类场景"))
    allure.dynamic.title(f"TC{case.get('id', 'N/A')} - {case.get('title', '未命名用例')}")

    severity_map = {
        "阻塞": allure.severity_level.BLOCKER,
        "严重": allure.severity_level.CRITICAL,
        "一般": allure.severity_level.NORMAL,
        "轻微": allure.severity_level.MINOR,
        "建议": allure.severity_level.TRIVIAL,
    }
    severity = case.get("severity", "一般")
    if severity in severity_map:
        allure.dynamic.severity(severity_map[severity])


# ============================================================
# 请求 / 响应 Attach（输出到 Allure 报告）
# ============================================================
def attach_request(method: str, url: str, **kwargs):
    """将 HTTP 请求 attach 到 Allure 报告（敏感字段已脱敏）"""
    parts = [f"{method.upper()} {url}"]
    if kwargs.get("headers"):
        # headers 中脱敏 Authorization
        headers = {k: ("******" if k.lower() == "authorization" else v)
                   for k, v in kwargs["headers"].items()}
        parts.append(f"\n Headers:\n{_pretty_json(headers)}")
    if kwargs.get("params"):
        parts.append(f"\n Params:\n{_pretty_json(kwargs['params'])}")
    if kwargs.get("json"):
        parts.append(f"\n JSON Body:\n{_pretty_json(kwargs['json'])}")
    if kwargs.get("data"):
        parts.append(f"\n Form Data:\n{_pretty_json(kwargs['data'])}")

    allure.attach(
        "\n".join(parts),
        name=f" 请求 ({method})",
        attachment_type=allure.attachment_type.TEXT,
    )


def attach_response(res: requests.Response):
    """将 HTTP 响应 attach 到 Allure 报告（敏感字段已脱敏）"""
    try:
        body = res.json()
        body_str = _pretty_json(body)
    except Exception:
        body_str = mask_sensitive_text(res.text[:2000])

    text = (
        f" 状态码: {res.status_code}\n"
        f" 耗时: {res.elapsed.total_seconds():.2f}s\n"
        f"\n Response Body:\n{body_str}"
    )
    allure.attach(text, name=" 响应", attachment_type=allure.attachment_type.TEXT)


def attach_db_result(sql: str, results: list, elapsed: float = 0):
    """将数据库查询结果 attach 到 Allure 报告"""
    lines = [f"SQL: {sql}", f"结果数: {len(results)}", f"耗时: {elapsed:.3f}s", ""]
    for i, row in enumerate(results[:10], 1):
        lines.append(f"[{i}] {json.dumps(row, ensure_ascii=False, default=str)}")
    if len(results) > 10:
        lines.append(f"\n... 共 {len(results)} 条，仅显示前10条")
    allure.attach("\n".join(lines), name=" 数据库查询", attachment_type=allure.attachment_type.TEXT)
