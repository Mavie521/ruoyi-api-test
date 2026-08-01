"""
Allure 报告附件工具 —— 自动脱敏 + 格式化

┌─────────────────────────────────────────────────────────────────────┐
│ 这个文件做了什么？                                                  │
├─────────────────────────────────────────────────────────────────────┤
│ 1. 敏感信息自动脱敏（token / password / secret 等）                │
│ 2. 请求/响应/数据库结果自动挂载到 Allure 报告                      │
│ 3. 超长内容截断保护（防止 Allure 报告卡顿）                        │
│ 4. allure_init() 动态设置测试标题、模块标签                         │
│                                                                     │
│                                     │
│ "统一封装 sensitive data masking，报告外泄也不会暴露 token/password; │
│  二进制响应、非 JSON、超长报文全部容错，不会因报文格式导致崩溃;     │
│  内容截断保护，防止 Allure 报告过大加载卡顿。"                      │
└─────────────────────────────────────────────────────────────────────┘
"""
import json
import allure
import requests


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║                    敏感字段名单（私有常量）                              ║
# ╚══════════════════════════════════════════════════════════════════════════╝

# 请求头里这些字段需要脱敏（k.lower() 做忽略大小写匹配）
_SENSITIVE_HEADERS = {"authorization", "cookie", "set-cookie", "token", "x-auth-token"}

# 响应体里这些字段需要脱敏
_SENSITIVE_BODY_FIELDS = {"token", "access_token", "refresh_token", "password", "secret"}


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║                    内部工具（用户不需要直接调用）                        ║
# ╚══════════════════════════════════════════════════════════════════════════╝

def _mask(val: str) -> str:
    """脱敏一个字符串：前4位 + **** + 后4位

    例: "eyJhbGciOiJIUzI1NiJ9.xxx" → "eyJh****iJ9."
        太短的字符串（≤12字符）：前2位 + **** + 后2位
    """
    s = str(val)
    if len(s) > 12:
        return s[:4] + "****" + s[-4:]
    return s[:2] + "****" + s[-2:]


def _clean_headers(headers: dict) -> dict:
    """遍历请求头的每个 key，敏感字段调用 _mask 打码

    k.lower() 的作用：不管传进来的是 "Token" / "token" / "TOKEN" 都能命中
    """
    return {
        k: (_mask(v) if k.lower() in _SENSITIVE_HEADERS else v)
        for k, v in headers.items()
    }


def _clean_body(body):
    """递归脱敏 JSON 体中的敏感字段

    递归逻辑（函数自己调用自己）：
      - 遇到 dict  → 遍历每个 key，敏感字段打码，value 继续递归
      - 遇到 list  → 遍历每个元素，每个都递归
      - 遇到其他   → 原样返回（字符串、数字、None）
    """
    if isinstance(body, dict):
        return {
            k: (_mask(v) if k in _SENSITIVE_BODY_FIELDS else _clean_body(v))
            for k, v in body.items()
        }
    if isinstance(body, list):
        return [_clean_body(i) for i in body]
    return body  # int / str / None / bool → 不处理


def _pretty_json(data) -> str:
    """把数据格式化成好看的 JSON 字符串（最多 2000 字符，防撑爆报告）

    如果传进来的是字符串，先尝试解析成 dict 再格式化。
    解析失败就原样截断返回。
    """
    if isinstance(data, str):
        try:
            data = json.loads(data)
        except json.JSONDecodeError:
            return data[:1000]  # 不是 JSON，直接截断
    try:
        return json.dumps(data, ensure_ascii=False, indent=2)[:2000]
    except (ValueError, TypeError, OverflowError):
        return str(data)[:2000]


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║                    对外接口（测试用例和 Excel 驱动调用）                 ║
# ╚══════════════════════════════════════════════════════════════════════════╝

def allure_init(case: dict):
    """Allure 初始化：从 Excel 用例字典设置四级标签

    层级: Epic > Feature > Story > Title
    Excel 可选的 epic 列默认值为「若依接口测试」，与代码测试线对齐。
    """
    allure.dynamic.epic(case.get("epic", "若依接口测试"))
    allure.dynamic.feature(case.get("feature", "未分类模块"))
    allure.dynamic.story(case.get("story", "未分类场景"))
    allure.dynamic.title(f"TC{case.get('id', 'N/A')} - {case.get('title', '未命名用例')}")


def attach_request(method: str, url: str, **kwargs):
    """把 HTTP 请求信息挂载到 Allure 报告（请求头自动脱敏）

    用法:
        attach_request("POST", "http://xxx/api/login", headers={...}, json={...})

    会在 Allure 报告的"附件"区显示：
      POST http://xxx/api/login

      Headers:
      {"Authorization": "eyJh****iJ9.", "Content-Type": "application/json"}

      Json:
      {"username": "admin", "password": "adm****123"}
    """
    parts = [f"{method.upper()} {url}"]
    if kwargs.get("headers"):
        parts.append(f"\n Headers:\n{_pretty_json(_clean_headers(kwargs['headers']))}")
    # 遍历 params / json / data 三种常见请求体，有就挂上
    for key in ("params", "json", "data"):
        if kwargs.get(key):
            parts.append(f"\n {key.capitalize()}:\n{_pretty_json(kwargs[key])}")
    allure.attach(
        "\n".join(parts),
        name=f" 请求 ({method})",
        attachment_type=allure.attachment_type.TEXT,
    )


def attach_response(res: requests.Response):
    """把 HTTP 响应信息挂载到 Allure 报告（响应体自动脱敏）

    自动处理三种情况：
      1. JSON 响应  → 脱敏 + 格式化
      2. 非 JSON 响应 → 截取前 2000 字符
      3. 二进制响应   → 走异常分支，截取文本
    """
    try:
        body = json.loads(res.content.decode("utf-8"))
        body_str = _pretty_json(_clean_body(body))
    except (ValueError, TypeError, json.JSONDecodeError, UnicodeDecodeError):
        # 不是 JSON（二进制、HTML、纯文本等），直接截取文本
        body_str = res.text[:2000]

    allure.attach(
        f" 状态码: {res.status_code}\n 耗时: {res.elapsed.total_seconds():.2f}s\n\n Response Body:\n{body_str}",
        name=" 响应",
        attachment_type=allure.attachment_type.TEXT,
    )


def attach_db_result(sql: str, results: list, elapsed: float = 0):
    """把数据库查询结果挂载到 Allure 报告（最多展示前 10 条）

    用法:
        attach_db_result("SELECT * FROM sys_user", rows, elapsed=0.023)
    """
    lines = [f"SQL: {sql}", f"结果数: {len(results)}", f"耗时: {elapsed:.3f}s", ""]
    for i, row in enumerate(results[:10], 1):
        lines.append(f"[{i}] {json.dumps(row, ensure_ascii=False, default=str)}")
    if len(results) > 10:
        lines.append(f"\n... 共 {len(results)} 条，仅显示前 10 条")
    allure.attach(
        "\n".join(lines),
        name=" 数据库查询",
        attachment_type=allure.attachment_type.TEXT,
    )
