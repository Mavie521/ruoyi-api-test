# RuoYi API Test Framework

基于 **Pytest + Requests + Allure** 的接口自动化测试框架，覆盖若依管理系统（RuoYi）核心业务模块：登录认证、用户管理、角色管理。

---

## 目录

- [特性](#特性)
- [技术栈](#技术栈)
- [快速开始](#快速开始)
- [项目结构](#项目结构)
- [架构设计](#架构设计)
- [设计理念详解](#设计理念详解)
- [代码示例](#代码示例)
- [测试覆盖](#测试覆盖)
- [CI/CD 集成](#cicd-集成)
- [常见问题](#常见问题)

---

## 特性

### 核心能力

| 特性 | 说明 |
|------|------|
| **API 分层封装（POM）** | 参考 Page Object Model 思想，将每个业务模块的接口操作封装为独立 API 对象，消除重复代码 |
| **Token 自动管理** | 基于 pytest session 级 fixture，一次登录自动保存 token，后续请求自动携带 Authorization 头 |
| **双维度断言** | API 响应断言（code / msg / success）+ MySQL 数据库落盘断言，两个维度互相印证 |
| **Allure 动态报告** | 每个请求自动 attach 请求/响应/异常信息，失败原因按类别展示 |

### 企业级特性

| 特性 | 说明 |
|------|------|
| **失败自动重试** | 基于 pytest-rerunfailures，偶发超时/网络波动自动重试 2 次，间隔 5 秒，减少误报 |
| **多环境切换** | `--env=dev/staging/prod` 一键切换，不同环境加载对应 `.env.{env}` 配置 |
| **用例分级** | P0（核心功能）/ P1（异常场景）/ P2（辅助功能）三级标记，支持按级别执行 |
| **并发执行** | pytest-xdist 多进程并行，回归测试时间缩短约 70% |
| **数据驱动** | Excel 管理测试用例，Jinja2 模板引擎支持变量引用，数据与代码分离 |
| **CI/CD 集成** | 支持 Jenkins / GitHub Actions 自动拉取代码、执行测试、生成 Allure 报告 |

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
| openpyxl + jinja2 | Excel 数据驱动 | — |
| pytest-xdist | 并发执行 | 3.5+ |
| pytest-rerunfailures | 失败重试 | 12.0+ |
| jsonpath | JSONPath 断言 | 0.82+ |

---

## 快速开始

### 1. 环境准备

```bash
git clone https://github.com/Mavie521/ruoyi-api-test.git
cd ruoyi_api_test

# 创建虚拟环境（推荐）
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

创建 `.env` 文件（或从模板复制）：

```bash
cp .env.example .env
```

根据你的环境修改 `.env` 中的配置：

```ini
# 若依后端地址
BASE_URL=http://localhost:8080

# 管理员账号
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123

# MySQL 数据库配置（用于数据库断言）
DB_HOST=127.0.0.1
DB_PORT=3306
DB_NAME=ry-vue
DB_USER=root
DB_PASSWORD=123456
```

> `.env` 为默认配置文件，框架自动读取。切换环境请参考下方"多环境切换"。

### 3. 运行测试

```bash
# ---------- 按级别运行 ----------

# P0 核心功能（18条，2分钟内跑完）
pytest tests/ -m p0 -v

# 冒烟测试
pytest tests/ -m smoke -v

# 全量回归
pytest tests/ -v

# ---------- 按环境运行 ----------

# 默认环境（读取 .env）
pytest tests/ -v

# 指定环境（读取 .env.staging）
ENV=staging pytest tests/ -v

# ---------- 进阶用法 ----------

# 并发执行（4 进程）
pytest tests/ -n 4 -v

# 失败重试（失败用例自动重试 2 次）
pytest tests/ --reruns 2 --reruns-delay 5 -v

# 排除慢速用例
pytest tests/ -m "not slow" -v

# 按关键字过滤
pytest tests/ -k login -v

# ---------- 使用 run.py 入口 ----------

python run.py run                    # 运行 + 生成 Allure 报告
python run.py run -m p0              # 只跑 P0
python run.py run --env=staging      # 指定环境
python run.py run -n 4 --reruns 2    # 并发 + 重试
python run.py report                 # 仅生成报告（需安装 Allure CLI）
python run.py open                   # 打开报告
```

python run.py run
python run.py run --env=staging
python run.py run -m p0
python run.py run -n 4 --reruns 2
```

### 4. 查看报告

需要安装 Allure CLI，下载地址：[Allure Releases](https://github.com/allure-framework/allure2/releases)

```bash
# 生成并打开报告
allure generate ./reports/allure-results -o ./reports/allure-report --clean
allure open ./reports/allure-report

# 或使用 run.py
python run.py report
python run.py open
```

---

## 项目结构

```
ruoyi_api_test/
│
├── api/                           # ===== API 封装层（POM 模式） =====
│   ├── __init__.py                # 包入口，统一导出
│   ├── base_api.py                # 基类：requests.Session + Token 管理
│   ├── login_api.py               # 登录模块（LoginApi extends BaseApi）
│   ├── user_api.py                # 用户管理 - 测试控制器
│   ├── system_user_api.py         # 用户管理 - 真实业务
│   └── role_api.py                # 角色管理
│
├── tests/                         # ===== 测试用例层 =====
│   ├── conftest.py                # pytest fixtures（登录态/数据库/测试数据）
│   ├── test_login.py              # 登录测试（P0: 3, P1: 3）
│   ├── test_user.py               # 用户测试（P0: 5, P1: 2, P2: 1）
│   ├── test_system_user.py        # 真实用户测试（P0: 5, P1: 4）
│   └── test_role.py               # 角色测试（P0: 5, P1: 2, P2: 3）
│
├── config/                        # ===== 配置层 =====
│   └── config.py                  # 全局配置，支持多环境 .env 加载
│
├── utils/                         # ===== 工具层 =====
│   ├── logger.py                  # 日志配置（loguru，控制台+文件双输出）
│   ├── assertions.py              # HTTP 响应断言器
│   ├── db_utils.py                # 数据库客户端 + 断言
│   └── allure_utils.py            # Allure 动态报告工具
│
├── data/                          # 测试数据文件
├── reports/                       # 测试报告输出目录
├── logs/                          # 日志文件输出目录
│
├── .env                           # 环境变量（默认 dev 环境）
├── .env.staging                   # 预发布环境配置示例
├── .env.example                   # 环境变量模板
├── pytest.ini                     # pytest 配置
├── requirements.txt               # 项目依赖
├── conftest.py                    # 全局 conftest（Allure 环境 + 失败处理）
├── run.py                         # 统一运行入口
└── README.md                      # 项目文档
```

---

## 架构设计

### 三层架构

```
┌──────────────────────────────────────────────────────────┐
│                   测试用例层（tests/）                     │
│  test_login.py  test_user.py  test_role.py               │
│  验证业务逻辑、组合断言、异常场景                           │
└──────────────────────┬───────────────────────────────────┘
                       │ 继承
┌──────────────────────▼───────────────────────────────────┐
│                  API 对象层（api/）                        │
│  LoginApi  RoleApi  UserApi  SystemUserApi               │
│  封装具体接口操作，每个方法对应一个 API                     │
└──────────────────────┬───────────────────────────────────┘
                       │ 继承
┌──────────────────────▼───────────────────────────────────┐
│                 基础设施层（api/base_api.py）               │
│  requests.Session 管理                                    │
│  Token 自动注入                                           │
│  统一 URL 拼接                                             │
│  统一异常处理                                              │
└──────────────────────┬───────────────────────────────────┘
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
    ├── admin_login（Session 级）→ 登录一次，自动保存 Token
    └── db（Session 级）       → 连接数据库一次
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
    │   ├── code 字段检查（200 表示成功）
    │   └── msg / success 字段检查
    │
    └── 维度二：MySQL 数据库断言
        ├── assert_value()    → 验证字段值
        ├── assert_exists()   → 验证记录存在
        └── assert_not_exists() → 验证记录已删除
    │
    ▼
Allure 报告输出
    ├── 自动 attach 请求报文
    ├── 自动 attach 响应报文
    ├── 失败时 attach 异常堆栈
    └── 失败分类（API 异常 / DB 断言 / 业务校验）
```

---

## 设计理念详解

### 1. 为什么用 POM 模式？

POM（Page Object Model）原本是 UI 自动化的设计模式，核心思想是**将页面操作封装成对象**。我们将这一思想迁移到接口测试中：

**没有 POM 时（反例）：**

```python
# 每个测试用例直接发请求，代码大量重复
def test_login():
    res = requests.post("http://localhost:8080/login",
                        json={"username": "admin", "password": "admin123"})
    token = res.json().get("token")
    assert token is not None

def test_get_info():
    res = requests.post("http://localhost:8080/login", ...)  # 重复登录
    token = res.json().get("token")
    res2 = requests.get("http://localhost:8080/getInfo",
                        headers={"Authorization": f"Bearer {token}"})
    assert res2.json().get("code") == 200
```

**使用 POM 后：**

```python
# 登录逻辑只写一次，后续所有用例直接注入已登录的 API 对象
def test_get_info(login_api):
    resp = login_api.get_info()  # login_api 已经带好了 Token
    assert resp["code"] == 200
```

**核心收益：消除重复代码、统一变更入口、提高可维护性。**

### 2. 为什么需要双维度断言？

只验证 API 响应是不够的，看一个真实场景：

```
接口返回 {"code": 200, "msg": "操作成功"}
→ API 断言通过 ✅

但数据库没有写入（事务未提交 / 缓存未刷新 / 业务逻辑漏了）
→ 用户实际查不到数据 ❌
```

双维度断言解决这个问题：

```python
# 维度一：API 响应验证
assert resp["code"] == 200    # 接口返回成功

# 维度二：数据库落盘验证
db.assert_exists(
    "SELECT role_id FROM sys_role WHERE role_key=%s",
    params=(role_data["roleKey"],),
)                             # 数据真实写入数据库
```

**两个维度互相印证，覆盖"接口通了但数据没写"的漏测。**

### 3. Token 自动管理设计

```python
# 流程：
# 1. LoginApi.login() 调用后自动保存 token
# 2. conftest.py 中的 admin_login fixture 一次性完成登录
# 3. 其他 API 对象通过 admin_login.token 获取 token
# 4. set_token() 将 token 写入 Session 的 Authorization 头
# 5. 后续所有请求自动携带

# 为什么设计成 Session 级 fixture？
# - 整个测试会话只登录一次，节省时间
# - 所有测试类共享同一 token，避免重复认证
# - 如果 token 过期，只需修改 fixture，不用改用例
```

### 4. 失败分类设计

Allure 报告的 categories.json 将失败原因分为 4 类：

| 分类 | 匹配规则 | 处理方式 |
|------|---------|---------|
| API 请求异常 | ConnectionError / timeout / 500 / 404 | 检查网络/服务状态 |
| 数据库断言失败 | assert_value / SQL / DB | 检查数据一致性问题 |
| 业务校验失败 | assert / 断言 / code != 200 | 检查业务逻辑 |
| 其他异常 | 未匹配的异常 | 进一步分析 |

这样在报告中一眼就能看出**问题出在哪个层面**，不用逐个点开日志看。

---

## 代码示例

### BaseApi 基类

```python
# api/base_api.py
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
        """统一请求入口：自动拼接 URL + 自动 attach Allure"""
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

### LoginApi 继承示例

```python
# api/login_api.py
class LoginApi(BaseApi):

    def login(self, username: str = None, password: str = None) -> str:
        username = username or DEFAULT_USER
        password = password or DEFAULT_PWD
        body = {"username": username, "password": password}
        res = self.post("/login", json=body)
        token = res.json().get("token")
        if token:
            self.set_token(token)  # 自动保存 token
        return token
```

### 数据库断言工具

```python
# utils/db_utils.py
class DbClient:

    def query_one(self, sql: str, params: tuple = None) -> dict:
        rows = self.query(sql, params)
        return rows[0] if rows else None

    @allure.step("数据库断言: 值相等")
    def assert_value(self, sql: str, expected, params=None, column=None):
        result = self.query_one(sql, params)
        assert result is not None, f"查询无结果: {sql}"
        actual = result.get(column) if column else list(result.values())[0]
        assert actual == expected, f"预期 {expected}, 实际 {actual}"

    def assert_exists(self, sql: str, params=None):
        rows = self.query(sql, params)
        assert len(rows) >= 1, f"期望记录存在，未查到: {sql}"
```

### Fixture 共享机制

```python
# tests/conftest.py
@pytest.fixture(scope="session")
def admin_login() -> LoginApi:
    """Session 级 fixture，整个会话只登录一次"""
    api = LoginApi()
    token = api.login(ADMIN_USERNAME, ADMIN_PASSWORD)
    assert token, "管理员登录失败"
    return api

@pytest.fixture(scope="session")
def db():
    """Session 级 fixture，整个会话只连接一次数据库"""
    client = DbClient()
    yield client
    client.close()

# 测试函数直接注入使用
def test_something(login_api, db):
    info = login_api.get_info()
    db.assert_value("SELECT ...", expected="xxx")
```

---

## 测试覆盖

| 模块 | 脚本测试 | 数据驱动 | 合计 | P0 | P1 | P2 |
|------|---------|---------|------|----|----|----|
| 登录认证 | 6 | — | 6 | 3 | 3 | — |
| 用户管理（真实） | 9 | — | 9 | 5 | 4 | — |
| 用户管理（测试） | 7 | — | 7 | 5 | 2 | 1 |
| 角色管理 | 11 | — | 11 | 5 | 2 | 3 |
| 全流程业务 | 1 | — | 1 | — | 1 | — |
| **合计** | **34** | **—** | **34** | **18** | **12** | **4** |

### 执行策略

```
提交代码 → P0（18 条，< 2min）→ 快速反馈 ✅
每日回归 → P0 + P1（29 条） → 全量验证 ✅
发版前  → 全量 33 条 → 最终确认 ✅
```

---

## CI/CD 集成

### Jenkins 流水线（推荐）

```groovy
pipeline {
    agent any
    stages {
        stage('Checkout') {
            steps { git 'https://github.com/Mavie521/ruoyi-api-test.git' }
        }
        stage('Install') {
            steps { sh 'pip install -r requirements.txt' }
        }
        stage('Test') {
            steps { sh 'pytest tests/ -m p0 --alluredir=./reports/allure-results' }
        }
        stage('Report') {
            steps { allure includeProperties: true, results: [[path: './reports/allure-results']] }
        }
    }
}
```

### GitHub Actions

```yaml
name: API Test
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - name: Install
        run: pip install -r requirements.txt
      - name: Run P0
        run: pytest tests/ -m p0 -v --alluredir=./allure-results
      - name: Generate report
        uses: simple-elf/allure-report-action@v1
        if: always()
        with:
          allure_results: ./allure-results
```

---

## 常见问题

### 测试报 401 怎么办？

检查 `.env` 中的账号密码是否正确，或后端是否已启动。

### 数据库断言失败？

确认数据库连接信息正确，且表结构匹配。

### 如何切换环境？

框架支持多环境，通过 `ENV` 环境变量或 `--env` 参数切换：

```bash
# 方式一：环境变量
ENV=staging pytest tests/ -v

# 方式二：run.py 参数
python run.py run --env=staging
```

框架会加载对应的 `.env.{env}` 文件（如 `ENV=staging` 时加载 `.env.staging`）。
不指定环境时默认读取 `.env`。

### 配置文件有哪些？

| 文件 | 用途 |
|------|------|
| `.env` | 默认配置，框架自动读取 |
| `.env.staging` | 预发布环境配置，`ENV=staging` 时读取 |
| `.env.example` | 配置模板，包含所有字段的占位符说明 |

### 如何添加新接口的测试？

1. 在 `api/` 下新建或扩展 API 对象（继承 BaseApi）
2. 在 `tests/` 下新建 `test_xxx.py`
3. 如果需要登录态，在 conftest.py 添加对应的 fixture
4. 按用例级别添加 `@pytest.mark.p0/p1/p2` 标记

### 如何切换运行环境？

```bash
# 方式一：命令行参数
pytest tests/ --env=staging -v

# 方式二：环境变量
ENV=staging pytest tests/ -v

# 方式三：run.py 入口
python run.py run --env=staging
```

---

## 后续计划

- [x] 失败自动重试（pytest-rerunfailures）
- [x] 多环境切换（--env 参数）
- [x] 用例分级（P0/P1/P2）
- [ ] Docker 容器化部署 RuoYi 项目
- [ ] Jenkins 流水线自动触发 + Allure 报告推送
- [ ] 钉钉/飞书失败通知
- [ ] 接口 Schema 校验（pydantic/jsonschema）
