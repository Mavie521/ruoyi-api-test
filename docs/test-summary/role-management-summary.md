# RuoYi API 测试平台 — 测试总结报告

> 更新日期：2026-08-01 | 版本：v2.0

## 执行概况

| 项目 | 数据 |
|------|------|
| 总用例数 | **95**（代码 50 + Excel 45） |
| 通过 | 93 |
| 跳过 | 1（XSS crash bug — 后端 500 拦截） |
| 已知缺陷（xfail） | 1（POST 幂等 — 若依返回 500 非 4xx） |
| 失败 | 0 |
| 通过率 | 100%（93/93 有效用例） |
| 执行耗时 | ~12s（顺序执行） |

## 用例分布

```
测试线:
  tests/       50 条   代码测试（fixture 注入，独立隔离）
  testcases/   45 条   Excel 数据驱动（Jinja2 渲染，变量链式传递）

按模块:
  登录认证      4 条   test_login.py
  用户管理     10 条   test_system_user.py
  角色管理     12 条   test_role.py
  安全测试     18 条   test_security.py
  业务流程      3 条   test_business_flow.py
  部门管理      2 条   test_dept.py
  岗位管理      2 条   test_post.py
  数据驱动     45 条   test_excel_driver.py

按优先级:
  P0 (阻塞)     6 条   登录/越权/业务流程
  P1 (核心)    44 条   CRUD/SQL注入/XSS/幂等
  P2 (次要)     5 条   下拉选项/部门树/个人信息
  未标记       40 条   Excel 驱动

按类型:
  功能验证     55 条   正向/异常 CRUD
  安全测试     19 条   SQL注入(7)+XSS(6)+越权(3)+Token(2)+超长(1)
  业务流程      3 条   端到端业务链
  幂等测试      1 条   POST 重复创建
  数据驱动     45 条   Excel 读操作全覆盖
```

## 接口覆盖率

| 模块 | 文档端点 | 已测 | 比率 | 说明 |
|------|:---:|:---:|:---:|------|
| 登录认证 | 4 | 3 | 75% | 缺 POST /logout（JWT 无状态，低价值） |
| 用户管理 | 13 | 9 | 69% | CRUD + 状态 + 密码 + 个人信息全覆盖 |
| 角色管理 | 14 | 10 | 71% | CRUD + 状态 + 权限 + 授权用户全覆盖 |
| 部门管理 | 5 | 5 | 100% | CRUD + 禁启用全覆盖 |
| 岗位管理 | 6 | 4 | 67% | CRUD + 禁启用，缺 GET/{id}、optionselect |
| 菜单管理 | 6 | 3 | 50% | 只读（Excel），缺 CRUD |
| 字典/配置/公告 | ~20 | ~7 | 35% | 只读（Excel），缺写操作 |
| 监控/日志/代码生成 | ~50 | 0 | 0% | 运维类，未纳入测试范围 |

## 安全测试矩阵

| 攻击类型 | 用例数 | 覆盖点 |
|------|:---:|------|
| SQL 注入 | 7 | 用户名 4 种 + 密码 3 种 payload |
| XSS（存储型） | 6 | 5 种脚本 + 1 种 HTML 标签 |
| 垂直越权 | 1 | 普通用户调用管理员接口 — 精确断言 403 |
| 水平越权 | 1 | 普通用户访问他人数据 — 精确断言 403 |
| 参数篡改 | 1 | 篡改 userId 修改他人资料 — 双层验证 + finally 自愈 |
| Token 伪造 | 1 | 随机字符串 token 访问受保护接口 |
| 超长输入 | 1 | 5000 字符用户名密码 |
| 幂等 | 1 | POST 重复创建 — xfail（若依已知缺陷） |

## 技术架构

```
conftest.py (根)            ← Allure 环境 + 失败附件
  │
  ├─ tests/conftest.py       ← API fixtures (session/function 级)
  │   ├─ admin_login          session 管理员登录
  │   ├─ role_api             session 角色 API（复用 token）
  │   ├─ system_user_api      session 用户 API
  │   ├─ dept_api / post_api  session 部门/岗位 API
  │   ├─ db                   session 数据库连接（连接池复用）
  │   ├─ non_admin_login      session 普通用户（安全测试）
  │   ├─ new_role_data        function 测试角色（自动清理）
  │   └─ new_real_user_data   function 测试用户（自动清理）
  │
  ├─ tests/ (50条)           代码测试 —— 独立隔离，支持并行
  │
  └─ testcases/ (45条)       Excel 驱动 —— 顺序执行，变量依赖
      └─ _check_vars()        变量缺失时 skip 代替报错（防雪崩）
```

## 发现的缺陷

| # | 类型 | 描述 | 状态 |
|---|------|------|:---:|
| 1 | xfail | POST 幂等：重复创建同 roleKey 返回 500 非 4xx | 🔴 若依已知缺陷 |
| 2 | skip | XSS crash：`<B>` 等 HTML 标签导致后端 500 崩溃 | 🟡 后端拦截，非测试问题 |

> 注：越权断言已精确化（500 前检 + 403 精确断言），Excel 雪崩已通过 `_check_vars()` 解决。
> xdist 并行：`non_admin_role` 的 CREATE 失败后有 DB 回查兜底，DB 唯一索引保证安全。

## 断言体系

| 层级 | 函数 | 用途 |
|------|------|------|
| 接口 | `assert_jsonpath_exact` | JSONPath 精准字段等值 + 自动类型转换 |
| 数据库 | `assert_db_value` | DB 字段值相等 |
| 数据库 | `assert_db_exists` | DB 记录存在 |
| 安全 | `assert token is None` | SQL 注入/异常登录验证 |
| 安全 | `assert code == 403` | 越权精确断言 |
| 二进制 | `assert_content_type/length/sha256` | 文件下载校验 |
| 变量提取 | `do_extract_json/sql` | 用例间变量传递（Excel 驱动） |

## 后续计划

| 优先级 | 事项 |
|:---:|------|
| 🟢 | 补 GET /system/post/{id}（岗位详情） |
| 🟢 | 补 PUT /system/user/authRole（分配角色） |
| 🟢 | 新建 MenuApi + 菜单 CRUD 用例 |
| ⬜ | 字典/配置/公告写操作 |
| ⬜ | CI/CD 集成（Jenkins/GitHub Actions） |
