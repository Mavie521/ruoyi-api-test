"""
角色管理模块测试用例
覆盖: 角色 CRUD、状态切换、数据库断言、下拉选项、数据权限等
"""
import uuid
import allure
import pytest
from utils.assertions import assert_jsonpath_exact, assert_db_value, assert_db_exists


def _first_role_id(role_api):
    """获取任意一个角色 ID（只读查询用，跳过空列表）"""
    resp = role_api.list({"pageNum": 1, "pageSize": 1})
    rows = resp.get("rows", [])
    if not rows:
        pytest.skip("角色列表为空")
    return rows[0].get("roleId")


def _find_role_id(role_api, role_name: str) -> int:
    """按角色名查找 ID（CRUD 操作后用，确认数据已创建）"""
    for page in range(1, 10):
        resp = role_api.list({"pageNum": page, "pageSize": 50})
        for r in resp.get("rows", []):
            if r.get("roleName") == role_name:
                return r.get("roleId")
    pytest.skip(f"未找到角色: {role_name}")


@allure.epic("若依接口测试")
@allure.feature("角色管理模块")
class TestRole:

    # ---------------------------------------------------------
    # P0 · 查询类
    # ---------------------------------------------------------
    @allure.story("角色查询")
    @allure.title("查询角色列表 - 正常返回分页数据")
    @allure.severity(allure.severity_level.BLOCKER)
    @pytest.mark.p0
    def test_list_roles(self, role_api):
        """查询角色列表"""
        resp = role_api.list()
        assert_jsonpath_exact(resp, "$.code", 200)

    @allure.story("角色查询")
    @allure.title("获取角色详情")
    @allure.severity(allure.severity_level.BLOCKER)
    @pytest.mark.p0
    def test_get_role_detail(self, role_api):
        """获取任意一个角色详情"""
        role_id = _first_role_id(role_api)
        resp = role_api.get(role_id)
        assert_jsonpath_exact(resp, "$.code", 200)

    # ---------------------------------------------------------
    # P0 · 新增
    # ---------------------------------------------------------
    @allure.story("角色新增")
    @allure.title("新增角色 - 正常创建成功 + 数据库验证")
    @allure.severity(allure.severity_level.BLOCKER)
    @pytest.mark.p0
    def test_create_role(self, role_api, new_role_data, db):
        """创建新角色，并验证数据库"""
        resp = role_api.create(new_role_data)
        assert_jsonpath_exact(resp, "$.code", 200)
        assert_db_exists(db,
            "SELECT role_id FROM sys_role WHERE role_key=%s",
            params=(new_role_data["roleKey"],),
        )

    # ---------------------------------------------------------
    # P0 · 修改
    # ---------------------------------------------------------
    @allure.story("角色修改")
    @allure.title("编辑角色信息 + 数据库验证")
    @allure.severity(allure.severity_level.BLOCKER)
    @pytest.mark.p0
    def test_update_role(self, role_api, new_role_data, db):
        """先创建角色，再编辑，并验证数据库已更新"""
        role_api.create(new_role_data)
        role_id = _find_role_id(role_api, new_role_data["roleName"])

        new_name = f"{new_role_data['roleName']}_已编辑"
        update_data = role_api.build_role_data(
            role_name=new_name,
            role_key=new_role_data["roleKey"],
            role_sort=2,
            role_id=role_id,
            menu_ids=[],
        )
        resp = role_api.update(update_data)
        assert_jsonpath_exact(resp, "$.code", 200)

        assert_db_value(db,
            "SELECT role_name FROM sys_role WHERE role_id=%s",
            expected=new_name,
            params=(role_id,),
        )

    # ---------------------------------------------------------
    # P0 · 删除
    # ---------------------------------------------------------
    @allure.story("角色删除")
    @allure.title("删除角色 + 数据库验证")
    @allure.severity(allure.severity_level.BLOCKER)
    @pytest.mark.p0
    def test_delete_role(self, role_api, new_role_data, db):
        """先创建角色，再删除，并验证数据库 del_flag='2'"""
        role_api.create(new_role_data)
        role_id = _find_role_id(role_api, new_role_data["roleName"])

        resp = role_api.delete([role_id])
        assert_jsonpath_exact(resp, "$.code", 200)

        assert_db_value(db,
            "SELECT del_flag FROM sys_role WHERE role_id=%s",
            expected="2",
            params=(role_id,),
        )

    # ---------------------------------------------------------
    # P1 · 状态切换
    # ---------------------------------------------------------
    @allure.story("角色状态")
    @allure.title("禁用角色 + 数据库验证")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.p1
    def test_disable_role(self, role_api, new_role_data, db):
        """创建角色 → 禁用 → 验证数据库状态"""
        role_api.create(new_role_data)
        role_id = _find_role_id(role_api, new_role_data["roleName"])

        resp = role_api.change_status(roleId=role_id, status="1")
        assert_jsonpath_exact(resp, "$.code", 200)

        assert_db_value(db,
            "SELECT status FROM sys_role WHERE role_id=%s",
            expected="1",
            params=(role_id,),
        )

    # ---------------------------------------------------------
    # P1 · 异常场景
    # ---------------------------------------------------------
    @allure.story("角色新增")
    @allure.title("新增角色 - 缺少必填字段应失败")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.p1
    def test_create_role_missing_required(self, role_api):
        """缺少必填字段 roleName"""
        suffix = uuid.uuid4().hex[:8]
        resp = role_api.create({
            "roleKey": f"test_missing_{suffix}",
            "roleSort": 1,
        })
        assert_jsonpath_exact(resp, "$.code", 500)

    # ---------------------------------------------------------
    # P2 · 辅助功能
    # ---------------------------------------------------------
    @allure.story("角色查询")
    @allure.title("获取角色下拉选项列表")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.p2
    def test_option_select(self, role_api):
        """角色下拉选项（用于表单）"""
        resp = role_api.option_select()
        assert_jsonpath_exact(resp, "$.code", 200)

    @allure.story("角色查询")
    @allure.title("获取部门树")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.p2
    def test_dept_tree(self, role_api):
        """获取第一个角色的部门树"""
        role_id = _first_role_id(role_api)
        resp = role_api.dept_tree(role_id)
        assert_jsonpath_exact(resp, "$.code", 200)

    @allure.story("角色授权")
    @allure.title("获取未绑定用户列表和已绑定用户列表")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.p2
    def test_auth_user_lists(self, role_api):
        """测试授权相关接口"""
        role_id = _first_role_id(role_api)

        unallocated = role_api.unallocated_user_list({"roleId": role_id})
        assert_jsonpath_exact(unallocated, "$.code", 200)

        allocated = role_api.allocated_user_list({"roleId": role_id})
        assert_jsonpath_exact(allocated, "$.code", 200)
