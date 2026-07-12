# RuoYi API Test Framework

基于 Pytest + Requests + Allure 的接口自动化测试框架，覆盖若依管理系统（RuoYi）核心业务模块：登录认证、用户管理、角色管理。支持 Docker 容器化部署、CI/CD 流水线集成。

---

## 目录

- [特性](#特性)
- [技术栈](#技术栈)
- [快速开始](#快速开始)
- [项目结构](#项目结构)
- [架构设计](#架构设计)
- [Docker 部署](#docker-部署)
- [CI/CD 集成](#cicd-集成)
- [代码示例](#代码示例)
- [测试覆盖](#测试覆盖)
- [常见问题](#常见问题)

---

## 特性

### 核心能力

| 特性 | 说明 |
|------|------|
| API 分层封装（POM） | 参考 Page Object Model 思想，将每个业务模块的接口操作封装为独立 API 对象，消除重复代码 |
| Token 自动管理 | 基于 pytest session 级 fixture，一次登录自动保存 token，后续请求自动携带 Authorization 头 |
| 双维度断言 | API 响应断言（code / msg / success）+ MySQL 数据库落盘断言，两个维度互相印证 |
| Allure 动态报告 | 每个请求自动 attach 请求/响应/异常信息，失败原因按类别展示 |

### 企业级特性

| 特性 | 说明 |
|------|------|
| Docker 容器化部署 | Docker Compose 编排 MySQL + Redis + RuoYi 后端 + 测试执行器 + Allure 报告，一键启动完整环境 |
| 失败自动重试 | 基于 pytest-rerunfailures，偶发超时/网络波动自动重试 2 次，间隔 5 秒 |
| 多环境切换 | --env=dev/staging/prod/docker 一键切换，不同环境加载对应 .env 配置 |
| 用例分级 | P0（核心功能）/ P1（异常场景）/ P2（辅助功能）三级标记，支持按级别执行 |
| 并发执行 | pytest-xdist 多进程并行，回归测试时间缩短约 70% |
| 数据驱动 | Excel 管理测试用例，Jinja2 模板引擎支持变量引用，数据与代码分离 |
| CI/CD 集成 | 支持 Jenkins / GitHub Actions 自动拉取代码、执行测试、生成 Allure 报告 |

---

## 技术栈

| 组件 | 用途 | 版本要求 |
|------|------|---------|
| Python | 编程语言 | 3.8+ |
| pytest | 测试框架 | 7.4+ |
| requests | HTTP 客户端 | 2.31+ |
| allure-pytest | 测试报告 | 2.13+ |
| mysql-connector-python | 数据库断言 | 9.0+ |
| loguru | 日志输出 | 0.7+ |
| python-dotenv | 环境配置管理 | 1.0+ |
| openpyxl + jinja2 | Excel 数据驱动 | -- |
| pytest-xdist | 并发执行 | 3.5+ |
| pytest-rerunfailures | 失败重试 | 12.0+ |
| jsonpath | JSONPath 断言 | 0.82+ |
| Docker | 容器化部署 | 24+ |
| Docker Compose | 服务编排 | 2.24+ |

---

## 快速开始

### 1. 环境准备

```bash
git clone https://github.com/Mavie521/ruoyi-api-test.git
cd ruoyi_api_test

# 创建虚拟环境
python -m venv venv
source venv/Scripts/activate    # Windows
# source venv/bin/activate      # Mac / Linux

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
cp .env.example .env
```

根据你的环境修改 .env：

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

### 3. 运行测试

```bash
# P0 核心功能（18条，2分钟内跑完）
python run.py run -m p0

# 按环境运行
python run.py run --env=staging

# 并发执行（4 进程）
python run.py run -n 4

# 失败重试
python run.py run --reruns 2

# 生成报告
python run.py report
```

---

## 项目结构

```
ruoyi_api_test/
├── api/                           # API 封装层（POM 模式）
│   ├── base_api.py                # 基类：Session + Token 管理
│   ├── login_api.py               # 登录模块
│   ├── user_api.py                # 用户管理
│   ├── system_user_api.py         # 真实用户业务
│   └── role_api.py                # 角色管理
│
├── tests/                         # 测试用例层
│   ├── conftest.py                # pytest fixtures
│   ├── test_login.py              # 登录测试
│   ├── test_user.py               # 用户测试
│   ├── test_system_user.py        # 真实用户测试
│   └── test_role.py               # 角色测试
│
├── config/
│   └── config.py                  # 全局配置，多环境 .env 加载
│
├── utils/
│   ├── logger.py                  # 日志配置（loguru）
│   ├── assertions.py              # HTTP 响应断言器
│   ├── db_utils.py                # 数据库客户端 + 断言
│   └── allure_utils.py            # Allure 动态报告工具
│
├── docker/                        # Docker 部署文件
│   ├── compose.yml                # 服务编排（MySQL + Redis + RuoYi + 测试 + 报告）
│   ├── ruoyi/                     # RuoYi 后端镜像构建
│   ├── allure/                    # Allure 报告生成器镜像
│   └── nginx/                     # Nginx 配置文件
│
├── scripts/
│   ├── deploy.sh                  # 一键部署脚本
│   ├── test_and_report.sh         # 全流程测试 + 报告生成
│   └── download_sql.sh            # 数据库初始化脚本下载
│
├── .env                           # 环境变量（默认 dev）
├── conftest.py                    # 全局 conftest
├── run.py                         # 统一运行入口
└── Jenkinsfile                    # Jenkins 流水线脚本
```

---

## 架构设计

### 三层架构

```
┌──────────────────────────────────────────────┐
│              测试用例层（tests/）               │
│  test_login.py  test_user.py  test_role.py   │
│  验证业务逻辑、组合断言、异常场景               │
└──────────────────────┬───────────────────────┘
                       │ 继承
┌──────────────────────▼───────────────────────┐
│              API 对象层（api/）                │
│  LoginApi  RoleApi  UserApi  SystemUserApi   │
│  封装具体接口操作，每个方法对应一个 API         │
└──────────────────────┬───────────────────────┘
                       │ 继承
┌──────────────────────▼───────────────────────┐
│            基础设施层（api/base_api.py）        │
│  requests.Session 管理                        │
│  Token 自动注入                               │
│  统一 URL 拼接                                │
└──────────────────────┬───────────────────────┘
                       │ HTTP 请求
               ┌───────▼────────┐
               │   若依后端      │
               └────────────────┘
```

### 数据流

```
Pytest 发现用例
    │
    ▼
conftest.py fixture 初始化
    ├── admin_login（Session 级）--> 登录一次，自动保存 Token
    └── db（Session 级）       --> 连接数据库一次
    │
    ▼
API 对象接收 fixture 注入的 Token
    ├── 自动携带 Authorization: Bearer xxx
    ├── 自动拼接 base_url
    └── 发送 HTTP 请求
    │
    ▼
若依后端响应
    │
    ▼
双维度断言
    ├── 维度一：API 响应断言
    │   ├── 状态码检查（200/401/500）
    │   ├── code 字段检查
    │   └── msg / success 字段检查
    │
    └── 维度二：MySQL 数据库断言
        ├── assert_value()    --> 验证字段值
        ├── assert_exists()   --> 验证记录存在
        └── assert_not_exists() --> 验证记录已删除
    │
    ▼
Allure 报告输出
    ├── 自动 attach 请求报文
    ├── 自动 attach 响应报文
    ├── 失败时 attach 异常堆栈
    └── 失败分类（API 异常 / DB 断言 / 业务校验）
```

---

## Docker 部署

### 架构

```
Linux Server (Docker)
┌──────────────────────────────────────────────┐
│  docker compose up -d                        │
│                                              │
│  ┌──────────┐  ┌──────────┐  ┌────────────┐ │
│  │  MySQL   │  │  Redis   │  │ RuoYi 后端 │ │
│  │  3307    │  │  6379    │  │  8080      │ │
│  └────┬─────┘  └────┬─────┘  └─────┬──────┘ │
│       │             │              │        │
│       └──────┬──────┘              │        │
│         ┌────▼─────────────────────▼──┐     │
│         │    Test Runner (pytest)     │     │
│         └────────────┬────────────────┘     │
│                      │                     │
│         ┌────────────▼────────────┐        │
│         │  Allure Report (Nginx)  │        │
│         │  8088                   │        │
│         └─────────────────────────┘        │
└──────────────────────────────────────────────┘
```

### 一键部署

```bash
# 1. 克隆项目
git clone https://github.com/Mavie521/ruoyi-api-test.git
cd ruoyi_api_test

# 2. 执行一键部署（启动服务 + 运行测试 + 生成报告）
bash scripts/deploy.sh

# 3. 或分步执行
bash scripts/test_and_report.sh
```

### 快速启动

```bash
# 启动所有服务
docker compose up -d

# 运行测试
docker compose --profile test run --rm test-runner

# 生成 Allure 报告
docker compose --profile report run --rm allure-reporter

# 访问报告
# http://<server-ip>:8088
```

### 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| ENV | 运行环境 | docker |
| BASE_URL | RuoYi 后端地址 | http://ruoyi-api:8080 |
| DB_HOST | 数据库地址 | mysql |
| DB_PORT | 数据库端口 | 3306 |
| DB_NAME | 数据库名 | ry-vue |
| DB_USER | 数据库用户 | root |
| DB_PASSWORD | 数据库密码 | root |

---

## CI/CD 集成

### Jenkins 流水线

Jenkinsfile 支持两种运行模式：

| 模式 | 说明 | 适用场景 |
|------|------|---------|
| direct | 主机直接执行 pytest | 本地开发环境 |
| docker | 通过 docker compose 启动完整环境 | Linux 服务器 |

```groovy
pipeline {
    agent any
    parameters {
        choice(name: 'RUN_MODE', choices: ['direct', 'docker'])
        choice(name: 'ENV', choices: ['dev', 'staging', 'prod', 'docker'])
        string(name: 'MARKER', defaultValue: 'p0')
    }
    stages {
        stage('Checkout') {
            steps { git 'https://github.com/Mavie521/ruoyi-api-test.git' }
        }
        stage('Docker Deploy') {
            when { expression { params.RUN_MODE == 'docker' } }
            steps { sh 'docker compose up -d' }
        }
        stage('Test') {
            steps { sh 'pytest tests/ -m ${MARKER} --alluredir=./reports/allure-results' }
        }
        stage('Report') {
            steps { allure results: [[path: 'reports/allure-results']] }
        }
    }
}
```

### GitHub Actions

项目已集成 GitHub Actions，提交代码自动执行项目结构检查和模块导入验证。

---

## 代码示例

### BaseApi 基类

```python
class BaseApi:
    """所有 API 对象的基类，封装请求发送、token 管理、日志"""

    def __init__(self):
        self.session = requests.Session()
        self.base_url = BASE_URL.rstrip("/")
        self._token = None

    def set_token(self, token: str):
        """设置 token，后续所有请求自动携带 Authorization 头"""
        self._token = token
        self.session.headers.update({"Authorization": f"Bearer {token}"})

    def request(self, method: str, url: str, **kwargs) -> Response:
        if not url.startswith("http"):
            url = f"{self.base_url}{url}"
        kwargs.setdefault("timeout", DEFAULT_TIMEOUT)
        attach_request(method, url, headers=self.session.headers, **kwargs)
        res = self.session.request(method, url, **kwargs)
        attach_response(res)
        return res

    def get(self, url, **kwargs): return self.request("GET", url, **kwargs)
    def post(self, url, **kwargs): return self.request("POST", url, **kwargs)
    def put(self, url, **kwargs): return self.request("PUT", url, **kwargs)
    def delete(self, url, **kwargs): return self.request("DELETE", url, **kwargs)
```

### Fixture 共享机制

```python
@pytest.fixture(scope="session")
def admin_login() -> LoginApi:
    """Session 级 fixture，整个会话只登录一次"""
    api = LoginApi()
    token = api.login(ADMIN_USERNAME, ADMIN_PASSWORD)
    assert token, "管理员登录失败"
    return api

# 测试函数直接注入使用
def test_something(login_api, db):
    info = login_api.get_info()
    db.assert_value("SELECT ...", expected="xxx")
```

### 双维度断言

```python
# 维度一：API 响应验证
assert resp["code"] == 200

# 维度二：数据库落盘验证
db.assert_exists(
    "SELECT role_id FROM sys_role WHERE role_key=%s",
    params=(role_data["roleKey"],),
)
```

---

## 测试覆盖

| 模块 | 脚本测试 | 合计 | P0 | P1 | P2 |
|------|---------|------|----|----|----|
| 登录认证 | 6 | 6 | 3 | 3 | -- |
| 用户管理（真实） | 9 | 9 | 5 | 4 | -- |
| 用户管理（测试） | 7 | 7 | 5 | 2 | 1 |
| 角色管理 | 11 | 11 | 5 | 2 | 3 |
| **合计** | **34** | **34** | **18** | **12** | **4** |

### 执行策略

```
提交代码 -> P0（18 条，< 2min）-> 快速反馈
每日回归 -> P0 + P1（30 条） -> 全量验证
发版前   -> 全量 34 条        -> 最终确认
```

---

## 常见问题

### 如何切换环境？

```bash
# 方式一：环境变量
ENV=staging pytest tests/ -v

# 方式二：run.py 参数
python run.py run --env=staging
```

框架会加载对应的 .env.{env} 文件。支持 dev / staging / prod / docker 四种环境。

### 如何添加新接口的测试？

1. 在 api/ 下新建或扩展 API 对象（继承 BaseApi）
2. 在 tests/ 下新建 test_xxx.py
3. 在 conftest.py 添加对应的 fixture
4. 按用例级别添加 @pytest.mark.p0/p1/p2 标记

### 测试报 401 / 数据库断言失败？

检查 .env 中的账号密码和数据库连接配置是否正确，确认后端服务已启动。
