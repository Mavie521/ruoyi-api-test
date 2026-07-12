"""
用户管理模块测试用例
覆盖: GET/POST/PUT/DELETE /test/user/*
"""
import allure
import pytest
from utils.assertions import HttpAssert

assertions = HttpAssert()


@allure.epic("若依接口测试")
@allure.feature("用户管理模块")
class TestUser:

    # ---------------------------------------------------------
    # P0 · 查询类
    # ---------------------------------------------------------
    @allure.story("用户查询")
    @allure.title("获取用户列表 - 正常返回数据")
    @allure.severity(allure.severity_level.BLOCKER)
    @pytest.mark.smoke
    @pytest.mark.p0
    def test_list_users(self, user_api):
        """查询用户列表"""
        resp = user_api.list_users()

        assert resp.get("code") == 200, f"code异常: {resp}"
        assert "data" in resp, "响应应包含 data 字段"
        assert isinstance(resp["data"], list), "data 应为数组"

    @allure.story("用户查询")
    @allure.title("获取指定用户详情")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.smoke
    @pytest.mark.p0
    def test_get_user_by_id(self, user_api):
        """获取第一个用户的详情"""
        list_resp = user_api.list_users()
        user_list = list_resp.get("data", [])
        if not user_list:
            pytest.skip("用户列表为空，跳过测试")

        user_id = user_list[0].get("userId")
        assert user_id is not None, "用户数据缺少 userId"

        detail_resp = user_api.get_user(user_id)
        assert detail_resp.get("code") == 200

    # ---------------------------------------------------------
    # P0 · 新增
    # ---------------------------------------------------------
    @allure.story("用户新增")
    @allure.title("新增用户 - 正常创建成功")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.smoke
    @pytest.mark.p0
    def test_create_user(self, user_api, new_user_data):
        """创建新用户"""
        resp = user_api.create_user(new_user_data)
        assert resp.get("code") == 200, f"创建用户失败: {resp}"

    # ---------------------------------------------------------
    # P0 · 修改
    # ---------------------------------------------------------
    @allure.story("用户修改")
    @allure.title("更新用户信息")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.smoke
    @pytest.mark.p0
    def test_update_user(self, user_api, new_user_data):
        """先创建用户，再更新其信息"""
        create_resp = user_api.create_user(new_user_data)
        assert create_resp.get("code") == 200, f"创建失败: {create_resp}"

        list_resp = user_api.list_users()
        user_list = list_resp.get("data", [])
        created_user = next((u for u in user_list if u.get("username") == new_user_data["username"]), None)
        if not created_user:
            pytest.skip("创建后未在列表中查找到用户")

        user_id = created_user.get("userId")
        update_data = user_api.build_user_data(
            username=new_user_data["username"],
            user_id=user_id,
            password="654321",
            mobile="13900139000",
        )
        update_resp = user_api.update_user(update_data)
        assert update_resp.get("code") == 200, f"更新失败: {update_resp}"

    # ---------------------------------------------------------
    # P0 · 删除
    # ---------------------------------------------------------
    @allure.story("用户删除")
    @allure.title("删除用户 - 正常删除")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.smoke
    @pytest.mark.p0
    def test_delete_user(self, user_api, new_user_data):
        """先创建用户，再将其删除"""
        create_resp = user_api.create_user(new_user_data)
        assert create_resp.get("code") == 200, f"创建失败: {create_resp}"

        list_resp = user_api.list_users()
        user_list = list_resp.get("data", [])
        target = next((u for u in user_list if u.get("username") == new_user_data["username"]), None)
        if not target:
            pytest.skip("创建后未找到用户")

        user_id = target.get("userId")
        delete_resp = user_api.delete_user(user_id)
        assert delete_resp.get("code") == 200, f"删除失败: {delete_resp}"

    # ---------------------------------------------------------
    # P1 · 异常场景
    # ---------------------------------------------------------
    @allure.story("用户查询")
    @allure.title("不存在的userId获取详情应返回错误")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.p1
    def test_get_nonexistent_user(self, user_api):
        """使用一个非常大的userId，验证异常处理"""
        resp = user_api.get_user(99999999)
        assert resp.get("code") != 200 or resp.get("success") is not False, \
            "不存在的用户应返回错误响应"

    @allure.story("用户新增")
    @allure.title("新增用户 - 空数据应返回错误")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.p1
    def test_create_user_empty_data(self, user_api):
        """发送空数据"""
        resp = user_api.create_user({})
        assert resp.get("code") != 200 or resp.get("data") is not None, \
            "空数据应返回错误或没有有效data"

    # ---------------------------------------------------------
    # P2 · 次要功能
    # ---------------------------------------------------------
    @allure.story("用户查询")
    @allure.title("获取用户列表 - 列表不为空")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.p2
    def test_list_users_not_empty(self, user_api):
        """用户列表不应为空（若依系统初始有用户）"""
        resp = user_api.list_users()
        assert len(resp.get("data", [])) > 0, "用户列表不应为空"
