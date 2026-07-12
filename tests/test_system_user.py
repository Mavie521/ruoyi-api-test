"""
真实用户管理模块测试用例
对应若依后台: 系统管理 → 用户管理
真实接口: /system/user/**
数据库: sys_user 表
"""
import allure
import pytest
from utils.logger import logger


@allure.epic("若依接口测试")
@allure.feature("用户管理（真实业务）")
class TestSystemUser:

    # ---------------------------------------------------------
    # P0 · 查询
    # ---------------------------------------------------------
    @allure.story("用户查询")
    @allure.title("查询用户列表 - 返回分页数据")
    @allure.severity(allure.severity_level.BLOCKER)
    @pytest.mark.smoke
    @pytest.mark.p0
    def test_list_users(self, system_user_api):
        """查询用户列表"""
        resp = system_user_api.list_users({"pageNum": 1, "pageSize": 10})

        assert resp.get("code") == 200
        assert "rows" in resp, "响应应包含 rows"
        assert resp["total"] > 0, "用户列表不应为空"

    @allure.story("用户查询")
    @allure.title("获取用户详情 - 管理员")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.smoke
    @pytest.mark.p0
    def test_get_admin_detail(self, system_user_api):
        """获取管理员用户详情"""
        resp = system_user_api.get_user(1)
        assert resp.get("code") == 200
        user = resp.get("data", {})
        assert user.get("userName") == "admin", f"用户应为admin: {user.get('userName')}"
        assert user.get("nickName") is not None

    # ---------------------------------------------------------
    # P0 · 新增 + 数据库验证
    # ---------------------------------------------------------
    @allure.story("用户新增")
    @allure.title("新增用户 - 正常创建 + 数据库验证")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.smoke
    @pytest.mark.p0
    def test_create_user(self, system_user_api, new_real_user_data, db):
        """创建用户并验证数据库落盘"""
        resp = system_user_api.create_user(new_real_user_data)
        assert resp.get("code") == 200, f"创建失败: {resp}"

        db.assert_exists(
            "SELECT user_id FROM sys_user WHERE user_name=%s AND del_flag='0'",
            params=(new_real_user_data["userName"],),
        )

    # ---------------------------------------------------------
    # P0 · 修改 + 数据库验证
    # ---------------------------------------------------------
    @allure.story("用户修改")
    @allure.title("修改用户昵称 + 数据库验证")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.smoke
    @pytest.mark.p0
    def test_update_user(self, system_user_api, new_real_user_data, db):
        """先创建用户，再修改昵称，验证数据库"""
        resp = system_user_api.create_user(new_real_user_data)
        assert resp.get("code") == 200

        list_resp = system_user_api.list_users({"pageSize": 100})
        rows = list_resp.get("rows", [])
        target = next((u for u in rows if u.get("userName") == new_real_user_data["userName"]), None)
        if not target:
            pytest.skip("创建后未找到用户")

        user_id = target.get("userId")
        new_nick = f"{new_real_user_data['nickName']}_已修改"

        update_data = {**new_real_user_data, "userId": user_id, "nickName": new_nick}
        update_resp = system_user_api.update_user(update_data)
        assert update_resp.get("code") == 200, f"修改失败: {update_resp}"

        db.assert_value(
            "SELECT nick_name FROM sys_user WHERE user_id=%s",
            expected=new_nick,
            params=(user_id,),
        )

    # ---------------------------------------------------------
    # P0 · 删除（逻辑删除 del_flag='2'）+ 数据库验证
    # ---------------------------------------------------------
    @allure.story("用户删除")
    @allure.title("删除用户 + 数据库验证")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.smoke
    @pytest.mark.p0
    def test_delete_user(self, system_user_api, new_real_user_data, db):
        """创建用户 → 删除 → 验证数据库 del_flag='2'"""
        system_user_api.create_user(new_real_user_data)

        list_resp = system_user_api.list_users({"pageSize": 100})
        rows = list_resp.get("rows", [])
        target = next((u for u in rows if u.get("userName") == new_real_user_data["userName"]), None)
        if not target:
            pytest.skip("未找到用户")

        user_id = target.get("userId")
        resp = system_user_api.delete_user(user_id)
        assert resp.get("code") == 200

        db.assert_value(
            "SELECT del_flag FROM sys_user WHERE user_id=%s",
            expected="2",
            params=(user_id,),
        )

    # ---------------------------------------------------------
    # P1 · 异常场景
    # ---------------------------------------------------------
    @allure.story("用户查询")
    @allure.title("不存在的用户ID应返回错误")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.p1
    def test_get_nonexistent_user(self, system_user_api):
        """查询不存在的用户"""
        resp = system_user_api.get_user(999999)
        assert resp.get("code") != 200, "不存在的用户应返回错误"

    @allure.story("用户新增")
    @allure.title("重复用户名创建应失败")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.p1
    def test_create_duplicate_username(self, system_user_api):
        """使用已存在的用户名 admin 创建应失败"""
        duplicate_data = {
            "userName": "admin",
            "nickName": "重复测试",
            "password": "123456",
            "deptId": 103,
            "postIds": [],
            "roleIds": [],
        }
        resp = system_user_api.create_user(duplicate_data)
        assert resp.get("code") != 200, "重复用户名应返回错误"

    # ---------------------------------------------------------
    # P1 · 状态切换 + 数据库验证
    # ---------------------------------------------------------
    @allure.story("用户状态")
    @allure.title("禁用用户 + 数据库验证")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.p1
    def test_disable_user(self, system_user_api, new_real_user_data, db):
        """创建用户 → 禁用 → 验证数据库 status='1'"""
        system_user_api.create_user(new_real_user_data)

        list_resp = system_user_api.list_users({"pageSize": 100})
        rows = list_resp.get("rows", [])
        target = next((u for u in rows if u.get("userName") == new_real_user_data["userName"]), None)
        if not target:
            pytest.skip("未找到用户")

        user_id = target.get("userId")
        resp = system_user_api.change_status(user_id, "1")
        assert resp.get("code") == 200

        db.assert_value(
            "SELECT status FROM sys_user WHERE user_id=%s",
            expected="1",
            params=(user_id,),
        )

        system_user_api.change_status(user_id, "0")

    # ---------------------------------------------------------
    # P1 · 重置密码
    # ---------------------------------------------------------
    @allure.story("用户维护")
    @allure.title("重置用户密码")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.p1
    def test_reset_password(self, system_user_api, new_real_user_data):
        """创建用户 → 重置密码"""
        system_user_api.create_user(new_real_user_data)

        list_resp = system_user_api.list_users({"pageSize": 100})
        rows = list_resp.get("rows", [])
        target = next((u for u in rows if u.get("userName") == new_real_user_data["userName"]), None)
        if not target:
            pytest.skip("未找到用户")

        user_id = target.get("userId")
        resp = system_user_api.reset_password(user_id, "654321")
        assert resp.get("code") == 200, f"重置密码失败: {resp}"
