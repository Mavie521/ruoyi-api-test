<div align="center">

# 🏗️ RuoYi API Test Framework

> **企业级接口自动化测试框架 · POM三层架构 · 双引擎驱动 · Docker容器化 · Jenkins CI/CD**

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![Pytest](https://img.shields.io/badge/Pytest-9.x-0A9EDC?style=flat-square&logo=pytest&logoColor=white)](https://pytest.org)
[![Pylint](https://img.shields.io/badge/Pylint-10.00%2F10-brightgreen?style=flat-square&logo=python&logoColor=white)]()
[![Allure](https://img.shields.io/badge/Allure-2.32-orange?style=flat-square&logo=simpleanalytics&logoColor=white)]()
[![Docker](https://img.shields.io/badge/Docker-24+-2496ED?style=flat-square&logo=docker&logoColor=white)]()
[![Jenkins](https://img.shields.io/badge/Jenkins-✓-D24939?style=flat-square&logo=jenkins&logoColor=white)]()
[![Coverage](https://img.shields.io/badge/Coverage-98%25-green?style=flat-square)]()
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)]()

</div>

<div align="center">
<table>
<tr>
<td width="25%" align="center"><b>🏗️ 架构</b><br/><small>POM 三层</small></td>
<td width="25%" align="center"><b>⚡ 双引擎</b><br/><small>代码 + Excel</small></td>
<td width="25%" align="center"><b>✅ 双断言</b><br/><small>API + DB</small></td>
<td width="25%" align="center"><b>🔁 CI/CD</b><br/><small>Jenkins 全自动</small></td>
</tr>
<tr>
<td width="25%" align="center"><b>🐳 Docker</b><br/><small>6 容器编排</small></td>
<td width="25%" align="center"><b>📊 Allure</b><br/><small>动态报告</small></td>
<td width="25%" align="center"><b>🔒 安全测试</b><br/><small>SQL/XSS/越权</small></td>
<td width="25%" align="center"><b>🧹 工程化</b><br/><small>Pylint 10.0</small></td>
</tr>
</table>
</div>

---

## 📊 快速一览

| 指标 | 数值 |
|------|------|
| **测试用例** | 31 条代码用例 + N 条 Excel 数据驱动 |
| **接口覆盖** | 20+ 个 REST API（角色/用户/登录/安全） |
| **代码质量** | ⭐ **Pylint 10.00/10**（满分） |
| **测试覆盖率** | 98%+（api/ + utils/ 核心模块） |
| **构建时间** | 全量 ~22s，P0 冒烟 < 5s |
| **失败重试** | 网络波动自动重试 1 次 |
| **部署方式** | Docker Compose 一键部署 / 本地直连 |
| **CI/CD** | Jenkins 每日凌晨自动回归 + Allure 报告 + 钉钉通知 |

---

## 📑 目录

<div style="display: flex; flex-wrap: wrap; gap: 20px;">
<div style="min-width: 200px;">

| | 章节 |
|---|------|
| 🏗️ | [架构全景](#架构全景) |
| ✨ | [特性矩阵](#特性矩阵) |
| 🛠️ | [技术栈](#技术栈) |
| 🚀 | [快速开始](#快速开始) |
| 📁 | [项目结构](#项目结构) |
| 🎯 | [架构设计详解](#架构设计详解) |
| ⚙️ | [测试引擎](#测试引擎) |
| 🐳 | [Docker 部署](#docker-部署) |

</div>
<div style="min-width: 200px;">

| | 章节 |
|---|------|
| 🔄 | [CI/CD 流水线](#cicd-流水线) |
| 📊 | [测试覆盖与策略](#测试覆盖与策略) |
| 🧹 | [代码质量与工程化](#代码质量与工程化) |
| 🔒 | [安全测试](#安全测试) |
| ✅ | [双维度断言体系](#双维度断言体系) |
| 📋 | [数据驱动引擎](#数据驱动引擎) |
| 💻 | [代码示例](#代码示例) |
| 📚 | [文档体系](#文档体系) |
| ❓ | [常见问题与排错](#常见问题与排错) |

</div>
</div>

---

## 架构全景

```
┌══════════════════════════════════════════════════════════════════════════════┐
║                           RuoYi API Test Framework                           ║
║                    企业级接口自动化测试框架 · 完整架构图                      ║
└══════════════════════════════════════════════════════════════════════════════┘

┌─ 用户触发层 ──────────────────────────────────────────────────────────────┐
│                                                                           │
│   ┌──────────┐   ┌──────────────┐   ┌──────────────────┐                 │
│   │ Git Push  │   │ Jenkins UI   │   │ 定时触发器(Cron) │                 │
│   │ (代码提交) │   │ (手动构建)   │   │ (每日凌晨2点)    │                 │
│   └─────┬────┘   └──────┬───────┘   └────────┬─────────┘                 │
│         │               │                    │                            │
│         └───────────────┼────────────────────┘                            │
│                         ▼                                                  │
│              ┌──────────────────────┐                                      │
│              │  Jenkins Pipeline    │                                      │
│              │  Jenkinsfile         │                                      │
│              │  1. 拉取代码         │                                      │
│              │  2. Docker Compose   │                                      │
│              │  3. 运行测试         │                                      │
│              │  4. Allure 报告      │                                      │
│              │  5. 钉钉通知         │                                      │
│              └──────────┬───────────┘                                      │
└─────────────────────────┼──────────────────────────────────────────────────┘
                          │
┌─ CI/CD 任务编排层 ─────┼───────────────────────────────────────────────────┐
│                         ▼                                                  │
│  ┌──────────────────────────────────────────────────────────────────────┐ │
│  │                   scripts/run_all.sh                                   │ │
│  │                                                                        │ │
│  │   set +e                                                               │ │
│  │   MARKER=${1:-p0}                                                      │ │
│  │   MODE=${2:-fast}                                                      │ │
│  │                                                                        │ │
│  │   ┌────────────┐   ┌────────────────┐   ┌─────────────────────────┐   │ │
│  │   │ docker     │ → │ docker compose  │ → │ docker compose --profile│ │ │
│  │   │ compose    │   │ up -d          │   │ test run test-runner    │   │ │
│  │   │ up -d      │   │ (启动后端服务)  │   │ bash wait_for_api.sh   │   │ │
│  │   │ (启服务)    │   │                │   │ (等API就绪, POST验证)   │   │ │
│  │   └────────────┘   └────────────────┘   └─────────────────────────┘   │ │
│  │                                                                        │ │
│  │   ┌───────────────────────────────────────────────────────────────┐   │ │
│  │   │  docker compose --profile test run --rm test-runner              │   │ │
│  │   │    sh -c "pytest tests/ testcases/test_excel_driver.py ..."     │   │ │
│  │   └───────────────────────────────────────────────────────────────┘   │ │
│  │                                                                        │ │
│  │   ┌────────────────┐   ┌──────────────────┐   ┌────────────────┐      │ │
│  │   │ allure generate │ → │ docker compose  │ → │ 钉钉通知        │      │ │
│  │   │ (生成报告)      │   │ up -d allure    │   │ (成功/失败)     │      │ │
│  │   └────────────────┘   └──────────────────┘   └────────────────┘      │ │
│  └──────────────────────────────────────────────────────────────────────┘ │
└──────────────────────────┬─────────────────────────────────────────────────┘
                           │
┌─ Docker 容器编排层 ──────┼─────────────────────────────────────────────────┐
│                          ▼                                                │
│  ┌──────────────────── ry-network (Docker Bridge) ─────────────────────┐  │
│  │                                                                    │  │
│  │  ┌─────────────┐    ┌─────────────┐    ┌──────────────────────┐   │  │
│  │  │  MySQL 8.0   │    │  Redis 7    │    │   RuoYi Backend      │   │  │
│  │  │  3306        │    │  6379       │    │   Java / JDK 17      │   │  │
│  │  │  ry-vue DB   │    │  缓存       │    │   Spring Boot 4.x    │   │  │
│  │  │  健康检查 ✓   │    │  健康检查 ✓  │    │   healthcheck: curl  │   │  │
│  │  └──────┬───────┘    └──────┬──────┘    └──────────┬───────────┘   │  │
│  │         │                  │                       │               │  │
│  │         └──────────────────┼───────────────────────┘               │  │
│  │                            │                                       │  │
│  │                    ┌───────▼──────────────────────────┐            │  │
│  │                    │  Test Runner (pytest)             │            │  │
│  │                    │  ┌─────────────────────────────┐  │            │  │
│  │                    │  │ 1. admin_login fixture       │  │            │  │
│  │                    │  │    POST /login → token      │  │            │  │
│  │                    │  │ 2. pytest tests/             │  │            │  │
│  │                    │  │    31 条代码用例             │  │            │  │
│  │                    │  │ 3. 可选: testcases/          │  │            │  │
│  │                    │  │    Excel 数据驱动用例         │  │            │  │
│  │                    │  │ 4. allure-results → 报告    │  │            │  │
│  │                    │  └─────────────────────────────┘  │            │  │
│  │                    └──────────────────────────────────┘            │  │
│  │                                                                    │  │
│  │  ┌────────────────────────────────────────────────────────────┐   │  │
│  │  │  Allure Report (Nginx alpine)                               │   │  │
│  │  │  serve/allure-report: /usr/share/nginx/html                 │   │  │
│  │  │  暴露端口: 8088                                             │   │  │
│  │  │  访问: http://192.168.159.128:8088                           │   │  │
│  │  └────────────────────────────────────────────────────────────┘   │  │
│  └────────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────────┘

┌─ 测试框架内部架构 ─────────────────────────────────────────────────────┐
│                                                                        │
│  ┌─── 测试用例层 ─────────────────────────────────────────────────┐   │
│  │  tests/                          testcases/                    │   │
│  │  ┌────────────────────┐          ┌────────────────────────┐    │   │
│  │  │ test_role.py       │          │ test_excel_driver.py   │    │   │
│  │  │  10 tests (P0/P1/P2)│         │  Excel 数据驱动        │    │   │
│  │  │ test_system_user.py│          │  read_excel() → 参数化  │    │   │
│  │  │  9 tests (P0/P1)   │          │  Jinja2 模板渲染变量   │    │   │
│  │  │ test_security.py   │          └────────────────────────┘    │   │
│  │  │  11 tests (P1/P2)  │                                        │   │
│  │  │ test_business_flow │                                        │   │
│  │  │  1 tests (P0)      │                                        │   │
│  │  └────────────────────┘                                        │   │
│  └──────────────────────────┬─────────────────────────────────────┘   │
│                             │ 继承 fixtures                           │
│  ┌──────────────────────────▼─────────────────────────────────────┐   │
│  │  Fixture 层 (conftest.py)                                      │   │
│  │  ┌────────────────────────────────────────────────────────┐    │   │
│  │  │ admin_login (session)  →  LoginApi.login() → token     │    │   │
│  │  │   ├─ login_api / user_api / role_api / system_user_api │    │   │
│  │  │   │  每个继承 token, 返回对应 API 对象                    │    │   │
│  │  │   └─ db (session)       →  DbClient 数据库连接          │    │   │
│  │  │                                                            │    │   │
│  │  │  new_role_data (function) → 自动生成 + 清理(fianlizer)     │    │   │
│  │  │  new_real_user_data      → 自动生成用户数据                │    │   │
│  │  └────────────────────────────────────────────────────────┘    │   │
│  └──────────────────────────┬─────────────────────────────────────┘   │
│                             │ 继承                                    │
│  ┌──────────────────────────▼─────────────────────────────────────┐   │
│  │  API 对象层 (api/)                                             │   │
│  │  ┌────────────┐ ┌──────────┐ ┌────────────┐ ┌──────────────┐  │   │
│  │  │ LoginApi   │ │ RoleApi  │ │ UserApi    │ │ SystemUserApi│  │   │
│  │  │ /login     │ │ /system/ │ │ /system/   │ │ /system/user │  │   │
│  │  │ /getInfo   │ │ role/*   │ │ user/*     │ │ /*           │  │   │
│  │  │ /getRouters│ │          │ │ (测试用户)  │ │ (真实用户)    │  │   │
│  │  └────────────┘ └──────────┘ └────────────┘ └──────────────┘  │   │
│  └──────────────────────────┬─────────────────────────────────────┘   │
│                             │ 继承                                    │
│  ┌──────────────────────────▼─────────────────────────────────────┐   │
│  │  基础设施层 (api/base_api.py)                                   │   │
│  │  ┌────────────────────────────────────────────────────────┐    │   │
│  │  │ BaseApi                                                  │    │   │
│  │  │  ├─ requests.Session (连接复用)                          │    │   │
│  │  │  ├─ Token 自动管理: set_token() → Authorization 头       │    │   │
│  │  │  ├─ 统一 URL 拼接: base_url + path                       │    │   │
│  │  │  ├─ 统一超时: timeout=15s                                │    │   │
│  │  │  ├─ 自动重试: 500/502/503/504 自动重试 1 次              │    │   │
│  │  │  ├─ 连接失败容错: ConnectionError → mock 503 响应        │    │   │
│  │  │  └─ Allure 自动 attach: 请求/响应/异常                   │    │   │
│  │  └────────────────────────────────────────────────────────┘    │   │
│  └──────────────────────────┬─────────────────────────────────────┘   │
│                             │ 调用                                    │
│  ┌──────────────────────────▼─────────────────────────────────────┐   │
│  │  工具层 (utils/)                                               │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────────────┐    │   │
│  │  │ logger   │ │assertions│ │ db_utils │ │ allure_utils   │    │   │
│  │  │ (loguru) │ │HttpAssert│ │ DbClient │ │ attach 工具     │    │   │
│  │  │ 控制台+  │ │ .code()  │ │ .query() │ │ · 请求/响应    │    │   │
│  │  │ 文件日志  │ │ .success │ │ .execute │ │ · 数据库结果   │    │   │
│  │  └──────────┘ │ .jsonpath│ │ .assert_ │ │ · 异常        │    │   │
│  │               │ .contains│ │  value() │ └────────────────┘    │   │
│  │               └──────────┘ │ .assert_ │                        │   │
│  │                            │  exists() │                       │   │
│  │                            └──────────┘                       │   │
│  └────────────────────────────────────────────────────────────────┘   │
│                                                                        │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## ✨ 特性矩阵

### 🎯 核心能力

| 特性 | 说明 | 实现方式 |
|------|------|---------|
| **🏛️ POM 三层架构** | 参考 Page Object Model，每业务模块封装为独立 API 对象 | `BaseApi` → `LoginApi`/`RoleApi`/`UserApi` |
| **🔑 Token 自动管理** | Session 级 fixture 一次登录，所有测试共享 | `admin_login` fixture → `set_token()` → `Authorization` 头 |
| **✅ 双维度断言** | API 响应 + MySQL 数据库落盘，两个维度互相印证 | `HttpAssert` + `DbClient.assert_*()` |
| **📊 Allure 动态报告** | 请求/响应/异常自动 attach，失败按类别分组 | `allure_utils.py` + `pytest_runtest_makereport` |
| **🔄 失败自动重试** | 网络波动/偶发超时自动重试 1 次，间隔 1s | `requests.Retry` + `--reruns 1` |
| **🛡️ 连接失败容错** | ConnectionError/Timeout 不崩溃，返回 mock 503 | `BaseApi.request()` try-except 容错 |
| **⚡ 双引擎驱动** | 代码用例 + Excel 数据驱动混合执行 | `tests/` + `testcases/` 统一入口 |

### 🏢 企业级特性

| 特性 | 说明 |
|------|------|
| **🐳 Docker 容器化** | 6 容器编排：MySQL + Redis + RuoYi 后端 + Test Runner + Allure + Nginx |
| **🌍 多环境切换** | `--env=dev/staging/prod/docker` 一键切换，加载对应 `.env` |
| **📊 用例分级** | P0（冒烟）/ P1（异常）/ P2（辅助），支持 `-m` 过滤 |
| **⚡ 并发执行** | pytest-xdist 多进程并行，`-n 4` 回归测试缩短 70% |
| **📋 Excel 数据驱动** | 数据与代码分离，Jinja2 模板引擎 + JSONPath/SQL 断言 |
| **🔄 Jenkins CI/CD** | 完整 Pipeline：拉代码 → `docker compose up` → `wait_for_api` → pytest → Allure → 钉钉通知 |
| **🔔 钉钉通知** | 构建成功/失败自动推送钉钉机器人消息 |
| **📈 Allure 报告服务** | Nginx 容器持续提供历史报告访问 `http://host:8088` |

---

## 🛠️ 技术栈

### 🐍 测试核心

| 组件 | 用途 | 最低版本 | 当前版本 |
|------|------|---------|---------|
| ![Python](https://img.shields.io/badge/-Python-3776AB?logo=python&logoColor=white) Python | 编程语言 | 3.10 | 3.11 / 3.14 |
| ![Pytest](https://img.shields.io/badge/-Pytest-0A9EDC?logo=pytest&logoColor=white) pytest | 测试框架 | 7.4 | 9.1 |
| ![Requests](https://img.shields.io/badge/-Requests-239120?logo=python&logoColor=white) requests | HTTP 客户端 | 2.31 | 2.32 |
| allure-pytest | Allure 报告集成 | 2.13 | 2.13+ |
| pytest-xdist | 并发执行 | 3.5 | 3.6+ |
| pytest-rerunfailures | 失败重试 | 12.0 | 14.0+ |

### 🔍 数据 & 断言

| 组件 | 用途 | 说明 |
|------|------|------|
| ![MySQL](https://img.shields.io/badge/-MySQL-4479A1?logo=mysql&logoColor=white) mysql-connector-python | MySQL 连接与断言 | `assert_value` / `assert_exists` |
| jsonpath | JSONPath 响应断言 | `$.data.xxx` 精确匹配 |
| ![Excel](https://img.shields.io/badge/-Excel-217346?logo=microsoftexcel&logoColor=white) openpyxl | Excel 数据读取 | 支持 `is_true` 筛选 |
| jinja2 | 模板引擎 | `{{TOKEN}}` 变量注入 |

### 🏗️ 基础设施

| 组件 | 用途 | 版本 |
|------|------|------|
| ![Docker](https://img.shields.io/badge/-Docker-2496ED?logo=docker&logoColor=white) Docker | 容器运行时 | 24+ |
| ![Docker Compose](https://img.shields.io/badge/-Compose-2496ED?logo=docker&logoColor=white) Docker Compose | 服务编排 | 2.24+ |
| ![Allure](https://img.shields.io/badge/-Allure-FF6600?logo=simpleanalytics&logoColor=white) Allure CLI | 报告生成 | 2.32 |
| ![Nginx](https://img.shields.io/badge/-Nginx-009639?logo=nginx&logoColor=white) Nginx | 报告静态服务 | Alpine |
| ![Jenkins](https://img.shields.io/badge/-Jenkins-D24939?logo=jenkins&logoColor=white) Jenkins | CI/CD 流水线 | Rocky Linux 9 |

---

## 🚀 快速开始

### 📦 1. 环境准备

```bash
# 克隆项目
git clone https://github.com/Mavie521/ruoyi-api-test.git
cd ruoyi_api_test

# 一键搭环境（venv + 依赖 + pre-commit）
make setup

# 或者手动：
# python -m venv .venv
# source .venv/Scripts/activate   # Windows
# source .venv/bin/activate       # Mac/Linux
# pip install -r requirements.txt
```

### ⚙️ 2. 配置环境变量

```bash
cp .env.example .env
```

然后编辑 `.env`：

```ini
BASE_URL=http://localhost:8080
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123
DB_HOST=127.0.0.1
DB_PORT=3306
DB_NAME=ry-vue
DB_USER=root
DB_PASSWORD=123456
```

### 🧪 3. 运行测试

```bash
# ── 最常用 ──
make test          # 跑 P0 冒烟（10 条，< 30s）
make test-all      # 跑全量测试（31 条，< 2min）
make test-keyword KW=login  # 按关键字

# ── 或者用 run.py ──
python run.py run -m p0              # P0 冒烟
python run.py run --env=staging      # 指定环境
python run.py run -k login           # 关键字过滤
python run.py run -n 4               # 4 进程并发
python run.py run --reruns 2         # 失败重试
python run.py run --help             # 查看全部选项
```

### 📊 4. 生成报告

```bash
make report        # 生成 Allure HTML 报告
make open-report   # 打开报告
# 或：python run.py report
```

---

## 📁 项目结构

```
ruoyi_api_test/
│
├── api/                              # ═══ API 对象层（POM 模式）═══
│   ├── __init__.py                   # 统一导出所有 API 类
│   ├── base_api.py                   # 基类：Session/Token/重试/容错/Allure
│   ├── login_api.py                  # 登录模块：login() / get_info() / get_routers()
│   ├── role_api.py                   # 角色管理：CRUD + 状态 + 下拉 + 部门树
│   ├── user_api.py                   # 测试用户管理（旧版接口）
│   └── system_user_api.py            # 真实用户业务：增删改查 + 改密 + 状态
│
├── tests/                            # ═══ 测试用例层（代码驱动）═══
│   ├── __init__.py
│   ├── conftest.py                   # Fixtures: admin_login / db / new_role_data / 自动清理
│   ├── test_role.py                  # 角色管理 10 条（P0×5, P1×2, P2×3）
│   ├── test_system_user.py           # 真实用户 9 条（P0×4, P1×5）
│   ├── test_security.py              # 安全测试 11 条（SQL注入/XSS/越权/超长输入）
│   └── test_business_flow.py         # 业务流程 1 条（用户→角色→分配→登录→清理）
│
├── testcases/                        # ═══ 测试用例层（Excel 数据驱动）═══
│   ├── __init__.py
│   └── test_excel_driver.py          # Excel 数据驱动执行器（三层架构）
│
├── data/                             # Excel 测试数据文件
│   ├── test_cases.xlsx               # 主测试数据文件
│   └── test_cases_final.xlsx         # 备用/归档
│
├── config/                           # ═══ 配置层 ═══
│   ├── __init__.py                   # 统一导出配置
│   └── config.py                     # 多环境配置（dev/staging/prod/docker）
│                                    #   - BASE_URL / DB_CONFIG / EXCEL_FILE
│                                    #   - 自动加载 .env.{env} 文件
│                                    #   - ensure_dirs() 自动创建报告/日志目录
│
├── utils/                            # ═══ 工具层 ═══
│   ├── __init__.py
│   ├── logger.py                     # 日志（loguru，控制台彩色 + 文件按天滚动）
│   ├── assertions.py                 # HTTP 断言器（状态码/success/code/JSONPath/包含）
│   ├── db_utils.py                   # 数据库客户端（query/execute/assert_value/assert_exists）
│   ├── excel_utils.py                # Excel 读取（is_true 筛选 + 字段映射）
│   ├── data_driver.py                # 数据驱动引擎（Jinja2渲染/发请求/断言/提取变量）
│   └── allure_utils.py               # Allure 工具（attach 请求/响应/数据库/日志）
│
├── docs/                             # ═══ 文档体系 ═══
│   ├── test-plan/                    # 测试计划
│   │   └── role-management-plan.md   # 角色管理测试计划（范围/策略/数据/风险）
│   ├── test-cases/                   # 测试用例文档
│   │   └── role-management-cases.md  # 10 条角色管理手工用例详情
│   ├── bug-reports/                  # 缺陷报告
│   │   └── bug-001-xss-json-crash.md # BUG-001: <字符致Jackson JSON 500
│   └── test-summary/                 # 测试总结
│       └── role-management-summary.md# 测试总结报告（通过率/缺陷/改进建议）
│
├── scripts/                          # ═══ 运维脚本 ═══
│   ├── run_all.sh                    # 主入口：启服务→等就绪→跑测试→生成报告→通知
│   ├── test_and_report.sh            # Docker 一键测试 + 报告 + 部署
│   ├── wait_for_api.sh               # 等待后端就绪（POST /login 验证 token）
│   ├── gen_excel.py                  # Excel 测试数据生成工具
│   ├── init_excel_template.py        # Excel 模板初始化
│   └── performance_test.py           # Locust 性能测试脚本
│
├── docker/                           # ═══ Docker 构建文件 ═══
│   ├── ruoyi/                        # RuoYi 后端 Dockerfile + JAR 包
│   │   └── Dockerfile               # JDK 17 + Spring Boot JAR
│   ├── allure/                       # Allure CLI 生成器镜像
│   │   └── Dockerfile               # Allure 2.32 + Java
│   └── mysql/                        # MySQL 初始化 SQL
│       └── init/                     # 建表/初始化数据脚本
│
├── .env                              # 环境变量（默认 dev 环境）
├── .env.example                      # 环境变量模板
├── .env.staging                      # 预发布环境配置
├── .dockerignore                     # Docker 构建忽略（__pycache__/.env 等）
├── .gitignore
├── .github/
│   └── workflows/
│       └── test.yml                  # GitHub Actions 配置（结构检查 + 导入验证）
│
├── requirements.txt                  # Python 依赖
├── pytest.ini                        # Pytest 配置（标记/日志/Allure/报告）
├── conftest.py                       # 全局 conftest（Allure 环境/失败附件/汇总）
├── run.py                            # 统一运行入口
├── Dockerfile.test                   # Test Runner 镜像（Python 3.11 + 项目代码）
├── docker-compose.yml                # 服务编排（6 个容器 + 网络 + 卷）
└── Jenkinsfile                       # Jenkins Pipeline 定义
```

---

## 🎯 架构设计详解

### 三层架构（POM 模式）

框架采用 **Page Object Model（POM）** 思想，将测试代码分为三层，层间单向依赖：

```
┌──────────────────────────────────────────────────────────────────────────┐
│                           测试用例层 (Test Layer)                         │
│                                                                          │
│  功能: 编排业务场景、组合断言、异常验证                                     │
│  文件: tests/test_*.py                                                   │
│  原则: 只关注"测什么"，不关心"怎么发请求"                                   │
│                                                                          │
│  def test_create_role(role_api, new_role_data, db):                      │
│      resp = role_api.create_role(new_role_data)       # 调用 API 层      │
│      assert resp.get("code") == 200                    # API 断言        │
│      db.assert_exists("SELECT ...", ...)               # DB 断言         │
│                                                                          │
├──────────────────────────────────────────────────────────────────────────┤
│                           API 对象层 (API Layer)                          │
│                                                                          │
│  功能: 封装具体接口的 HTTP 操作，一个方法 = 一个 API                        │
│  文件: api/*.py                                                          │
│  原则: 只关心"怎么调接口"，不关心"请求怎么发"                                │
│                                                                          │
│  class RoleApi(BaseApi):                                                 │
│      def create_role(self, data):                                        │
│          return self.post("/system/role", json=data)                     │
│      def list_roles(self, params=None):                                  │
│          return self.get("/system/role/list", params=params)             │
│                                                                          │
├──────────────────────────────────────────────────────────────────────────┤
│                          基础设施层 (Base Layer)                          │
│                                                                          │
│  功能: Session 管理 / Token 注入 / URL 拼接 / 超时重试 / 容错 / 日志      │
│  文件: api/base_api.py                                                   │
│  原则: 封装所有"与具体业务无关"的通用能力                                    │
│                                                                          │
│  class BaseApi:                                                          │
│      session = requests.Session()       # 连接复用                       │
│      set_token(t) → Authorization       # Token 自动注入                  │
│      request() → 超时/重试/容错/日志/Allure attach                       │
└──────────────────────────────────────────────────────────────────────────┘
```

### 数据流（一次测试执行的完整路径）

```
                             Pytest 启动
                                │
                                ▼
                    ┌───────────────────────┐
                    │    pytest.ini         │
                    │  - testpaths=tests    │
                    │  - markers: p0/p1/p2  │
                    │  - allure/日志配置     │
                    └───────────┬───────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │  conftest.py (全局)    │
                    │  pytest_configure      │
                    │  → 输出环境信息到日志   │
                    │  → Allure 环境配置      │
                    └───────────┬───────────┘
                                │
                                ▼
              ╔═══════════════════════════════╗
              ║   pytest_collection           ║
              ║   发现 tests/ 下 test_*.py    ║
              ║   匹配 test_* 函数名          ║
              ║   按 -m 过滤 (p0/p1/p2)      ║
              ╚═══════════════════════════════╝
                                │
                                ▼
              ╔═══════════════════════════════╗
              ║   Session 级 Fixture          ║
              ║   (整个测试只会执行一次)       ║
              ╚═══════════════════════════════╝
                                │
                    ┌───────────┴───────────┐
                    │                       │
                    ▼                       ▼
          ┌──────────────────┐   ┌──────────────────┐
          │ admin_login      │   │ db (DbClient)    │
          │ POST /login      │   │ connect to MySQL │
          │ → token          │   │ 复用连接         │
          └────────┬─────────┘   └────────┬─────────┘
                   │                      │
                   ▼                      │
          ┌──────────────────┐            │
          │ set_token(token) │            │
          │ → Authorization  │            │
          └──────────────────┘            │
                   │                      │
                   ▼                      ▼
              ╔═══════════════════════════════╗
              ║   测试函数执行                 ║
              ║   def test_xxx(api, db):     ║
              ╚═══════════════════════════════╝
                                │
                    ┌───────────┴───────────┐
                    │                       │
                    ▼                       ▼
          ┌──────────────────┐   ┌──────────────────┐
          │  API 对象调用     │   │  数据库断言       │
          │  api.do_something│   │  db.assert_value  │
          │  → HTTP 请求     │   │  → SQL 查询       │
          └────────┬─────────┘   └────────┬─────────┘
                   │                      │
                   ▼                      │
          ┌──────────────────┐            │
          │  HTTP 响应       │            │
          │  + Allure Attach  │            │
          │  请求/响应/异常   │            │
          └────────┬─────────┘            │
                   │                      │
                   ▼                      ▼
          ┌──────────────────────────────────────┐
          │  双维度断言                           │
          │  ✅ API 断言: code=200 / msg=成功     │
          │  ✅ DB 断言: 数据库落盘值匹配预期      │
          │  ❌ 任一失败 → Allure attach 失败信息  │
          └──────────────────────────────────────┘
                                │
                                ▼
              ╔═══════════════════════════════╗
              ║   下一个测试函数...            ║
              ╚═══════════════════════════════╝
                                │
                                ▼
              ╔═══════════════════════════════╗
              ║   pytest_sessionfinish        ║
              ║   输出测试汇总 (P/F/T)        ║
              ╚═══════════════════════════════╝
                                │
                                ▼
                    ┌───────────────────────┐
                    │   Allure 报告生成      │
                    │   allure generate     │
                    │   → allure-report/    │
                    └───────────────────────┘
```

### Fixture 依赖树

```
pytest session 开始
    │
    ├── admin_login (session scope) ──────────────────────────────┐
    │   └── LoginApi.login("admin", "admin123") → token          │
    │       │                                                     │
    │       ├── login_api (→ 返回 LoginApi 实例)                  │
    │       ├── user_api (→ 继承 token 的 UserApi)                │
    │       ├── role_api (→ 继承 token 的 RoleApi)                │
    │       └── system_user_api (→ 继承 token 的 SystemUserApi)   │
    │                                                             │
    ├── db (session scope) ─────────────────────────────────────┐ │
    │   └── DbClient() → connect MySQL                          │ │
    │                                                           │ │
    ├── new_role_data (function scope) ─────────────────────────┐ │
    │   ├── 生成: {roleName, roleKey, ...} + 时间戳              │ │
    │   └── finalizer: DELETE FROM sys_role WHERE role_key=...  │ │
    │                                                           │ │
    └── new_real_user_data (function scope) ────────────────────┘ │
        └── 生成: {userName, nickName, password, ...} + 时间戳     │
                                                                  │
每个测试函数可以按需注入任意组合：                                   │
    def test_xxx(role_api, db):          ← 角色 + 数据库           │
    def test_xxx(system_user_api, db):   ← 用户 + 数据库           │
    def test_xxx(login_api):             ← 登录 API                │
    def test_xxx(new_role_data):         ← 测试数据                │
```

---

## ⚙️ 测试引擎

### 双引擎架构

框架支持**两种测试用例来源**，可以在一次运行中混合执行：

```
                    ┌────────────────────────────────────────────┐
                    │           pytest 统一入口                  │
                    │  pytest tests/ testcases/test_excel_driver │
                    └────────────────┬───────────────────────────┘
                                     │
                    ┌────────────────┴────────────────┐
                    │                                 │
                    ▼                                 ▼
    ┌──────────────────────────┐      ┌──────────────────────────┐
    │  引擎一：代码驱动         │      │  引擎二：Excel 数据驱动   │
    │  tests/test_*.py         │      │  testcases/ + data/*.xlsx │
    │                          │      │                          │
    │  特点：                   │      │  特点：                   │
    │  · 灵活的业务编排          │      │  · 数据与代码分离         │
    │  · 复杂断言逻辑           │      │  · 非技术人员可维护       │
    │  · 条件分支/循环          │      │  · 批量用例管理           │
    │  · 异常场景覆盖           │      │  · 变量引用 {{TOKEN}}    │
    │                          │      │                          │
    │  维护者：自动化测试工程师   │      │  维护者：业务测试人员     │
    └──────────────────────────┘      └──────────────────────────┘
                                     │
                                     ▼
                    ┌────────────────────────────────────────────┐
                    │  结果统一输出到 Allure 报告                 │
                    │  · 代码用例: static allure 注解            │
                    │  · Excel用例: dynamic allure 属性          │
                    └────────────────────────────────────────────┘
```

### 引擎二详细工作流

```
开始
 │
 ▼
读取 Excel: read_excel()
 ├── 打开 test_cases.xlsx
 ├── 过滤 is_true=True 的有效用例
 └── 返回 list[dict]
 │
 ▼
构建参数化列表: _build_params()
 ├── case["marker"] → @pytest.mark.p0/p1/p2
 └── 返回 parametrize 参数列表
 │
 ▼
setup_module()
 ├── POST /login (admin/admin123)
 └── GLOBAL_VARS["TOKEN"] = token
 │
 ▼
逐条执行测试 (每个 case 执行以下步骤):
 │
 ├── 步骤1: allure_init(case)
 │   └── dynamic.feature/story/title/severity
 │
 ├── 步骤2: render_case(case, GLOBAL_VARS)
 │   └── Jinja2 渲染 {{TOKEN}} 等变量
 │
 ├── 步骤3: send_request(case)
 │   ├── 拼接 URL: BASE_URL + path
 │   ├── 发送 HTTP 请求
 │   └── Allure attach 请求/响应
 │
 ├── 步骤4: do_assert(case, response)
 │   ├── check + expected → JSONPath 断言
 │   └── 或 包含断言
 │
 ├── 步骤5: do_db_assert(case)
 │   ├── sql_check + sql_expected → 数据库断言
 │   └── DbClient.query_one() + 值比较
 │
 └── 步骤6: do_extract(case, response, GLOBAL_VARS)
     ├── jsonExData → 从响应 JSON 提取变量
     └── sqlExData → 从数据库提取变量
```

---

## 🐳 Docker 部署

### 容器架构 (6 容器)

```
┌─────────────────────────────────────────────────────────────────────┐
│                      Linux Server (Docker)                          │
│                                                                     │
│  ┌──────────────────── ry-network (Bridge) ──────────────────────┐  │
│  │                                                                │  │
│  │  ┌──────────┐  ┌──────────┐  ┌────────────────────────┐      │  │
│  │  │ MySQL 8.0│  │ Redis 7  │  │ RuoYi API (JDK 17)     │      │  │
│  │  │ 3306     │  │ 6379     │  │ 8080                   │      │  │
│  │  │ ry-vue   │  │ 缓存     │  │ Spring Boot 4.x        │      │  │
│  │  └────┬─────┘  └────┬─────┘  └───────────┬────────────┘      │  │
│  │       │             │                    │                    │  │
│  │       └──────┬──────┘                    │                    │  │
│  │              │                           │                    │  │
│  │     ┌────────▼───────────────────────────▼────────┐          │  │
│  │     │          Test Runner (Python 3.11)           │          │  │
│  │     │          docker compose --profile test run   │          │  │
│  │     │          · wait_for_api.sh (POST验证)        │          │  │
│  │     │          · pytest + 代码 + Excel 驱动        │          │  │
│  │     │          · 输出 allure-results               │          │  │
│  │     └──────────────────┬───────────────────────────┘          │  │
│  │                        │                                       │  │
│  │     ┌──────────────────▼───────────────────────────┐          │  │
│  │     │          Allure Reporter                      │          │  │
│  │     │          allure generate → allure-report       │          │  │
│  │     └──────────────────┬───────────────────────────┘          │  │
│  │                        │                                       │  │
│  │     ┌──────────────────▼───────────────────────────┐          │  │
│  │     │          Nginx (Alpine)                       │          │  │
│  │     │          8088 → /usr/share/nginx/html        │          │  │
│  │     │          提供 Allure 报告访问                  │          │  │
│  │     └──────────────────────────────────────────────┘          │  │
│  └────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

### 一键部署

```bash
# 完整流程（启动服务 + 等待就绪 + 执行测试 + 生成报告）
bash scripts/test_and_report.sh

# 或分步执行
./scripts/run_all.sh all fast
```

### Docker Compose 命令速查

```bash
# 启动所有后端服务
docker compose up -d

# 运行测试（带 profile 激活 test-runner）
docker compose --profile test run --rm test-runner bash /app/scripts/wait_for_api.sh
docker compose --profile test run --rm test-runner sh -c "pytest tests/ --alluredir=reports/allure-results -v"

# 只跑 P0
docker compose --profile test run --rm test-runner sh -c "pytest tests/ -m p0 --alluredir=reports/allure-results -v"

# 生成 Allure 报告
docker compose --profile report run --rm allure-reporter

# 查看报告
# http://<server-ip>:8088
```

### 环境变量 (Docker)

| 变量 | 说明 | Docker 默认值 |
|------|------|--------------|
| `ENV` | 运行环境 | `docker` |
| `BASE_URL` | RuoYi 后端地址 | `http://ruoyi-api:8080` |
| `DB_HOST` | 数据库主机 | `mysql` |
| `DB_PORT` | 数据库端口 | `3306` |
| `DB_NAME` | 数据库名 | `ry-vue` |
| `DB_USER` | 数据库用户 | `root` |
| `DB_PASSWORD` | 数据库密码 | `root` |

---

## 🔄 CI/CD 流水线

### Jenkins Pipeline 完整流程

```groovy
pipeline {
    agent any
    parameters {
        choice(name: 'MODE', choices: ['fast', 'clean'], description: '运行模式')
        choice(name: 'MARKER', choices: ['p0', 'p1', 'p2', 'all'], description: '用例级别')
    }
    triggers {
        cron('H 8 * * *')  // 每日凌晨自动回归
    }
    stages {
        stage('全流程') {
            steps {
                sh "bash /home/yy/ruoyi-api-test/scripts/run_all.sh ${params.MARKER} ${params.MODE}"
            }
        }
        stage('Allure 报告') {
            steps {
                sh 'cp -r /home/yy/ruoyi-api-test/reports/allure-results \${WORKSPACE}/allure-results'
                allure includeProperties: true, results: [[path: 'allure-results']]
            }
        }
    }
    post {
        always {
            script {
                currentBuild.displayName = "#${BUILD_NUMBER}-${params.MARKER}-${params.MODE}"
            }
        }
    }
}
```

### 执行流程时序图

```
时间线
│
├─ 开发者 Push / Jenkins UI 触发
│
├─ Stage 1: 全流程 ──────────────────────────────────────────────
│  ├─ 1.1 docker compose up -d
│  │    ├─ 创建/启动 MySQL 容器 (健康检查: ping)
│  │    ├─ 创建/启动 Redis 容器 (健康检查: ping)
│  │    └─ 创建/启动 RuoYi 后端 (健康检查: curl /login)
│  │        └─ 依赖等待: MySQL + Redis 健康后才启动
│  │
│  ├─ 1.2 docker compose --profile test run wait_for_api.sh
│  │    └─ 最多 40 次 × 5s = 200s 轮询
│  │        └─ POST /login {"admin","admin123"} → 验证 token
│  │
│  └─ 1.3 docker compose --profile test run pytest
│       ├─ 31 条代码用例 (tests/)
│       └─ N 条 Excel 驱动用例 (testcases/ + data/)
│           └─ 失败自动重试 1 次
│
├─ Stage 2: Allure 报告 ──────────────────────────────────────────
│  ├─ allure generate → allure-report
│  ├─ Jenkins 任务页面内嵌显示
│  └─ Nginx 独立服务 (http://192.168.159.128:8088)
│
└─ Post: 钉钉通知 ────────────────────────────────────────────────
   ├─ 成功: "✅ 构建成功 | P0:18/18 | 耗时:22s"
   └─ 失败: "❌ 构建失败 | 失败:3 | 耗时:15s"
```

### CI/CD 配置参数

| 参数 | 选项 | 说明 |
|------|------|------|
| `MODE` | `fast` / `clean` | `fast`: 增量启服务; `clean`: 重建所有容器 |
| `MARKER` | `p0` / `p1` / `p2` / `all` | 按用例级别过滤 |

### 触发器

| 触发方式 | 配置 |
|---------|------|
| 定时触发 | 每日凌晨 `H 8 * * *` |
| 手动触发 | Jenkins UI → Build with Parameters |
| 代码提交 | (预留) 通过 Webhook 触发 |

### 访问地址

| 服务 | 地址 |
|------|------|
| Jenkins | `http://192.168.159.128:8081` |
| Allure 报告 | Jenkins 构建页面内嵌 |
| Nginx 报告独立服务 | `http://192.168.159.128:8088` |
| RuoYi 后端 | `http://192.168.159.128:8080` |

---

## 📊 测试覆盖与策略

### 当前测试覆盖

| 模块 | 文件 | 代码用例 | P0 | P1 | P2 | 覆盖接口 |
|------|------|---------|----|----|----|---------|
| 角色管理 | `test_role.py` | 10 | 5 | 2 | 3 | list/detail/create/update/delete/status/option/deptTree/authUser |
| 真实用户管理 | `test_system_user.py` | 9 | 4 | 5 | 0 | list/detail/create/update/delete/status/resetPwd |
| 安全测试 | `test_security.py` | 11 | 0 | 10 | 1 | SQL注入4/XSS4+1/越权1/超长输入1 |
| 业务流程 | `test_business_flow.py` | 1 | 1 | 0 | 0 | 用户+角色全生命周期 |
| **合计** | | **31** | **10** | **17** | **4** | **20+ 接口** |
| Excel 数据驱动 | `test_excel_driver.py` | 依数据 | — | — | — | 配置化的增删改查 |

### 测试执行策略

```
                  代码提交/PR
                      │
                      ▼
              ╔══════════════════╗
              ║   P0 冒烟测试    ║  ← 10条，<2分钟
              ║   核心功能验证    ║     快速反馈
              ╚══════════════════╝
                      │
                    全部通过?
                    /      \
                  是        否
                  │         │
                  ▼         ▼
        ╔══════════════╗  阻断，通知开发者修复
        ║  P0+P1 回归  ║  ← 27条，<5分钟
        ║  异常场景验证  ║     每日构建
        ╚══════════════╝
                │
              全部通过?
              /      \
            是        否
            │         │
            ▼         ▼
   ╔════════════════╗  记录缺陷，通知修复
   ║  全量测试 (all) ║  ← 31+条，<30秒
   ║  + Excel 驱动  ║     发版前执行
   ╚════════════════╝
```

### 测试数据管理

| 数据类型 | 生成方式 | 清理方式 | 示例 |
|---------|---------|---------|------|
| 角色数据 | fixture `new_role_data` (+ 时间戳) | `request.addfinalizer` → DELETE SQL | `测试角色_283746` |
| 用户数据 | fixture `new_real_user_data` (+ 时间戳) | 硬删除 (业务流末尾) | `test_user_847562` |
| 角色 Key | `f"test_role_{suffix}"` | 同上 DELETE | `test_role_283746` |
| 菜单/角色关联 | `menuIds: [], roleIds: []` | — | 不创建关联 |
| 数据库隔离 | 每个测试独立数据 | 自动清理或逻辑删除 | del_flag='2' |

---

## 🧹 代码质量与工程化

### 代码质量保障体系

```
┌─ 提交代码前 ─────────────────────────────────────────────────┐
│                                                               │
│  pre-commit 自动检查                                           │
│  ┌────────────────────────────────────────────────────────┐   │
│  │ • 行尾空格 / 文件末尾换行 / YAML 语法 / 大文件检测      │   │
│  │ • black 自动格式化 Python 代码（行宽 120）              │   │
│  │ • 私钥泄漏检测                                          │   │
│  └────────────────────────────────────────────────────────┘   │
│                                                               │
│  git commit → 检查通过 → 提交成功                              │
│  git commit → 检查失败 → 自动拦截                             │
│                                                               │
├─ 本地开发 ────────────────────────────────────────────────────┤
│                                                               │
│  make lint        pylint 静态代码分析          10.00/10 ✅     │
│  make format      black 代码格式化             自动修复       │
│  make coverage    pytest-cov 覆盖率报告         98%+ ✅       │
│  make test        跑 P0 冒烟测试               < 2min         │
│                                                               │
├─ CI/CD 流水线 ────────────────────────────────────────────────┤
│                                                               │
│  Jenkins Pipeline → 拉代码 → pylint → pytest → Allure → 钉钉  │
│                                                               │
└───────────────────────────────────────────────────────────────┘
```

### pylint 评分演进

| 阶段 | 分数 | 问题数 | 说明 |
|------|------|--------|------|
| 初始 | 7.39 | 200+ | 导入顺序混乱、缺 docstring、异常捕获过宽 |
| 配置 `.pylintrc` | 8.25 | 146 | 屏蔽 CRLF 等非代码质量问题 |
| 修复 api/ utils/ 核心代码 | 9.47 | 37 | 导入顺序、异常收窄、参数重构 |
| 全面清理（含测试文件） | **10.00** | **0** | **满分！** |

### 工程化工具链

| 文件 | 作用 |
|------|------|
| `Makefile` | 统一命令入口（`make setup`/`make test`/`make lint`/`make format`） |
| `.pylintrc` | 代码规范配置（行宽 120、忽略非代码质量问题） |
| `.pre-commit-config.yaml` | 提交前自动检查（格式/语法/安全） |
| `.coveragerc` | 覆盖率配置（api/ + utils/ + config/） |
| `requirements-dev.txt` | 开发工具依赖（pylint + black + pre-commit + pytest-cov） |

---

## 🔒 安全测试

覆盖 **SQL 注入 / XSS / 越权 / 边界异常** 四大类安全场景：

### SQL 注入 (4 条)

```python
@pytest.mark.parametrize("payload", [
    "admin' OR '1'='1",
    "admin'--",
    "admin' OR 1=1--",
    'admin" OR "1"="1',
])
def test_login_sql_injection(self, payload):
    token = api.login(payload, "admin123")
    assert token is None  # 恶意输入不应登录成功
```

### XSS 注入 (5 条)

```python
@pytest.mark.parametrize("xss_payload", [
    '<script>alert("xss")</script>',
    '"><script>alert(1)</script>',
    'javascript:alert(1)',
    '<ScRiPt>alert(1)</ScRiPt>',
])
def test_role_name_xss(self, xss_payload):
    # 验证 XSS payload 不应导致服务端 500
    assert resp.get("code") != 500

# 已知 Bug: < 字符导致 Jackson JSON 解析崩溃
@pytest.mark.xfail(reason="Ruoyi Bug: '<'字符导致Jackson JSON 500")
def test_role_name_xss_crash_bug(self):
    # 预期返回 400，实际返回 500
```

### 越权测试 (1 条)

```python
def test_fake_token_access(self):
    fake_tokens = [
        "eyJhbGciOiJIUzUxMiJ9.fake.xxxx",  # 伪造 JWT
        "Bearer invalid_token_here",        # 格式错误
        "",                                  # 空字符串
        "abcdef123456",                      # 随机字符串
    ]
    for fake in fake_tokens:
        api.set_token(fake)
        resp = api.get("/getInfo")
        assert resp.status_code in (401, 403) or body.get("code") != 200
```

---

## ✅ 双维度断言体系

### 维度一：API 响应断言

```python
# HTTP 状态码检查
assert resp.status_code == 200
assertions.status_code(resp, 200)

# 若依响应结构检查
assert resp.json()["code"] == 200
assert resp.json()["success"] is True
assertions.code(resp, 200)
assertions.success(resp)

# JSONPath 精确匹配
assertions.jsonpath_match(resp, "$.data.username", "admin")

# 包含断言
assertions.contains(resp, "操作成功")

# 列表不为空
assertions.list_not_empty(resp, "$.rows")
```

### 维度二：MySQL 数据库断言

```python
# 值相等断言
db.assert_value(
    "SELECT status FROM sys_role WHERE role_id=%s",
    expected="1",
    params=(role_id,),
)

# 记录存在断言
db.assert_exists(
    "SELECT role_id FROM sys_role WHERE role_key=%s",
    params=(new_role_data["roleKey"],),
)

# 记录不存在断言（验证删除）
db.assert_not_exists(
    "SELECT user_id FROM sys_user WHERE user_name=%s",
    params=("test_user_cleanup",),
)

# 原生查询
row = db.query_one("SELECT user_id FROM sys_user WHERE user_name=%s", (username,))
rows = db.query("SELECT * FROM sys_role WHERE status=%s", ("0",))
affected = db.execute("UPDATE sys_user SET status=%s WHERE user_id=%s", ("1", user_id))
```

### 断言维度对比

| 维度 | 验证对象 | 优势 | 劣势 | 适用场景 |
|------|---------|------|------|---------|
| API 断言 | HTTP 响应 | 执行快，不依赖 DB 连接 | 只验证接口返回，不保证数据落盘 | 查询/校验类接口 |
| DB 断言 | MySQL 数据 | 验证数据真正持久化 | 需要 DB 连接，对数据库有侵入 | 增/删/改/状态变更 |

---

## 📋 数据驱动引擎

### Excel 用例结构

| 字段 | 说明 | 示例 |
|------|------|------|
| `id` | 用例编号 | `TC001` |
| `title` | 用例标题 | `新增角色-正常创建` |
| `feature` | Allure feature | `角色管理模块` |
| `story` | Allure story | `角色新增` |
| `severity` | 严重程度 | `严重` |
| `marker` | 用例标记 | `p0` |
| `method` | HTTP 方法 | `post` |
| `path` | 请求路径 | `/system/role` |
| `headers` | 请求头(JSON) | `{"Authorization": "Bearer {{TOKEN}}"}` |
| `json` | 请求体(JSON) | `{"roleName": "测试角色", ...}` |
| `check` | JSONPath 断言 | `$.code` |
| `expected` | 预期值 | `200` |
| `sql_check` | 数据库断言 SQL | `SELECT role_id FROM sys_role WHERE role_key='{{roleKey}}'` |
| `sql_expected` | 数据库断言预期值 | 非空 |
| `jsonExData` | 从响应提取变量 | `{"TOKEN": "$..token"}` |
| `sqlExData` | 从数据库提取变量 | `{"roleId": "SELECT id FROM sys_role ORDER BY id DESC LIMIT 1"}` |
| `is_true` | 是否启用 | `TRUE` |

### 三层数据驱动架构

```
Excel 行数据 (原始)
    │
    ▼
┌─────────────────────────────┐
│  render_case()              │
│  Jinja2 模板渲染            │
│  {{TOKEN}} → eyJhbG...     │
│  {{roleKey}} → test_8472   │
└──────────┬──────────────────┘
           │
           ▼
┌─────────────────────────────┐
│  send_request()             │
│  拼接 URL → 发送 HTTP      │
│  自动 attach 请求/响应      │
└──────────┬──────────────────┘
           │
           ▼
┌─────────────────────────────┐
│  do_assert() + do_db_assert│
│  JSONPath 断言              │
│  数据库落盘断言              │
└──────────┬──────────────────┘
           │
           ▼
┌─────────────────────────────┐
│  do_extract()               │
│  jsonExData → 全局变量      │
│  sqlExData → 全局变量       │
│  供后续用例引用              │
└─────────────────────────────┘
```

---

## 💻 代码示例

### BaseApi 基类（完整）

```python
class BaseApi:
    """所有 API 对象的基类"""

    def __init__(self):
        self.session = requests.Session()
        self.base_url = BASE_URL.rstrip("/")
        self._token = None
        self.timeout = DEFAULT_TIMEOUT  # 15s

        # 自动重试策略（500/502/503/504 重试 1 次）
        retry_strategy = Retry(
            total=1, backoff_factor=1,
            status_forcelist=[500, 502, 503, 504],
            allowed_methods=["GET", "POST", "PUT", "DELETE"],
        )
        self.session.mount("http://", HTTPAdapter(max_retries=retry_strategy))
        self.session.mount("https://", HTTPAdapter(max_retries=retry_strategy))

    def set_token(self, token: str):
        self._token = token
        self.session.headers.update({"Authorization": f"Bearer {token}"})

    def request(self, method: str, url: str, **kwargs) -> Response:
        if not url.startswith("http"):
            url = f"{self.base_url}{url}"
        kwargs.setdefault("timeout", self.timeout)
        attach_request(method, url, headers=self.session.headers, **kwargs)
        try:
            res = self.session.request(method, url, **kwargs)
            attach_response(res)
            return res
        except requests.exceptions.ConnectionError as e:
            # 连接失败 → 返回 mock 503，不崩溃
            mock_res = Response(); mock_res.status_code = 503
            mock_res._content = b'{"code":500,"msg":"Connection refused"}'
            return mock_res
```

### 完整测试用例示例

```python
@allure.epic("若依接口测试")
@allure.feature("角色管理模块")
class TestRole:

    @allure.story("角色新增")
    @allure.title("新增角色 - 正常创建成功 + 数据库验证")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.p0
    def test_create_role(self, role_api, new_role_data, db):
        """创建新角色，并验证数据库落盘"""
        resp = role_api.create_role(new_role_data)
        assert resp.get("code") == 200, f"创建角色失败: {resp}"

        db.assert_exists(
            "SELECT role_id FROM sys_role WHERE role_key=%s",
            params=(new_role_data["roleKey"],),
        )
```

### Fixture 自动清理模式

```python
@pytest.fixture
def new_role_data(request, db) -> dict:
    """生成角色数据 + 自动清理"""
    suffix = str(int(time.time() * 1000))[-6:]
    role_key = f"test_role_{suffix}"
    data = {
        "roleName": f"测试角色_{suffix}",
        "roleKey": role_key,
        "roleSort": 1,
        "status": "0",
        "menuIds": [],
    }
    yield data

    # ★ 测试结束后自动清理，即使断言失败也会执行 ★
    def cleanup():
        db.execute("DELETE FROM sys_role WHERE role_key=%s", (role_key,))
    request.addfinalizer(cleanup)
```

---

## 📚 文档体系

```
docs/
├── test-plan/                          # 测试计划
│   └── role-management-plan.md         # · 测试范围与策略
│                                       # · 功能点/接口/优先级映射
│                                       # · 测试数据设计
│                                       # · 风险与应对方案
│
├── test-cases/                         # 测试用例
│   └── role-management-cases.md        # · 10 条角色管理手工用例
│                                       # · 每用例包含前置/步骤/预期/DB断言
│                                       # · 标注 P0/P1/P2 级别
│
├── bug-reports/                        # 缺陷报告
│   └── bug-001-xss-json-crash.md       # · BUG-001: <字符致500
│                                       # · 复现步骤/根因分析/影响范围
│
└── test-summary/                       # 测试总结
    └── role-management-summary.md      # · 执行概况/通过率/缺陷统计
                                       # · CI/CD 质量门禁状态
                                       # · 改进建议
```

---

## ❓ 常见问题与排错

### 1. Jenkins 构建报 "no tests ran in 0.02s"

**可能原因**：`docker compose run` 缺少 `--profile test`

```
# ❌ 错误写法
docker compose run --rm test-runner pytest tests/

# ✅ 正确写法（test-runner 服务配置了 profiles: [test]）
docker compose --profile test run --rm test-runner pytest tests/
```

**修复**：所有 `docker compose run test-runner` 命令都需要加 `--profile test`

### 2. Jenkins 报 "file or directory not found: testcases/test_excel_driver.py"

**可能原因**：宿主机 `testcases/` 目录为空，volume mount 覆盖了镜像内的文件

```
# 检查宿主机目录
ls -la /home/yy/ruoyi-api-test/testcases/

# 修复方案 A：确保宿主机有文件
# 修复方案 B：去掉 docker-compose.yml 中 testcases 的 volume mount
```

### 3. 所有测试报 "管理员登录失败"

**可能原因**：API 后端未就绪，或 wait_for_api.sh 验证条件太宽松

```
# 检查 wait_for_api.sh 是否用了 POST + token 验证
grep "token" /home/yy/ruoyi-api-test/scripts/wait_for_api.sh

# 手动验证 API
curl -X POST http://ruoyi-api:8080/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'
```

### 4. docker compose 报 "service not found"

**原因**：Docker Compose v2 对 profiles 的处理更严格

```
# 需要显式指定 --profile
docker compose --profile test run --rm test-runner ...
docker compose --profile report run --rm allure-reporter ...
```

### 5. 测试数据未清理

**原因**：测试异常中断导致 finalizer 未执行

```
# 手动清理（连接 MySQL 容器）
docker exec -it ry-mysql mysql -uroot -proot ry-vue
DELETE FROM sys_role WHERE role_key LIKE 'test_%';
DELETE FROM sys_user WHERE user_name LIKE 'test_%';
```

### 6. 如何切换环境？

```bash
# 方式一：环境变量
ENV=staging pytest tests/ -v

# 方式二：run.py 参数
python run.py run --env=staging

# 方式三：Docker 环境变量已由 docker-compose.yml 自动设置
```

### 7. 如何添加新接口的测试？

```
1. 在 api/ 下新建或扩展 API 对象（继承 BaseApi）
    class XxxApi(BaseApi):
        def do_something(self, data):
            return self.post("/xxx/do", json=data)

2. 在 tests/conftest.py 添加对应的 fixture
    @pytest.fixture(scope="session")
    def xxx_api(admin_login) -> XxxApi:
        api = XxxApi()
        api.set_token(admin_login.token)
        return api

3. 在 tests/ 下新建 test_xxx.py
    @pytest.mark.p0
    def test_xxx(self, xxx_api, db):
        resp = xxx_api.do_something(data)
        assert resp.get("code") == 200
        db.assert_exists("SELECT ...", ...)
```

### 8. 如何添加 Excel 数据驱动用例？

```
1. 编辑 data/test_cases.xlsx 添加新行
2. 填写: method / path / json / check / expected / marker 等字段
3. 设置 is_true=TRUE 启用用例
4. 运行 pytest tests/ testcases/ -v 即可
```

---

## 📋 更新日志

| 日期 | 版本 | 变更摘要 |
|------|------|---------|
| 2026-07-15 | **v3.0** 🎯 | **工程化工具链：pylint 10.0/10 + Makefile + pre-commit + 覆盖率配置** |
| 2026-07-15 | v2.1 🔧 | 修复 Jenkins profile/volume/wait_for_api 三连问题 |
| 2026-07-15 | v2.0 📝 | 完善 README 架构图、CI/CD 流水线全面更新 |
| 2026-07-13 | v1.1 🔒 | 新增安全测试、Excel 数据驱动、Allure 分类报告 |
| 2026-07-12 | v1.0 🚀 | 初始版本：角色/用户 CRUD + Docker 容器化部署 |

---

<div align="center">

**RuoYi API Test Framework** · Built with ❤️ by Mavie

[GitHub](https://github.com/Mavie521/ruoyi-api-test) · [Jenkins](http://192.168.159.128:8081) · [Allure Report](http://192.168.159.128:8088)

</div>
