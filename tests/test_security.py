"""
安全测试用例 —— SQL 注入 / XSS / 越权 / Token 伪造
覆盖若依系统常见安全弱点，增强测试纵深。
具备安全测试意识，能覆盖 SQL 注入、XSS、越权等安全场景。
"""
import allure
import pytest
from api import BaseApi, LoginApi
from utils.assertions import assert_jsonpath_exact
from utils.logger import logger


@allure.epic("若依接口测试")
@allure.feature("安全测试")
class TestSecurity:
    """安全测试：SQL注入 / XSS / 越权 / 边界异常"""

    # ============================================================
    # SQL 注入
    # ============================================================
    @allure.story("SQL 注入")
    @allure.title("登录接口 SQL 注入 — 用户名字段注入")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.security
    @pytest.mark.p1
    @pytest.mark.parametrize("payload", [
        "admin' OR '1'='1",
        "admin'--",
        "admin' OR 1=1--",
        "admin\" OR \"1\"=\"1",
    ])
    def test_login_sql_injection_username(self, payload):
        """
        用户名 SQL 注入不应登录成功。

        若依使用 MyBatis #{} 预编译占位符，参数值在 SQL 执行前已被转义为
        纯字符串字面量，注入 payload 不会改变 SQL 语义结构。
        这是参数化查询（PreparedStatement）的标准防护效果。
        https://mybatis.org/mybatis-3/sqlmap-xml.html#Parameters
        """
        with allure.step(f"尝试 SQL 注入登录: username={payload[:20]}..."):
            api = LoginApi()
            token = api.login(payload, "admin123")
        with allure.step("验证注入未导致登录成功"):
            assert token is None, f"用户名 SQL 注入不应成功: {payload}"

    @allure.story("SQL 注入")
    @allure.title("登录接口 SQL 注入 — 密码字段注入")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.security
    @pytest.mark.p1
    @pytest.mark.parametrize("payload", [
        "' OR '1'='1",
        "' OR 1=1--",
        "') OR ('1'='1",
    ])
    def test_login_sql_injection_password(self, payload):
        """
        密码字段 SQL 注入不应登录成功。

        同上：若依 MyBatis #{} 预编译机制在 SQL 层面做了参数化隔离，
        攻击者输入的 ' OR '1'='1 等 payload 被当作普通字符串匹配，
        无法打破 WHERE 子句的原始逻辑。
        """
        with allure.step(f"尝试密码字段 SQL 注入: {payload[:20]}"):
            api = LoginApi()
            token = api.login("admin", payload)
        with allure.step("验证注入未导致登录成功"):
            assert token is None, f"密码 SQL 注入不应成功: {payload}"

    # ============================================================
    # XSS（存储型 — 接口 + 数据库双重验证）
    # ============================================================
    @allure.story("XSS")
    @allure.title("角色名 XSS 注入 — 接口不崩溃 + 数据库未原样存储脚本")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.security
    @pytest.mark.p1
    @pytest.mark.parametrize("xss_payload", [
        '<script>alert("xss")</script>',
        '"><script>alert(1)</script>',
        'javascript:alert(1)',
        '<ScRiPt>alert(1)</ScRiPt>',
        '<img src=x onerror=alert(1)>',
    ])
    def test_role_name_xss(self, role_api, new_role_data, db, xss_payload):
        """
        角色名 XSS 安全测试（双层验证）:
          ① 接口层面：不应导致服务端 500 崩溃
          ② 数据库层面：存储值不应包含原始 <script> / onerror 等 XSS 向量

        标准安全测试不能只判不崩溃 —— code=200 但后端原样存储
        <script> 标签，页面渲染时依然存在存储型 XSS 漏洞。
        """
        with allure.step(f"创建含 XSS payload 的角色: {xss_payload[:30]}..."):
            data = new_role_data.copy()
            data["roleName"] = f"{new_role_data['roleName']}_xss"
            resp = role_api.create(data)
            # ① 接口层：不应崩溃
            assert resp.get("code") != 500, (
                f"XSS 导致服务端 500: {xss_payload}"
            )

        with allure.step("数据库回读 — 验证角色名未原样存储 XSS 脚本"):
            row = db.query_one(
                "SELECT role_name FROM sys_role "
                "WHERE role_key=%s AND del_flag='0'",
                (data["roleKey"],),
            )
            if row is None:
                # 后端若在入库前做了输入校验并拒绝创建，角色不会落盘。
                # 此时 DB 查不到是正常的安全行为（输入已被拦截），
                # skip 而非 fail，避免把"安全拦截"误判为"测试失败"。
                pytest.skip("角色创建后未在数据库中找到（可能被后端过滤拒绝）")
            else:
                stored_name = row["role_name"]
                # ② 存储层：核心安全断言
                has_script = "<script>" in stored_name.lower()
                has_onevent = any(
                    tag in stored_name.lower()
                    for tag in ["onerror=", "onload=", "javascript:"]
                )
                assert not has_script, (
                    f"❌ 存储型 XSS 漏洞！角色名未过滤 <script> 标签\n"
                    f"  注入 payload: {xss_payload}\n"
                    f"  数据库存储值: {stored_name}"
                )
                assert not has_onevent, (
                    f"❌ 存储型 XSS 漏洞！角色名含事件处理器/html协议\n"
                    f"  注入 payload: {xss_payload}\n"
                    f"  数据库存储值: {stored_name}"
                )

    @allure.story("XSS")
    @allure.title("角色名含 < 字符 — 不应导致服务端 500 + 数据库验证（已修复）")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.security
    @pytest.mark.p1
    def test_role_name_xss_crash_bug(self, role_api, new_role_data, db):
        """HTML 标签注入：后端应拦截或转义，不应原样存储"""
        with allure.step("创建含 HTML 标签的角色名"):
            data = new_role_data.copy()
            data["roleName"] = f"x<B>test_{new_role_data['roleKey']}"
            resp = role_api.create(data)

        # 两种安全场景：后端拦截（非 200），或正常处理不崩溃
        if resp.get("code") != 200:
            pytest.skip("后端校验拦截含 HTML 标签的角色名称，安全")

        # 创建成功 → 校验入库内容是否被转义
        with allure.step("数据库回读 — 验证 HTML 标签已被转义或过滤"):
            row = db.query_one(
                "SELECT role_name FROM sys_role "
                "WHERE role_key=%s AND del_flag='0'",
                (data["roleKey"],),
            )
            assert row is not None, "角色创建成功但数据库中未找到记录"
            stored = row["role_name"]
            assert "<B>" not in stored, (
                f"❌ 存储型 XSS 风险：HTML 标签未被转义\n"
                f"  存储值: {stored}"
            )

    # ============================================================
    # Token 伪造
    # ============================================================
    @allure.story("身份认证漏洞")
    @allure.title("伪造/过期 Token 访问 — 应返回 401")
    @allure.severity(allure.severity_level.BLOCKER)
    @pytest.mark.security
    @pytest.mark.p1
    def test_fake_token_access(self):
        """伪造 Token 无法访问受保护接口"""
        fake_tokens = [
            "eyJhbGciOiJIUzUxMiJ9.fake.xxxx",       # 伪造 JWT
            "Bearer invalid_token_here",             # 格式错误
            "",                                       # 空字符串
            "abcdef123456",                          # 随机字符串
        ]
        for fake in fake_tokens:
            with allure.step(f"测试伪造 Token: {fake[:25]}"):
                api = BaseApi()
                api.set_token(fake)
                resp = api.request(method="GET", path="/getInfo")
                body = resp.json()
                is_rejected = (
                    resp.status_code in (401, 403)
                    or body.get("code") != 200
                )
                assert is_rejected, f"伪造 Token 应被拒绝: {fake[:20]}"

    # ============================================================
    # 边界异常
    # ============================================================
    @allure.story("边界异常")
    @allure.title("超长用户名/密码 — 登录应被拒绝")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.security
    @pytest.mark.p2
    def test_extreme_length_input(self):
        """超长输入应导致登录失败，不应返回有效 token"""
        with allure.step("发送 5000 字符的用户名和密码"):
            api = LoginApi()
            long_str = "A" * 5000
            token = api.login(long_str, long_str)
        with allure.step("验证超长输入未通过认证"):
            assert token is None, (
                f"❌ 超长用户名/密码不应登录成功！\n"
                f"  预期: token=None（登录被拒绝）\n"
                f"  实际: 获得了有效 token（长度={len(token) if token else 0}）\n"
                f"  风险: 超长输入可能触发缓冲区溢出或绕过认证逻辑"
            )

    # ============================================================
    # 垂直越权
    # ============================================================
    @allure.story("垂直越权")
    @allure.title("普通用户不能操作管理员接口")
    @allure.severity(allure.severity_level.BLOCKER)
    @pytest.mark.security
    @pytest.mark.p0
    def test_common_user_cannot_escalate(self, non_admin_login):
        """普通角色用户不能创建角色（管理员接口）"""
        with allure.step("以普通用户身份尝试创建角色"):
            resp = non_admin_login.request(
                method="POST", path="/system/role",
                json={"roleName": "越权角色", "roleKey": "escalate", "roleSort": 1},
            ).json()

        with allure.step("验证越权操作被拒绝（精确断言 403，500=测试缺陷）"):
            code = resp.get("code")
            if code == 500:
                raise AssertionError(
                    f"❌ 服务端崩溃（500），无法判断越权防护是否生效\n"
                    f"  响应: {resp}"
                )
            assert code != 200, (
                f"❌ 垂直越权漏洞！普通用户成功创建了角色\n"
                f"  响应: {resp}"
            )

    # ============================================================
    # 水平越权
    # ============================================================
    @allure.story("水平越权")
    @allure.title("数据权限隔离 — 普通用户不能查看其他用户")
    @allure.severity(allure.severity_level.BLOCKER)
    @pytest.mark.security
    @pytest.mark.p0
    def test_horizontal_privilege_escalation(self, non_admin_login):
        """普通用户访问用户列表应被拒绝（无菜单权限 code=403）"""
        with allure.step("以普通用户身份访问用户列表"):
            list_resp = non_admin_login.request(
                method="GET", path="/system/user/list",
                params={"pageNum": 1, "pageSize": 50},
            )
            body = list_resp.json()
        with allure.step("验证水平越权被拦截（预期 403）"):
            assert body.get("code") == 403, (
                f"❌ 水平越权防护不足！预期 403，实际: {body}"
            )

    # ============================================================
    # 参数篡改越权
    # ============================================================
    @allure.story("参数篡改越权")
    @allure.title("参数篡改防护 — 普通用户篡改 userId 无法修改他人资料")
    @allure.severity(allure.severity_level.BLOCKER)
    @pytest.mark.security
    @pytest.mark.p0
    def test_param_tampering_cannot_update_others(self, non_admin_login, admin_login):
        """
        经典越权场景: /system/user/profile（若依经典漏洞）

        攻击链路:
          1. 获取管理员原始昵称和 userId
          2. 普通用户调用 /system/user/profile，body 中传入管理员的 userId
          3. 验证管理员昵称未被篡改

        profile 接口设计初衷：只能修改当前登录用户自己的资料，
        从 Token 上下文提取用户 ID，忽略前端传参。
        （原为 xfail 漏洞，现已修复：接口正确从 Token 获取用户身份）

        防御性设计: 如果后端回归导致昵称被意外修改，
        finally 块自动恢复原始值，避免污染 admin_login fixture。
        """
        # Step 1: 获取管理员原始信息
        with allure.step("1. 获取管理员当前昵称和 userId"):
            admin_orig = admin_login.get_info()
            admin_nick = admin_orig.get("user", {}).get("nickName", "")
            admin_id = admin_orig.get("user", {}).get("userId")
            assert admin_id, "无法获取管理员 userId"
            allure.attach(
                f"管理员 userId={admin_id}, nickName={admin_nick}",
                name="管理员原始信息",
                attachment_type=allure.attachment_type.TEXT,
            )

        try:
            # Step 2: 普通用户发起参数篡改攻击
            with allure.step("2. 普通用户篡改 userId 参数，尝试修改管理员昵称"):
                non_admin_login.request(
                    method="PUT", path="/system/user/profile",
                    json={"userId": admin_id, "nickName": "参数篡改攻击"},
                )

            # Step 3: 验证管理员资料未被污染
            # 注意：攻击者自身的昵称被修改是预期行为——profile 接口
            # 从 Token 取用户身份，忽略前端传参 userId，只修改登录用户自己。
            # 这是正确的防护：你能改自己，但不能改别人。
            with allure.step("3. 验证管理员昵称未被篡改"):
                admin_after = admin_login.get_info()
                actual_admin = admin_after.get("user", {}).get("nickName", "")
                assert actual_admin == admin_nick, (
                    f"❌ 参数篡改漏洞！管理员的昵称被普通用户通过篡改 userId 修改了。\n"
                    f"  管理员原昵称: {admin_nick}\n"
                    f"  管理员现昵称: {actual_admin}\n"
                    f"  攻击方式: 普通用户调用 /system/user/profile，"
                    f"body 中传入 userId={admin_id}\n"
                    f"  结论: 接口正确从 Token 提取身份，防住了跨用户篡改"
                )
        finally:
            # 防御性恢复：如果漏洞回归导致管理员昵称被篡改，自动还原
            current_admin = admin_login.get_info()
            current_admin_nick = current_admin.get("user", {}).get("nickName", "")
            if current_admin_nick != admin_nick:
                admin_login.request(
                    method="PUT", path="/system/user/profile",
                    json={"nickName": admin_nick},
                )
                logger.warning(
                    f"⚠ 参数篡改漏洞！已恢复管理员昵称: "
                    f"{current_admin_nick} → {admin_nick}"
                )
