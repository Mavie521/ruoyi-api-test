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
        with allure.step("验证 Token 可访问受保护接口 /getInfo"):
            info = admin_login.get_info()
            assert_jsonpath_exact(info, "$.code", 200)
            assert info.get("user"), "应返回用户信息"

    @allure.story("异常登录")
    @allure.title("密码错误 — 登录失败")
    @allure.severity(allure.severity_level.BLOCKER)
    @pytest.mark.p0
    def test_login_wrong_password(self):
        """密码错误不应返回 token"""
        with allure.step("使用错误密码尝试登录"):
            api = LoginApi()
            token = api.login("admin", "wrong_password_123")
        with allure.step("验证登录被拒绝（token=None）"):
            assert token is None, "密码错误不应登录成功"

    @allure.story("异常登录")
    @allure.title("禁用账号 — 无法登录")
    @allure.severity(allure.severity_level.BLOCKER)
    @pytest.mark.p0
    def test_login_disabled_user(self, system_user_api, db):
        """被禁用的用户无法登录"""
        suffix = uuid.uuid4().hex[:8]
        username = f"disabled_test_{suffix}"

        with allure.step("创建测试用户"):
            resp = system_user_api.create(
                SystemUserApi.build_user_data(username=username))
            assert resp.get("code") == 200, f"创建用户失败: {resp}"

        with allure.step("通过数据库将用户状态设为禁用"):
            uid = _find_user_id(db, username)
            db.execute("UPDATE sys_user SET status='1' WHERE user_id=%s", (uid,))

        with allure.step("验证禁用用户无法登录"):
            api = LoginApi()
            token = api.login(username, "123456")
            assert token is None, f"禁用用户不应登录成功: {username}"

        with allure.step("清理：恢复状态并删除测试用户"):
            db.execute("UPDATE sys_user SET status='0' WHERE user_id=%s", (uid,))
            system_user_api.delete([uid])

    @allure.story("会话管理")
    @allure.title("禁用后已签发 Token 仍有效（JWT 无状态缺陷）")
    @allure.severity(allure.severity_level.BLOCKER)
    @pytest.mark.p0
    def test_token_rejected_after_user_disabled(self, system_user_api, db):
        """
        验证「登录后禁用 → 旧 Token 是否失效」
        若依没有独立的 /system/user/changeStatus 接口，
        只能通过通用编辑接口 update() 修改 status 字段。
        原生 JWT 无黑名单：账号禁用只拦截新登录，已下发的 Token 仍然放行。
        """
        suffix = uuid.uuid4().hex[:8]
        username = f"revoked_{suffix}"

        with allure.step("1. 创建新用户并登录获取 Token"):
            resp = system_user_api.create(
                SystemUserApi.build_user_data(username=username))
            assert resp.get("code") == 200

            user_login = LoginApi()
            token = user_login.login(username, "123456")
            assert token, "新用户登录失败"
            info = user_login.get_info()
            assert_jsonpath_exact(info, "$.code", 200)

        uid = _find_user_id(db, username)

        try:
            with allure.step("2. 通过 SQL 将用户状态设为禁用"):
                db.execute("UPDATE sys_user SET status='1' WHERE user_id=%s", (uid,))
                row = db.query_one(
                    "SELECT status FROM sys_user WHERE user_id=%s", (uid,))
                assert row and row["status"] == "1", (
                    f"禁用未生效！期望 status='1'，实际: {row}"
                )

            with allure.step("3. 验证禁用后无法重新登录"):
                api2 = LoginApi()
                token2 = api2.login(username, "123456")
                assert token2 is None, "禁用用户不应能重新登录"

            with allure.step("4. 验证旧 Token 仍然有效（JWT 无黑名单缺陷）"):
                info_after = user_login.get_info()
                assert info_after.get("code") == 200, (
                    "旧 Token 在禁用后仍可访问——原生 JWT 无黑名单，"
                    "修复建议：引入 Redis Token 黑名单 + 网关层拦截"
                )
        finally:
            with allure.step("5. 清理：恢复状态并删除测试用户"):
                db.execute("UPDATE sys_user SET status='0' WHERE user_id=%s", (uid,))
                system_user_api.delete([uid])
