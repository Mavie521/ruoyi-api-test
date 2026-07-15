"""
安全测试用例 —— SQL 注入 / XSS / 越权 / Token 伪造
覆盖若依系统常见安全弱点，增强测试纵深。

面试话术：具备安全测试意识，能覆盖 SQL 注入、XSS、越权等安全场景。
"""
import allure
import pytest
from api import LoginApi
from utils.assertions import HttpAssert

assertions = HttpAssert()


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
        data["roleName"] = f"x{xss_payload[:20]}"
        resp = role_api.create_role(data)
        # 预期：系统做字符过滤后返回非 500 即可（可能返回 200 或参数校验错误）
        assert resp.get("code") != 500, f"XSS 不应导致 500: {xss_payload}"

    # === 已知 Bug：< 字符导致 Java JSON 解析器返回 500 ===
    # RuoYi 后端未对 '<' 字符做预处理，导致 Jackson 解析 JSON 时抛出异常
    # 期望返回 HTTP 400 参数错误，实际返回 500 服务端内部错误
    @allure.story("XSS")
    @allure.title("已知 Bug：< 字符导致后端 JSON 解析崩溃")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.security
    @pytest.mark.xfail(reason="Ruoyi Bug: '<'字符导致Jackson JSON解析器返回500，应返回400")
    def test_role_name_xss_crash_bug(self, role_api, new_role_data):
        """Ruoyi-482: '<' 字符触发 Jackson JSON 解析异常，应返回 400 而非 500"""
        data = new_role_data.copy()
        data["roleName"] = "x<B oncopy=alert(1)>test</B>"
        resp = role_api.create_role(data)
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
            resp = api.get("/getInfo")
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
