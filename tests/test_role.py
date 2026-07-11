"""
角色管理模块测试用例
覆盖: 角色 CRUD、状态切换、数据库断言、下拉选项、数据权限等
"""
import allure
import pytest
from utils.assertions import HttpAssert

assertions = HttpAssert()


@allure.epic("若依接口测试")
@allure.feature("角色管理模块")
class TestRole:

    # ---------------------------------------------------------
    # 查询类
    # ---------------------------------------------------------
    @allure.story("角色查询")
    @allure.title("查询角色列表 - 正常返回分页数据")
    @allure.severity(allure.severity_level.BLOCKER)
    @pytest.mark.smoke
    def test_list_roles(self, role_api):
        """查询角色列表"""
        resp = role_api.list_roles()

        assert resp.get("code") == 200
        assert "rows" in resp, "响应应包含 rows"
        assert resp["total"] > 0, "角色列表不应为空"

    @allure.story("角色查询")
    @allure.title("获取角色详情")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.smoke
    def test_get_role_detail(self, role_api):
        """获取第一个角色的详情"""
        list_resp = role_api.list_roles({"pageNum": 1, "pageSize": 1})
        rows = list_resp.get("rows", [])
        if not rows:
            pytest.skip("角色列表为空")

        role_id = rows[0].get("roleId")
        detail_resp = role_api.get_role(role_id)

        assert detail_resp.get("code") == 200

    @allure.story("角色查询")
    @allure.title("获取角色下拉选项列表")
    @allure.severity(allure.severity_level.NORMAL)
    def test_option_select(self, role_api):
        """角色下拉选项（用于表单）"""
        resp = role_api.option_select()
        assert resp.get("code") == 200

    @allure.story("角色查询")
    @allure.title("获取部门树")
    @allure.severity(allure.severity_level.NORMAL)
    def test_dept_tree(self, role_api):
        """获取第一个角色的部门树"""
        list_resp = role_api.list_roles({"pageNum": 1, "pageSize": 1})
        rows = list_resp.get("rows", [])
        if not rows:
            pytest.skip("角色列表为空")

        role_id = rows[0].get("roleId")
        resp = role_api.dept_tree(role_id)
        assert resp.get("code") == 200

    # ---------------------------------------------------------
    # 新增
    # ---------------------------------------------------------
    @allure.story("角色新增")
    @allure.title("新增角色 - 正常创建成功 + 数据库验证")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.smoke
    def test_create_role(self, role_api, new_role_data, db):
        """创建新角色，并验证数据库"""
        resp = role_api.create_role(new_role_data)
        assert resp.get("code") == 200, f"创建角色失败: {resp}"
        # 数据库断言：验证角色已写入 sys_role 表
        db.assert_exists(
            "SELECT role_id FROM sys_role WHERE role_key=%s",
            params=(new_role_data["roleKey"],),
        )

    @allure.story("角色新增")
    @allure.title("新增角色 - 缺少必填字段应失败")
    @allure.severity(allure.severity_level.NORMAL)
    def test_create_role_missing_required(self, role_api):
        """缺少必填字段 roleName"""
        import time
        suffix = str(int(time.time() * 1000))[-6:]
        invalid_data = {
            "roleKey": f"test_missing_{suffix}",
            "roleSort": 1,
        }
        resp = role_api.create_role(invalid_data)
        assert resp.get("code") != 200, "缺少必填字段应返回错误"

    # ---------------------------------------------------------
    # 修改
    # ---------------------------------------------------------
    @allure.story("角色修改")
    @allure.title("编辑角色信息 + 数据库验证")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.smoke
    def test_update_role(self, role_api, new_role_data, db):
        """先创建角色，再编辑，并验证数据库已更新"""
        # 创建
        create_resp = role_api.create_role(new_role_data)
        assert create_resp.get("code") == 200

        # 从列表中查找（pageSize=100 确保新角色在返回结果中）
        list_resp = role_api.list_roles({"pageSize": 100})
        rows = list_resp.get("rows", [])
        target = None
        for r in rows:
            if r.get("roleName") == new_role_data["roleName"]:
                target = r
                break

        if not target:
            pytest.skip("创建后未在列表中找到角色")

        role_id = target.get("roleId")
        new_name = f"{new_role_data['roleName']}_已编辑"
        update_data = role_api.build_role_data(
            role_name=new_name,
            role_key=new_role_data["roleKey"],
            role_sort=2,
            role_id=role_id,
            menu_ids=[],
        )
        update_resp = role_api.update_role(update_data)
        assert update_resp.get("code") == 200, f"编辑失败: {update_resp}"

        # 数据库断言：验证 role_name 已更新
        db.assert_value(
            "SELECT role_name FROM sys_role WHERE role_id=%s",
            expected=new_name,
            params=(role_id,),
        )

    # ---------------------------------------------------------
    # 状态切换
    # ---------------------------------------------------------
    @allure.story("角色状态")
    @allure.title("禁用角色 + 数据库验证")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_disable_role(self, role_api, new_role_data, db):
        """创建角色 → 禁用 → 验证数据库状态"""
        role_api.create_role(new_role_data)

        list_resp = role_api.list_roles({"pageSize": 100})
        rows = list_resp.get("rows", [])
        target = None
        for r in rows:
            if r.get("roleName") == new_role_data["roleName"]:
                target = r
                break
        if not target:
            pytest.skip("未找到角色")

        role_id = target.get("roleId")
        disable_resp = role_api.change_status({
            "roleId": role_id,
            "status": "1",
        })
        assert disable_resp.get("code") == 200, f"禁用失败: {disable_resp}"

        # 数据库断言：验证 status='1'
        db.assert_value(
            "SELECT status FROM sys_role WHERE role_id=%s",
            expected="1",
            params=(role_id,),
        )

    # ---------------------------------------------------------
    # 删除（若依为逻辑删除 del_flag='2'）
    # ---------------------------------------------------------
    @allure.story("角色删除")
    @allure.title("删除角色 + 数据库验证")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.smoke
    def test_delete_role(self, role_api, new_role_data, db):
        """先创建角色，再删除，并验证数据库 del_flag='2'"""
        role_api.create_role(new_role_data)

        list_resp = role_api.list_roles({"pageSize": 100})
        rows = list_resp.get("rows", [])
        target = None
        for r in rows:
            if r.get("roleName") == new_role_data["roleName"]:
                target = r
                break
        if not target:
            pytest.skip("未找到角色")

        role_id = target.get("roleId")
        delete_resp = role_api.delete_role([role_id])
        assert delete_resp.get("code") == 200, f"删除失败: {delete_resp}"

        # 数据库断言：若依逻辑删除，del_flag='2'
        db.assert_value(
            "SELECT del_flag FROM sys_role WHERE role_id=%s",
            expected="2",
            params=(role_id,),
        )

    # ---------------------------------------------------------
    # 用户授权
    # ---------------------------------------------------------
    @allure.story("角色授权")
    @allure.title("获取未绑定用户列表和已绑定用户列表")
    @allure.severity(allure.severity_level.NORMAL)
    def test_auth_user_lists(self, role_api):
        """测试授权相关接口"""
        list_resp = role_api.list_roles({"pageNum": 1, "pageSize": 1})
        rows = list_resp.get("rows", [])
        if not rows:
            pytest.skip("角色列表为空")

        role_id = rows[0].get("roleId")

        unallocated = role_api.unallocated_user_list({"roleId": role_id})
        assert unallocated.get("code") == 200

        allocated = role_api.allocated_user_list({"roleId": role_id})
        assert allocated.get("code") == 200
