"""
登录与会话模块测试用例
P0: 管理员登录 / 密码错误 / 账号禁用
"""
import uuid
import allure
import pytest
from api import LoginApi, SystemUserApi
from utils.assertions import assert_jsonpath_exact


def _find_user_id(db, username: str) -> int:
    """查用户 ID（复用已有 db 连接，不创建新连接）"""
    row = db.query_one("SELECT user_id FROM sys_user WHERE user_name=%s", (username,))
    assert row, f"用户不存在: {username}"
    return row["user_id"]


@allure.epic("若依接口测试")
@allure.feature("登录与会话")
class TestLogin:

    @allure.story("正常登录")
    @allure.title("管理员正常登录 — 获取 token 并访问受保护资源")
    @allure.severity(allure.severity_level.BLOCKER)
    @pytest.mark.p0
    def test_admin_login_success(self, admin_login):
        """登录成功，token 可用于 getInfo"""
        info = admin_login.get_info()
        assert_jsonpath_exact(info, "$.code", 200)
        assert info.get("user"), "应返回用户信息"

    @allure.story("异常登录")
    @allure.title("密码错误 — 登录失败")
    @allure.severity(allure.severity_level.BLOCKER)
    @pytest.mark.p0
    def test_login_wrong_password(self):
        """密码错误不应返回 token"""
        api = LoginApi()
        token = api.login("admin", "wrong_password_123")
        assert token is None, "密码错误不应登录成功"

    @allure.story("异常登录")
    @allure.title("禁用账号 — 无法登录")
    @allure.severity(allure.severity_level.BLOCKER)
    @pytest.mark.p0
    def test_login_disabled_user(self, system_user_api, db):
        """被禁用的用户无法登录"""
        suffix = uuid.uuid4().hex[:8]
        username = f"disabled_test_{suffix}"

        resp = system_user_api.create(
            SystemUserApi.build_user_data(username=username))
        assert resp.get("code") == 200, f"创建用户失败: {resp}"

        uid = _find_user_id(db, username)
        system_user_api.change_status(userId=uid, status="1")

        api = LoginApi()
        token = api.login(username, "123456")
        assert token is None, f"禁用用户不应登录成功: {username}"

        system_user_api.delete([uid])

    @allure.story("会话管理")
    @allure.title("禁用后的 token 应立即失效")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.p0
    def test_token_rejected_after_user_disabled(self, system_user_api, db):
        """用户登录后被管理员禁用，旧 token 应立即失效"""
        suffix = uuid.uuid4().hex[:8]
        username = f"revoked_{suffix}"

        resp = system_user_api.create(
            SystemUserApi.build_user_data(username=username))
        assert resp.get("code") == 200

        user_login = LoginApi()
        token = user_login.login(username, "123456")
        assert token, "新用户登录失败"
        info = user_login.get_info()
        assert_jsonpath_exact(info, "$.code", 200)

        uid = _find_user_id(db, username)
        system_user_api.change_status(userId=uid, status="1")

        info_after = user_login.get_info()
        # 禁用后的 token 应被系统拒绝
        assert info_after.get("code") == 500, f"禁用后的 token 应被拒绝: {info_after}"

        system_user_api.delete([uid])
