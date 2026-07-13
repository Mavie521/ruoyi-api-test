"""
Allure 动态报告工具

功能:
1. allure_init() — Excel 数据驱动模式下的动态属性初始化
2. attach_request() — 格式化 attach HTTP 请求
3. attach_response() — 格式化 attach HTTP 响应
4. step() — 更清晰的分步装饰器
"""
import json
import allure
import requests


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


def attach_request(method: str, url: str, **kwargs):
    """将 HTTP 请求 attach 到 Allure 报告"""
    parts = [f"{method.upper()} {url}"]
    if kwargs.get("headers"):
        parts.append(f"\n Headers:\n{_pretty_json(kwargs['headers'])}")
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
    """将 HTTP 响应 attach 到 Allure 报告"""
    try:
        body = res.json()
        body_str = _pretty_json(body)
    except Exception:
        body_str = res.text[:2000]

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


def _pretty_json(data) -> str:
    """JSON 格式化输出"""
    if isinstance(data, str):
        try:
            data = json.loads(data)
        except json.JSONDecodeError:
            return data[:1000]
    try:
        return json.dumps(data, ensure_ascii=False, indent=2)[:2000]
    except Exception:
        return str(data)[:2000]
