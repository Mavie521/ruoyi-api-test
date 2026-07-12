"""
登录模块测试用例
覆盖: POST /login, GET /getInfo, GET /getRouters
"""
import allure
import pytest
from api import LoginApi
from utils.assertions import HttpAssert

assertions = HttpAssert()


@allure.epic("若依接口测试")
@allure.feature("登录认证模块")
class TestLogin:

    # ---------------------------------------------------------
    # P0 · 正常场景
    # ---------------------------------------------------------
    @allure.story("登录")
    @allure.title("管理员登录成功 - 能获取到token")
    @allure.severity(allure.severity_level.BLOCKER)
    @pytest.mark.smoke
    @pytest.mark.p0
    def test_admin_login_success(self):
        """验证管理员账号可以正常登录并获取token"""
        api = LoginApi()
        token = api.login("admin", "admin123")

        assert token is not None, "登录应返回 token"
        assert len(token) > 0, "token 不应为空字符串"

    @allure.story("登录后查询")
    @allure.title("登录后可以获取当前用户信息")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.smoke
    @pytest.mark.p0
    def test_get_info_after_login(self, login_api):
        """验证登录后调用 getInfo 成功"""
        resp = login_api.get_info()

        assert resp.get("code") == 200, f"状态码异常: {resp}"
        assert resp.get("user") is not None or resp.get("data") is not None, \
            "响应应包含用户信息"

    @allure.story("登录后查询")
    @allure.title("登录后可以获取菜单路由")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.smoke
    @pytest.mark.p0
    def test_get_routers_after_login(self, login_api):
        """验证登录后调用 getRouters 返回菜单树"""
        resp = login_api.get_routers()

        if resp.get("code") is not None:
            assert resp["code"] == 200
        assert resp is not None, "响应不应为空"

    # ---------------------------------------------------------
    # P1 · 异常场景
    # ---------------------------------------------------------
    @allure.story("登录 - 异常场景")
    @allure.title("错误密码登录应失败")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.p1
    def test_login_wrong_password(self):
        """使用错误密码登录，应返回失败"""
        api = LoginApi()
        token = api.login("admin", "wrong_password_123")

        assert token is None, "错误密码登录不应返回 token"

    @allure.story("登录 - 异常场景")
    @allure.title("不存在的用户登录应失败")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.p1
    def test_login_nonexistent_user(self):
        """使用不存在的用户名登录"""
        api = LoginApi()
        token = api.login("nonexistent_user_xyz", "any_password")

        assert token is None, "不存在的用户不应返回 token"

    @allure.story("登录 - 异常场景")
    @allure.title("空用户名登录应失败")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.p1
    def test_login_empty_username(self):
        """空用户名登录"""
        api = LoginApi()
        token = api.login("", "admin123")
        assert token is None, "空用户名不应返回 token"
