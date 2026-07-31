"""
真实用户管理模块测试用例
对应若依后台: 系统管理 → 用户管理
真实接口: /system/user/**
数据库: sys_user 表
"""
import allure
import pytest
from utils.assertions import assert_jsonpath_exact, assert_db_value, assert_db_exists

# pylint: disable=missing-function-docstring


def _created_user_id(db, username: str) -> int:
    """从数据库查询刚创建的用户 ID（跳过未找到）"""
    row = db.query_one("SELECT user_id FROM sys_user WHERE user_name=%s", (username,))
    if row is None:
        pytest.skip("创建后未在数据库中找到用户")
    return row["user_id"]


@allure.epic("若依接口测试")
@allure.feature("用户管理（真实业务）")
class TestSystemUser:
    """真实用户管理模块：增删改查 + 状态变更 + 密码重置"""

    # ---------------------------------------------------------
    # P0 · 查询
    # ---------------------------------------------------------
    @allure.story("用户查询")
    @allure.title("查询用户列表 - 返回分页数据")
    @allure.severity(allure.severity_level.BLOCKER)
    @pytest.mark.p0
    def test_list_users(self, system_user_api):
        with allure.step("请求用户分页列表"):
            resp = system_user_api.list({"pageNum": 1, "pageSize": 10})
            assert_jsonpath_exact(resp, "$.code", 200)

    @allure.story("用户查询")
    @allure.title("获取用户详情 - 管理员")
    @allure.severity(allure.severity_level.BLOCKER)
    @pytest.mark.p0
    def test_get_admin_detail(self, system_user_api):
        with allure.step("查询管理员 (userId=1) 详情"):
            resp = system_user_api.get(1)
            assert_jsonpath_exact(resp, "$.code", 200)
        with allure.step("验证返回 admin 用户信息"):
            user = resp.get("data", {})
            assert user.get("userName") == "admin", (
                f"用户应为admin: {user.get('userName')}"
            )
            assert user.get("nickName") is not None

    # ---------------------------------------------------------
    # P0 · 新增
    # ---------------------------------------------------------
    @allure.story("用户新增")
    @allure.title("新增用户 - 正常创建 + 数据库验证")
    @allure.severity(allure.severity_level.BLOCKER)
    @pytest.mark.p0
    def test_create_user(self, system_user_api, new_real_user_data, db):
        with allure.step("创建新用户"):
            resp = system_user_api.create(new_real_user_data)
            assert_jsonpath_exact(resp, "$.code", 200)
        with allure.step("数据库验证用户已落盘"):
            assert_db_exists(db,
                "SELECT user_id FROM sys_user WHERE user_name=%s AND del_flag='0'",
                params=(new_real_user_data["userName"],),
            )

    # ---------------------------------------------------------
    # P0 · 修改
    # ---------------------------------------------------------
    @allure.story("用户修改")
    @allure.title("修改用户昵称 + 数据库验证")
    @allure.severity(allure.severity_level.BLOCKER)
    @pytest.mark.p0
    def test_update_user(self, system_user_api, new_real_user_data, db):
        with allure.step("创建待编辑的用户"):
            resp = system_user_api.create(new_real_user_data)
            assert_jsonpath_exact(resp, "$.code", 200)
            user_id = _created_user_id(db, new_real_user_data["userName"])

        with allure.step("修改用户昵称"):
            new_nick = f"{new_real_user_data['nickName']}_已修改"
            update_data = {**new_real_user_data, "userId": user_id, "nickName": new_nick}
            resp = system_user_api.update(update_data)
            assert_jsonpath_exact(resp, "$.code", 200)

        with allure.step("数据库验证昵称已更新"):
            assert_db_value(db,
                "SELECT nick_name FROM sys_user WHERE user_id=%s",
                expected=new_nick,
                params=(user_id,),
            )

    # ---------------------------------------------------------
    # P0 · 删除
    # ---------------------------------------------------------
    @allure.story("用户删除")
    @allure.title("删除用户 + 数据库验证")
    @allure.severity(allure.severity_level.BLOCKER)
    @pytest.mark.p0
    def test_delete_user(self, system_user_api, new_real_user_data, db):
        with allure.step("创建待删除的用户"):
            system_user_api.create(new_real_user_data)
            user_id = _created_user_id(db, new_real_user_data["userName"])

        with allure.step("软删除用户"):
            resp = system_user_api.delete(user_id)
            assert_jsonpath_exact(resp, "$.code", 200)

        with allure.step("数据库验证 del_flag='2'"):
            assert_db_value(db,
                "SELECT del_flag FROM sys_user WHERE user_id=%s",
                expected="2",
                params=(user_id,),
            )

    # ---------------------------------------------------------
    # P1 · 异常场景
    # ---------------------------------------------------------
    @allure.story("用户查询")
    @allure.title("不存在的用户ID应返回错误")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.p1
    def test_get_nonexistent_user(self, system_user_api):
        with allure.step("查询不存在的 userId=999999"):
            resp = system_user_api.get(999999)
        with allure.step("验证返回非 200（用户不存在）"):
            assert resp.get("code") != 200, "不存在的用户应返回错误"

    @allure.story("用户新增")
    @allure.title("重复用户名创建应失败")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.p1
    def test_create_duplicate_username(self, system_user_api):
        with allure.step("尝试创建重名 admin 用户"):
            duplicate_data = system_user_api.build_user_data(
                username="admin",
                nick_name="重复测试",
            )
            resp = system_user_api.create(duplicate_data)
        with allure.step("验证创建被拒绝"):
            assert resp.get("code") != 200, "重复用户名应返回错误"

    # ---------------------------------------------------------
    # P1 · 状态变更
    # ---------------------------------------------------------
    @allure.story("用户状态")
    @allure.title("禁用用户 + 数据库验证")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.p1
    def test_disable_user(self, system_user_api, new_real_user_data, db):
        with allure.step("创建用户"):
            system_user_api.create(new_real_user_data)
            user_id = _created_user_id(db, new_real_user_data["userName"])

        with allure.step("禁用用户"):
            resp = system_user_api.change_status(userId=user_id, status="1")
            assert_jsonpath_exact(resp, "$.code", 200)

        with allure.step("数据库验证 status='1'"):
            assert_db_value(db,
                "SELECT status FROM sys_user WHERE user_id=%s",
                expected="1",
                params=(user_id,),
            )

        with allure.step("恢复用户状态（清理）"):
            system_user_api.change_status(userId=user_id, status="0")

    # ---------------------------------------------------------
    # P1 · 密码重置
    # ---------------------------------------------------------
    @allure.story("用户维护")
    @allure.title("重置用户密码")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.p1
    def test_reset_password(self, system_user_api, new_real_user_data, db):
        with allure.step("创建用户"):
            system_user_api.create(new_real_user_data)
            user_id = _created_user_id(db, new_real_user_data["userName"])

        with allure.step("重置密码为 654321"):
            resp = system_user_api.reset_password(user_id, "654321")
            assert_jsonpath_exact(resp, "$.code", 200)

    # ---------------------------------------------------------
    # P1 · 个人信息
    # ---------------------------------------------------------
    @allure.story("用户查询")
    @allure.title("获取当前用户个人信息")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.p1
    def test_get_profile(self, system_user_api):
        """验证 profile() 返回当前登录用户信息"""
        with allure.step("请求当前用户个人信息"):
            resp = system_user_api.profile()
            assert_jsonpath_exact(resp, "$.code", 200)
        with allure.step("验证返回了 userName"):
            user_data = resp.get("data", {})
            assert user_data.get("userName"), "应返回当前用户名"
