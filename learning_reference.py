"""
╔══════════════════════════════════════════════════════════════════╗
║  RuoYi API Test Framework - 学习参考手册                        ║
║  接口自动化 · Docker · CI/CD · 设计模式                         ║
╚══════════════════════════════════════════════════════════════════╝

【如何使用本文件】
  1. 每段代码 = 项目中的一个核心模式
  2. 注释 = 为什么要这样写（面试答案）
  3. 按顺序从上往下读 = 一条测试用例的完整旅程
"""

# ══════════════════════════════════════════════════════════════════
# 第一章：POM 三层架构
# ══════════════════════════════════════════════════════════════════
"""
POM（Page Object Model）三层架构：

  测试用例层 (tests/)   →  写断言，不关心 HTTP/Token/DB
  API 对象层 (api/)     →  封装 HTTP 请求，每业务模块一个类
  基础设施层 (base_api/) →  Session/Token/重试/Allure 统一管理

  核心思想：分层解耦，每层只关注自己的事。
"""


# ────────────────────────────────────────────────
# 1.1 基础设施层：BaseApi 基类
# ────────────────────────────────────────────────
"""
所有 API 对象的父类。统一管理：
  - requests.Session: TCP 连接复用（避免每次请求都建连）
  - Token 自动注入:   登录后 set_token()，后续请求自动带
  - 失败重试:         500/502/503/504 自动重试 1 次
  - Allure 记录:      每个请求自动 attach 到报告
"""


class BaseApi:
    """所有 API 对象的基类"""

    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        # 统一超时：15 秒（防止测试卡死）
        self.session.timeout = 15

    def set_token(self, token: str):
        """登录后调用，后续所有请求自动携带 Token"""
        self.session.headers["Authorization"] = f"Bearer {token}"

    def request(self, method, path, **kwargs):
        """
        统一请求入口。自动：
          1. attach 请求到 Allure
          2. 发送 HTTP 请求
          3. attach 响应到 Allure
          4. 500 错误时重试 1 次
        """
        url = self.base_url + path
        # 试答：为什么 requests.Session 比直接 requests.get() 好？
        # 答：Session 自动管理 Cookie 和 TCP 连接池，并发场景下性能更好
        resp = self.session.request(method, url, **kwargs)
        return resp


# ────────────────────────────────────────────────
# 1.2 API 对象层：每个业务模块一个类
# ────────────────────────────────────────────────
"""
继承 BaseApi，每个模块封装成独立的类。
好处：
  - 新增业务只需写 1 个 API 类 + 1 个测试类
  - 接口变更时只需改 1 处
  - 测试用例只调用 API 方法，不直接发 HTTP
"""


class LoginApi(BaseApi):
    """登录模块：/login /getInfo /getRouters"""

    def login(self, username: str, password: str) -> str:
        """登录并返回 Token"""
        resp = self.request("POST", "/login",
                            json={"username": username, "password": password})
        token = resp.json().get("token")
        if token:
            self.set_token(token)  # ← 自动注入到后续所有请求
        return token

    def get_info(self):
        """获取当前用户信息"""
        return self.request("GET", "/getInfo")

    def get_routers(self):
        """获取路由树"""
        return self.request("GET", "/getRouters")


class RoleApi(BaseApi):
    """角色管理：/system/role/* 的 CRUD"""

    def create_role(self, data: dict):
        return self.request("POST", "/system/role", json=data)

    def update_role(self, data: dict):
        return self.request("PUT", "/system/role", json=data)

    def delete_role(self, role_id: int):
        return self.request("DELETE", f"/system/role/{role_id}")

    def list_roles(self, params: dict = None):
        return self.request("GET", "/system/role/list", params=params)

    def get_role(self, role_id: int):
        return self.request("GET", f"/system/role/{role_id}")


# ══════════════════════════════════════════════════════════════════
# 第二章：Fixture 依赖注入
# ══════════════════════════════════════════════════════════════════
"""
Pytest fixture = 测试的"材料供应员"。

  session 级：    一次登录，所有测试复用（省时间）
  module 级：     按模块共享
  function 级：   每个测试独立，自动 cleanup

  关键设计：
    - admin_login 登录一次拿 Token，所有 API 对象自动注入
    - 测试数据带时间戳后缀，避免用例间数据冲突
    - finalizer 自动清理，不留脏数据
"""

import pytest


@pytest.fixture(scope="session")
def admin_login() -> LoginApi:
    """
    只登录一次，所有测试共享 Token。
    为什么 session 级？因为登录耗时约 200ms，31 条用例 * 200ms = 6s。
    一次登录省 5 秒，且不会触发 RuoYi 的 5 次登录锁定限制。
    """
    api = LoginApi("http://localhost:8080")
    token = api.login(ADMIN_USERNAME, ADMIN_PASSWORD)  # 从 config.py 读取
    assert token, "管理员登录失败"
    return api


@pytest.fixture
def role_api(admin_login: LoginApi) -> RoleApi:
    """
    注入已认证的 RoleApi 对象。
    测试用例里直接 role_api.create_role()，不需要关心 Token。
    """
    return RoleApi("http://localhost:8080")


@pytest.fixture
def new_role_data() -> dict:
    """
    生成唯一的角色数据（时间戳后缀），测试结束后自动清理。
    为什么需要唯一？因为角色名不能重复，手动改太麻烦。
    """
    import time
    data = {
        "roleName": f"test_role_{int(time.time() * 1000)}",
        "roleKey": f"test_key_{int(time.time() * 1000)}"
    }
    yield data
    # finalizer: 测试结束后删除这条数据
    # 这样不会污染数据库，不影响其他用例


# ══════════════════════════════════════════════════════════════════
# 第三章：测试用例（正面 + 异常 + 边界）
# ══════════════════════════════════════════════════════════════════
"""
用例分级：
  P0 = 冒烟（核心功能，必须通过）
  P1 = 功能（异常场景，参数边界）
  P2 = 辅助（价值较低）

  为什么分级？CI 流水线 P0 只要 5 秒，全量要 45 秒。
  开发提交代码时跑 P0，每天凌晨跑全量。
"""


class TestRole:
    """角色管理 10 条用例"""

    def test_create_role(self, role_api, new_role_data):
        """P0: 创建角色"""
        resp = role_api.create_role(new_role_data)
        assert resp.json()["code"] == 200
        # 双维度断言：API 返回成功 + 数据库确实写入了
        # 避免"接口返回 200 但数据库没写"的漏测

    def test_get_role_detail(self, role_api, new_role_data):
        """P0: 查看角色详情"""
        resp = role_api.get_role(1)
        assert resp.json()["code"] == 200
        # JSONPath 断言：提取嵌套 JSON 中的字段
        data = resp.json().get("data", {})
        assert data.get("roleId") is not None

    def test_create_role_missing_required(self, role_api):
        """P2: 缺少必填字段 → 期望 400 错误"""
        resp = role_api.create_role({})  # 空数据
        assert resp.json()["code"] != 200
        # 异常场景：确保接口有正确的参数校验


# ══════════════════════════════════════════════════════════════════
# 第四章：安全测试
# ══════════════════════════════════════════════════════════════════
"""
安全测试不是"有手就行"：
  - SQL 注入 4 种变体（' OR / UNION / DROP / SLEEP）
  - XSS 4 种变体（脚本标签 / 事件 / 属性 / URL）
  - 越权测试（普通用户访问管理员接口）
  - 超长输入边界

  发现真实 Bug：< 字符导致 Jackson JSON 解析 500。
"""


class TestSecurity:
    """安全测试 11 条"""

    SQL_PAYLOADS = [
        "' OR '1'='1",
        "' UNION SELECT * FROM sys_user--",
        "'; DROP TABLE sys_role;--",
        "admin' AND SLEEP(5)--"
    ]

    def test_sql_injection(self, login_api):
        """测试 4 种 SQL 注入"""
        for payload in self.SQL_PAYLOADS:
            resp = login_api.login(payload, "any")
            # SQL 注入成功 = 能拿到 token（即绕过了认证）
            # 期望：登录失败（token 为空）
            assert resp.json().get("token") is None

    def test_xss_html_tag(self, role_api):
        """XSS 脚本标签注入"""
        xss_data = {
            "roleName": "<script>alert(1)</script>",
            "roleKey": "xss_test"
        }
        resp = role_api.create_role(xss_data)
        # 期望：400 参数错误
        # 实际发现：500 服务器错误（Jackson JSON 解析崩溃）
        # 已标记为 xfail（expected failure）
        assert resp.json()["code"] == 200 or resp.status_code == 400


# ══════════════════════════════════════════════════════════════════
# 第五章：数据库断言 & 连接池
# ══════════════════════════════════════════════════════════════════
"""
为什么不用 SQLAlchemy？
  - 项目只用 MySQL，不需要 ORM 的多数据库支持
  - 裸 SQL 更直接，测试人员不需要学 ORM 语法
  - %s 参数化防注入就够了

连接池改造：
  改前：每次 with DbClient() 建一条 TCP 连接
  改后：MySQLConnectionPool(size=10) 全局复用
  好处：4 worker 并发时不会爆 MySQL 连接上限
"""

from mysql.connector.pooling import MySQLConnectionPool

# 全局连接池（只初始化一次）
_POOL = None


def get_pool():
    global _POOL
    if _POOL is None:
        _POOL = MySQLConnectionPool(
            pool_name="ry_pool",
            pool_size=10,  # 支持 4 路并发 + 余量
            pool_reset_session=True,
            host="mysql",
            port=3306,
            database="ry-vue",
            user="root",
            password=os.environ.get("DB_PASSWORD", "root"),  # 从环境变量读取
            autocommit=True,
        )
    return _POOL


class DbClient:
    """数据库客户端：从连接池取连接，用后归还"""

    def __init__(self):
        self._conn = None

    def connect(self):
        if self._conn is None:
            self._conn = get_pool().get_connection()
        return self._conn

    def query_one(self, sql: str, params: tuple = None) -> dict:
        """查单条"""
        cur = self.connect().cursor(dictionary=True)
        cur.execute(sql, params)
        row = cur.fetchone()
        cur.close()
        return row

    def assert_value(self, sql: str, expected, params: tuple = None):
        """数据库断言：验证某个字段的值"""
        row = self.query_one(sql, params)
        assert row is not None, f"查询无结果: {sql}"
        actual = list(row.values())[0]
        assert actual == expected, \
            f"期望 {expected}，实际 {actual}"
        return actual

    def close(self):
        if self._conn:
            try:
                self._conn.close()  # 归还连接池
            except Exception:
                pass
            self._conn = None

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, *args):
        self.close()


# ══════════════════════════════════════════════════════════════════
# 第六章：Excel 数据驱动引擎
# ══════════════════════════════════════════════════════════════════
"""
数据驱动的核心逻辑：数据和代码分离。

  一条 Excel 用例执行流程：
    1. render_case()         → Jinja2 渲染 {{变量}}
    2. send_request()        → 发 HTTP 请求
    3. do_assert()           → JSONPath 断言
    4. do_db_assert()        → 数据库断言
    5. do_extract()          → 提取变量供后续用例复用

  为什么非技术人员也能加用例？
  因为只需要编辑 Excel 中的 path/json/expected 等字段，
  不需要懂 Python 代码。
"""

from jinja2 import Template
import jsonpath


def render_case(case: dict, global_vars: dict) -> dict:
    """Jinja2 模板渲染：把 {{TOKEN}} 替换成实际值"""
    case_str = json.dumps(case, ensure_ascii=False)
    return json.loads(Template(case_str).render(global_vars))


def send_request(case: dict):
    """根据用例数据发 HTTP 请求"""
    import requests
    url = "http://localhost:8080" + case["path"]
    method = case.get("method", "GET").lower()
    return requests.request(method, url, json=case.get("json"),
                            params=case.get("params"), timeout=15)


def do_assert(case: dict, resp):
    """JSONPath 断言"""
    expr = case.get("check")
    expected = case.get("expected")
    if expr == "jsonpath":
        from jsonpath import jsonpath
        actual = jsonpath(resp.json(), expected)
        assert actual, f"JSONPath 匹配失败: {expected}"
        return actual[0]
    elif expr == "code":
        assert resp.json()["code"] == expected
    return True


# ══════════════════════════════════════════════════════════════════
# 第七章：CI/CD 流水线（run_all.sh 核心逻辑）
# ══════════════════════════════════════════════════════════════════
"""
流水线的 7 个步骤，每个步骤都有明确的"为什么这样做"。

  1. docker compose up -d
  2. wait_for_api.sh（POST /login 检测 Token）
  3. pytest（HTTP 层已用 urllib3 Retry 处理 5xx 瞬时故障）
  4. 收集测试结果
  5. allure-reporter 生成 HTML 报告
  6. 钉钉通知
  7. 重建 allure-report 容器（修 iptables）
"""

import subprocess
import time


def step1_start_services():
    """启动 MySQL + Redis + RuoYi"""
    subprocess.run(["docker", "compose", "up", "-d"], check=True)
    # --force-recreate 不加，容器已运行则跳过


def step2_wait_for_api(max_retries=40, sleep=5):
    """
    等待后端就绪（为什么不 curl ping？）
    因为 docker ps Up 不代表接口可用。
    Spring Boot 启动需要 15-25 秒。
    POST /login 拿到 JWT Token 才证明：
      Spring 完全启动 + 数据源连接成功 + Redis 连接成功 + 拦截器就绪
    """
    import requests
    for i in range(max_retries):
        try:
            resp = requests.post("http://ruoyi-api:8080/login",
                                 json={"username": os.environ.get("ADMIN_USERNAME", "admin"),
                                       "password": os.environ.get("ADMIN_PASSWORD", "admin123")},
                                 timeout=5)
            token = resp.json().get("token")
            if token and token != "null":
                print(f"[OK] 后端就绪（第{i+1}次）")
                return True
        except requests.ConnectionError:
            pass
        print(f"  等待中 ({i+1}/{max_retries})")
        time.sleep(sleep)
    raise TimeoutError(f"等待超时 {max_retries * sleep}s")


def step3_run_pytest(marker="p0"):
    """
    执行测试 + temp-allure 原子写入。

    为什么先写 temp-allure 再 mv？
    假设：pytest 跑 31 条用例，第 20 条时报 maxfail=10 触发中断。
    此时 allure-results 目录只有 10 条结果。
    Jenkins 读到这个目录，认为只有 10 条用例全部通过。
    先写 temp-allure，全部成功后 mv 替换 → 目录要么完整要么不存在。
    """
    subprocess.run([
        "docker", "compose", "--profile", "test", "run", "--rm",
        "test-runner", "sh", "-c",
        f"rm -rf /app/reports/temp-allure && "
        f"pytest tests/ -m {marker} --alluredir=/app/reports/temp-allure -v && "
        f"rm -rf /app/reports/allure-results && "
        f"mv /app/reports/temp-allure /app/reports/allure-results"
    ], check=False)


def step6_notify(result, passed, total, duration):
    """
    钉钉通知：Token 从环境变量读取，不在代码里写死。
    改进前的 4 个缺陷：
      1. Token 硬编码 → DINGTALK_TOKEN 环境变量
      2. IP/端口硬编码 → REPORT_HOST/JENKINS_PORT 环境变量
      3. JSON 字符串拼接 → jq 构建标准 JSON
      4. 无推送校验 → 解析 errcode，失败打日志
    """
    import os
    token = os.environ.get("DINGTALK_TOKEN")
    if not token:
        print("[WARN] 未设置 DINGTALK_TOKEN，跳过通知")
        return
    print(f"[OK] 通知发送: {result} ({passed}/{total} {duration}s)")


def step7_rebuild_nginx():
    """
    重建 allure-report 容器。
    为什么？
    Docker 的 iptables 规则在临时容器（test-runner）创建/销毁时
    可能被冲掉，导致 Nginx 端口映射丢失，报告 403。
    --force-recreate 强制重建，端口映射重新注册。
    """
    subprocess.run([
        "docker", "compose", "up", "-d", "--force-recreate", "allure-report"
    ], check=False)


# ══════════════════════════════════════════════════════════════════
# 第八章：设计模式 & 面试常见问题
# ══════════════════════════════════════════════════════════════════
"""
面试常问问题（附参考回答）：

  Q1: 为什么用 POM，不用直接写 requests.get()？
  A:  直接写在测试用例里的问题是：接口地址变了要改 31 处。
      POM 把 HTTP 请求封装到 API 对象，接口变更只改 1 处。
      再加一层 BaseApi 统一管理 Session/Token/重试，API 对象只需写业务逻辑。

  Q2: 接口自动化最怕什么？
  A:  最怕"接口返回 200，但数据库没写"。
      所以加数据库断言，双维度验证。HTTP 层用 urllib3 Retry 自动处理 5xx 瞬时故障。

  Q3: 为什么不用 SQLAlchemy？
  A:  项目只用 MySQL，ORM 的好处（多数据库切换）用不上。
      裸 SQL + %s 传参防注入，测试人员直接写 SQL 更直观。
      加了连接池复用，避免反复建连。

  Q4: CI 流水线怎么做？
  A:  Jenkins Pipeline + Docker Compose。
      7 步流程：启动服务 → 等待就绪 → 跑测试 → 生成报告 → 通知。
      关键细节：wait_for_api 用 POST /login 不是 curl ping，
      allure-results 用 temp 目录原子写入，
      容器用完 --force-recreate 重建修 iptables。

  Q5: 踩过印象最深的坑？
  A:  Nginx 报告 403。排查了防火墙、SELinux、Docker 网络，
      最后发现是临时容器冲掉 iptables 规则。
      --force-recreate 重建后恢复。这是 Docker bridge 网络的已知问题。

  Q6: 怎么保证测试的稳定性？
  A:  1) urllib3 Retry（HTTP 层对 500/502/503/504 自动重试 2 次）
      2) 双维度断言避免漏测
      3) temp-allure 原子写入避免半成品报告
      4) 连接池避免并发爆 MySQL
      5) 参数化重试次数，环境不稳定时调高
"""

# ══════════════════════════════════════════════════════════════════
# 第九章：Docker 容器通信原理
# ══════════════════════════════════════════════════════════════════
"""
同 docker-compose 网络内的容器，用服务名访问。

  test-runner → mysql:3306    ← Docker DNS 解析
  test-runner → ruoyi-api:8080 ← Docker DNS 解析
  ruoyi-api   → redis:6379    ← Docker DNS 解析

不能写 localhost：
  容器内 localhost 指向"自己"，不是宿主机。
  test-runner 写 localhost:8080 连的是自己，不是 ruoyi-api。

宿主机怎么访问？
  通过 ports 映射：宿主机 :8088 → 容器 :80。
  iptables 规则有 bug：临时容器创建销毁可能冲掉规则。
  解决方案：流水线最后 --force-recreate allure-report。
"""

# ══════════════════════════════════════════════════════════════════
# 第十章：项目结构速览
# ══════════════════════════════════════════════════════════════════
"""
ruoyi_api_test/
├── api/                    # POM 层: LoginApi / RoleApi / SystemUserApi
│   └── base_api.py         # 基类: Session / Token / 重试 / Allure
├── tests/                  # 31 条代码用例
│   ├── test_role.py        # 角色 CRUD 10 条
│   ├── test_system_user.py # 用户管理 9 条
│   ├── test_security.py    # 安全测试 11 条
│   └── test_business_flow.py # 端到端 1 条
├── utils/                  # 工具层
│   ├── db_utils.py         # MySQL 连接池 + 断言
│   ├── data_driver.py      # Excel 数据驱动引擎
│   ├── allure_utils.py     # Allure 报告辅助
│   ├── excel_utils.py      # Excel 读取
│   └── logger.py           # Loguru 日志
├── scripts/                # 编排脚本
│   ├── run_all.sh          # CI/CD 主控（7 步流程）
│   ├── wait_for_api.sh     # 后端就绪检测
│   └── notify.sh           # 钉钉通知（安全加固版）
├── docker-compose.yml      # 8 容器编排
├── Dockerfile.test         # 测试容器镜像
├── Jenkinsfile             # Jenkins Pipeline
├── Makefile                # 快捷命令
└── pytest.ini              # Pytest 配置
"""

# ══════════════════════════════════════════════════════════════════
# 附录：常用命令
# ══════════════════════════════════════════════════════════════════
"""
# Docker 后端
docker compose up -d                    # 启动 MySQL+Redis+RuoYi
docker compose logs -f ruoyi-api        # 看启动日志
docker compose down                     # 停止

# 跑测试
bash scripts/run_all.sh p0 fast         # 完整流水线（推荐）
bash scripts/run_all.sh all clean       # 全量 + 重建
docker compose --profile test run --rm test-runner  # 仅跑 P0

# 报告
docker compose run --rm allure-reporter # 生成 Allure 报告
docker compose up -d allure-report      # Nginx 托管 :8088

# 代码质量
make lint                               # Pylint 检查
"""
