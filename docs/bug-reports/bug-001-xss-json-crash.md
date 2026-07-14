# 缺陷报告 BUG-001

## 概述

| 字段 | 值 |
|------|----|
| 缺陷ID | BUG-001 |
| 标题 | `<` 字符导致 Jackson JSON 解析器抛出异常，接口返回 500 |
| 严重程度 | Critical |
| 优先级 | P1 |
| 状态 | 已确认（标记为 xfail） |
| 发现人 | Mavie |
| 发现时间 | 2026-07-13 |
| 被测版本 | RuoYi-Vue v3.9.2 |

## 环境信息

- Docker ruoyi-api:8080
- JDK 17 / Spring Boot 4.0.6
- MySQL 8.0

## 复现步骤

```python
# 测试代码
data = new_role_data.copy()
data["roleName"] = "x<B oncopy=alert(1)>test</B>"
resp = role_api.create_role(data)
assert resp.get("code") != 500  # 失败，实际返回 500
```

## 实际结果

```
HTTP 200
Body: {"msg": "JSON parse error: Unexpected character ('<' (code 60))", "code": 500}
```

## 预期结果

- 服务端应对 `<` 字符做转义处理
- 应返回 HTTP 400 参数错误
- 不应返回 500 服务端内部错误

## 根因分析

Jackson JSON 解析器在处理包含 `<` 字符的请求体时抛出 `JsonParseException`，未被全局异常处理器捕获为合理的 400 错误。

## 影响范围

所有 POST/PUT 接口中带 `<` 字符的字符串字段都可能触发此问题。

## 附件

Allure 报告截图：/app/allure-report/#bug-001
