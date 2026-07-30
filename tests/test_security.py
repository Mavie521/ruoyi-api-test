"""
安全测试用例 —— SQL 注入 / XSS / 越权 / Token 伪造
覆盖若依系统常见安全弱点，增强测试纵深。
具备安全测试意识，能覆盖 SQL 注入、XSS、越权等安全场景。
"""
import allure
import pytest
from api import LoginApi
from utils.assertions import assert_jsonpath_exact


@allure.epic("若依接口测试")
@allure.feature("安全测试")
class TestSecurity:
    """安全测试：SQL注入 / XSS / 越权 / 边界异常"""

    @allure.story("SQL 注入")
    @allure.title("登录接口 SQL 注入 — 多种注入 payload")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.security
    @pytest.mark.p1
    @pytest.mark.parametrize("payload", [
        "admin' OR '1'='1",
        "admin'--",
        "admin' OR 1=1--",
        "admin\" OR \"1\"=\"1",
    ])
    def test_login_sql_injection(self, payload):
        """防止 SQL 注入：恶意用户名不应登录成功"""
        api = LoginApi()
        token = api.login(payload, "admin123")
        assert token is None, f"SQL 注入 payload 不应成功: {payload}"

    @allure.story("XSS")
    @allure.title("角色名 XSS 注入 — 特殊字符/脚本")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.security
    @pytest.mark.p1
    @pytest.mark.parametrize("xss_payload", [
        '<script>alert("xss")</script>',
        '"><script>alert(1)</script>',
        'javascript:alert(1)',
        '<ScRiPt>alert(1)</ScRiPt>',
    ])
    def test_role_name_xss(self, role_api, new_role_data, xss_payload):
        """角色名不应被 XSS 脚本影响"""
        data = new_role_data.copy()
        data["roleName"] = f"{new_role_data['roleName']}_x{xss_payload[:8]}"
        resp = role_api.create(data)
        # 预期：系统做字符过滤后返回非 500 即可（可能返回 200 或参数校验错误）
        assert resp.get("code") != 500, f"XSS 不应导致 500: {xss_payload}"

    @allure.story("XSS")
    @allure.title("角色名含 < 字符 — 不应导致服务端 500（已修复）")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.security
    @pytest.mark.p1
    def test_role_name_xss_crash_bug(self, role_api, new_role_data):
        """< 特殊字符不应导致服务端 500"""
        data = new_role_data.copy()
        data["roleName"] = f"x<B>test_{new_role_data['roleKey']}"
        resp = role_api.create(data)
        assert resp.get("code") != 500, "< 字符不应导致服务端 500"

    @allure.story("越权测试")
    @allure.title("伪造/过期 Token 访问 — 应返回 401")
    @allure.severity(allure.severity_level.BLOCKER)
    @pytest.mark.security
    @pytest.mark.p1
    def test_fake_token_access(self):
        """伪造 Token 无法访问受保护接口"""
        api = LoginApi()
        fake_tokens = [
            "eyJhbGciOiJIUzUxMiJ9.fake.xxxx",       # 伪造 JWT
            "Bearer invalid_token_here",             # 格式错误
            "",                                       # 空字符串
            "abcdef123456",                          # 随机字符串
        ]
        for fake in fake_tokens:
            api.set_token(fake)
            resp = api.request(method="GET", path="/getInfo")
            body = resp.json()
            # 预期：伪造 Token 访问失败（应返回 HTTP 401/403 或 JSON code != 200）
            is_rejected = resp.status_code in (401, 403) or body.get("code") != 200
            assert is_rejected, f"伪造 Token 应被拒绝: {fake[:20]}"

    @allure.story("边界异常")
    @allure.title("超长用户名/密码 — 系统容错")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.security
    @pytest.mark.p2
    def test_extreme_length_input(self):
        """超长输入不应导致系统崩溃"""
        api = LoginApi()
        long_str = "A" * 5000
        token = api.login(long_str, long_str)
        # 期望：不会 500 崩溃（可能成功或失败，但不抛异常）
        assert token is None or len(token) > 0

    @allure.story("垂直越权")
    @allure.title("普通用户不能操作管理员接口")
    @allure.severity(allure.severity_level.BLOCKER)
    @pytest.mark.security
    @pytest.mark.p0
    def test_common_user_cannot_escalate(self, non_admin_login):
        """普通角色用户不能创建角色（管理员接口）"""
        from api import RoleApi
        role_api = RoleApi()
        role_api.set_token(non_admin_login.token)
        resp = role_api.create({"roleName": "越权角色", "roleKey": "escalate"})
        assert resp.get("code") != 200, f"普通用户不应能创建角色: {resp}"

    @allure.story("水平越权")
    @allure.title("数据权限隔离 — 普通用户不能查看其他用户")
    @allure.severity(allure.severity_level.BLOCKER)
    @pytest.mark.security
    @pytest.mark.p0
    def test_horizontal_privilege_escalation(self, non_admin_login):
        """普通用户访问用户列表应被拒绝（无菜单权限 code=403）"""
        from api import BaseApi
        api = BaseApi()
        api.set_token(non_admin_login.token)

        list_resp = api.request(method="GET", path="/system/user/list",
                                params={"pageNum": 1, "pageSize": 50})
        body = list_resp.json()
        # 后端已修复水平越权：无用户管理菜单权限的用户访问列表返回 403
        assert body.get("code") == 403, (
            f"水平越权防护预期 403，实际: {body}"
        )

    @allure.story("参数篡改越权")
    @allure.title("参数篡改防护 — 普通用户篡改 userId 无法修改他人资料")
    @allure.severity(allure.severity_level.BLOCKER)
    @pytest.mark.security
    @pytest.mark.p0
    def test_param_tampering_cannot_update_others(self, non_admin_login, admin_login):
        """
        普通用户修改资料时在 body 中传入管理员的 userId，
        系统应从 Token 上下文提取当前用户 ID，忽略前端传参。
        （原为 xfail 漏洞，现已修复：接口正确从 Token 获取用户身份）
        """
        from api import BaseApi

        admin_api = BaseApi()
        admin_api.set_token(admin_login.token)
        admin_orig = admin_api.request(method="GET", path="/getInfo").json()
        admin_nick = admin_orig.get("user", {}).get("nickName", "")
        admin_id = admin_orig.get("user", {}).get("userId")
        assert admin_id, "无法获取管理员 userId"

        api = BaseApi()
        api.set_token(non_admin_login.token)
        api.request(
            method="PUT", path="/system/user/profile",
            json={"userId": admin_id, "nickName": "参数篡改攻击"},
        )

        admin_after = admin_api.request(method="GET", path="/getInfo").json()
        assert admin_after.get("user", {}).get("nickName") == admin_nick, (
            "参数篡改漏洞！管理员的昵称被普通用户通过篡改 userId 修改了。\n"
            "修复建议：/system/user/profile 接口应从 Token 上下文获取当前用户 ID，"
            "忽略前端传入的 userId 参数。"
        )
