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
        with allure.step("请求角色分页列表"):
            resp = role_api.list()
        with allure.step("验证返回 200"):
            assert_jsonpath_exact(resp, "$.code", 200)

    @allure.story("角色查询")
    @allure.title("获取角色详情")
    @allure.severity(allure.severity_level.BLOCKER)
    @pytest.mark.p0
    def test_get_role_detail(self, role_api):
        """获取任意一个角色详情"""
        with allure.step("获取首个角色 ID"):
            role_id = _first_role_id(role_api)
        with allure.step(f"查询角色 {role_id} 详情"):
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
        with allure.step("创建新角色"):
            resp = role_api.create(new_role_data)
            assert_jsonpath_exact(resp, "$.code", 200)
        with allure.step("数据库验证角色已落盘"):
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
        with allure.step("创建待编辑的角色"):
            role_api.create(new_role_data)
            role_id = _find_role_id(role_api, new_role_data["roleName"])

        with allure.step("编辑角色名称"):
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

        with allure.step("数据库验证角色名已更新"):
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
        with allure.step("创建待删除的角色"):
            role_api.create(new_role_data)
            role_id = _find_role_id(role_api, new_role_data["roleName"])

        with allure.step("软删除角色"):
            resp = role_api.delete([role_id])
            assert_jsonpath_exact(resp, "$.code", 200)

        with allure.step("数据库验证 del_flag='2'"):
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
        with allure.step("创建角色"):
            role_api.create(new_role_data)
            role_id = _find_role_id(role_api, new_role_data["roleName"])

        with allure.step("禁用角色"):
            resp = role_api.change_status(roleId=role_id, status="1")
            assert_jsonpath_exact(resp, "$.code", 200)

        with allure.step("数据库验证 status='1'"):
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
        with allure.step("发送缺少 roleName 的创建请求"):
            suffix = uuid.uuid4().hex[:8]
            resp = role_api.create({
                "roleKey": f"test_missing_{suffix}",
                "roleSort": 1,
            })
        with allure.step("验证返回 500（参数校验失败）"):
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
        with allure.step("请求角色下拉选项"):
            resp = role_api.option_select()
            assert_jsonpath_exact(resp, "$.code", 200)

    @allure.story("角色查询")
    @allure.title("获取部门树")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.p2
    def test_dept_tree(self, role_api):
        """获取第一个角色的部门树"""
        with allure.step("获取首个角色 ID"):
            role_id = _first_role_id(role_api)
        with allure.step(f"查询角色 {role_id} 的部门树"):
            resp = role_api.dept_tree(role_id)
            assert_jsonpath_exact(resp, "$.code", 200)

    @allure.story("角色授权")
    @allure.title("获取未绑定用户列表和已绑定用户列表")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.p2
    def test_auth_user_lists(self, role_api):
        """测试授权相关接口"""
        with allure.step("获取首个角色 ID"):
            role_id = _first_role_id(role_api)

        with allure.step("查询未分配用户列表"):
            unallocated = role_api.unallocated_user_list({"roleId": role_id})
            assert_jsonpath_exact(unallocated, "$.code", 200)

        with allure.step("查询已分配用户列表"):
            allocated = role_api.allocated_user_list({"roleId": role_id})
            assert_jsonpath_exact(allocated, "$.code", 200)

    # ---------------------------------------------------------
    # P1 · 幂等性
    # ---------------------------------------------------------
    @allure.story("接口幂等")
    @allure.title("POST 非幂等 — 重复创建同 roleKey 不应返回 500，且不产生脏数据")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.p1
    @pytest.mark.xfail(
        reason="若依已知缺陷：重复创建返回 500 而非 4xx 业务错误码。DB 唯一索引兜底，无脏数据。"
    )
    def test_create_role_idempotent(self, role_api, new_role_data, db):
        """幂等性验证：同一个 roleKey 创建两次，第二次应返回明确业务错误，数据库无重复记录

        企业场景：用户双击提交、网关超时重试，服务端不可崩溃或产生脏数据。
        若依通过 role_key 唯一索引兜底，本用例验证防御层有效。

        当前状态（xfail）：若依返回 code=500 + msg="角色名称已存在"。
        虽然 DB 层面唯一索引防住了脏数据，但 HTTP 层应返回 4xx 业务错误码而非 500。
        面试可讲：'我通过测试发现了若依的幂等返回码不规范的缺陷'。
        """
        with allure.step("1. 首次创建角色"):
            resp1 = role_api.create(new_role_data)
            assert resp1.get("code") == 200, f"首次创建应成功: {resp1}"

        with allure.step("2. 重复创建同一 roleKey"):
            resp2 = role_api.create(new_role_data)

        with allure.step("3. 验证不崩 500，返回明确业务错误"):
            assert resp2.get("code") != 500, (
                f"❌ 幂等缺陷！重复创建同 roleKey 不应返回 500\n"
                f"  响应: {resp2}\n"
                f"  预期: 业务错误码（如 4xx），实际: 500"
            )

        with allure.step("4. 数据库验证无重复脏数据"):
            count = db.query(
                "SELECT COUNT(*) AS cnt FROM sys_role "
                "WHERE role_key=%s AND del_flag='0'",
                (new_role_data["roleKey"],),
            )
            actual = count[0]["cnt"] if count else 0
            assert actual == 1, (
                f"❌ 幂等缺陷！同 role_key 产生了 {actual} 条记录（预期 1 条）\n"
                f"  role_key: {new_role_data['roleKey']}"
            )
