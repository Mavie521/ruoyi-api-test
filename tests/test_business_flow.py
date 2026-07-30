"""
业务流程测试 —— 用户完整生命周期
模拟真实业务：创建用户 → 创建角色 → 分配角色 → 验证 → 清理

这是面试官最想看到的"业务场景覆盖"类测试
"""
import uuid
import allure
import pytest
from api import LoginApi
from utils.logger import logger
from utils.assertions import assert_jsonpath_exact, assert_db_value, assert_db_exists


def _first_id(api, key="roleId"):
    """从分页列表中提取第一个 ID（不存在则 skip）"""
    resp = api.list({"pageNum": 1, "pageSize": 1})
    rows = resp.get("rows", [])
    if not rows:
        pytest.skip(f"{api.resource} 列表为空")
    return rows[0].get(key)


def _first_dept_id(dept_api):
    """从部门树中提取第一个部门 ID（不存在则 skip）"""
    resp = dept_api.list()
    data = resp.get("data", [])
    if not data:
        pytest.skip("部门列表为空")
    return data[0].get("deptId")


@allure.epic("若依接口测试")
@allure.feature("业务流程")
class TestBusinessFlow:
    """业务场景测试：用户角色完整生命周期"""

    @allure.story("用户角色生命周期")
    @allure.title("创建用户→创建角色→分配角色→验证→清理")
    @allure.severity(allure.severity_level.BLOCKER)
    @pytest.mark.p0
    def test_user_role_full_lifecycle(self, system_user_api, role_api, db):
        """完整的用户+角色分配业务流程"""
        suffix = uuid.uuid4().hex[:8]

        # Step 1: 创建新用户
        with allure.step("1. 创建新用户"):
            username = f"flow_user_{suffix}"
            user_data = system_user_api.build_user_data(
                username=username,
                nick_name=f"流程用户_{suffix}",
                email=f"{username}@ruoyi.com",
                phone=f"138{suffix[:8].zfill(8)}",
                remark="业务流程测试-自动创建",
            )
            resp = system_user_api.create(user_data)
            assert_jsonpath_exact(resp, "$.code", 200)
            logger.info(f"   用户 {username} 创建成功")

            #若依的创建接口不返回新用户的 ID。但后面分配角色需要 userId，所以必须查数据库 从数据库查询用户 ID
            row = db.query_one("SELECT user_id FROM sys_user WHERE user_name=%s", (username,))
            if row is None:
                pytest.skip("创建后未在数据库中找到用户")
            user_id = row["user_id"]
            logger.info(f"  用户ID: {user_id}")

            # 数据库验证
            assert_db_exists(db,
                "SELECT user_id FROM sys_user WHERE user_id=%s AND del_flag='0'",
                params=(user_id,),
            )
            logger.info("   数据库已确认用户存在")

        # Step 2: 创建新角色
        with allure.step("2. 创建新角色"):
            role_name = f"flow_role_{suffix}"
            role_key = f"flow_role_key_{suffix}"
            role_data = role_api.build_role_data(
                role_name=role_name,
                role_key=role_key,
                role_sort=1,
            )
            resp = role_api.create(role_data)
            assert_jsonpath_exact(resp, "$.code", 200)
            logger.info(f"   角色 {role_name} 创建成功")

            # 从数据库查询角色 ID
            row = db.query_one("SELECT role_id FROM sys_role WHERE role_key=%s", (role_key,))
            if row is None:
                pytest.skip("创建后未在数据库中找到角色")
            role_id = row["role_id"]
            logger.info(f"  角色ID: {role_id}")

            # 数据库验证
            assert_db_value(db,
                "SELECT role_name FROM sys_role WHERE role_id=%s",
                expected=role_name,
                params=(role_id,),
            )

        # Step 3: 给用户分配角色
        with allure.step("3. 给用户分配角色"):
            update_data = {"userId": user_id, "userName": username, "roleIds": [role_id]}
            resp = system_user_api.update(update_data)
            assert_jsonpath_exact(resp, "$.code", 200)
            assert_db_exists(db,
                "SELECT * FROM sys_user_role WHERE user_id=%s AND role_id=%s",
                params=(user_id, role_id),
            )
            logger.info(f"   用户 {user_id} 已分配角色 {role_id}")

        # Step 4: 验证新用户可以登录
        with allure.step("4. 验证新用户能登录"):
            new_login = LoginApi()
            token = new_login.login(username, "123456")
            assert token is not None, f"新用户 {username} 登录失败"
            logger.info(f"   新用户 {username} 登录成功")
            info = new_login.get_info()
            assert_jsonpath_exact(info, "$.code", 200)
            logger.info("   新用户可正常查询个人信息")

        # Step 5: 清理数据
        with allure.step("5. 清理测试数据"):
            resp = system_user_api.delete(user_id)
            assert_jsonpath_exact(resp, "$.code", 200)
            assert_db_value(db,
                "SELECT del_flag FROM sys_user WHERE user_id=%s",
                expected="2",
                params=(user_id,),
            )
            logger.info(f"   用户 {username} 已逻辑删除")
            resp = role_api.delete([role_id])
            assert_jsonpath_exact(resp, "$.code", 200)
            assert_db_value(db,
                "SELECT del_flag FROM sys_role WHERE role_id=%s",
                expected="2",
                params=(role_id,),
            )
            logger.info(f"   角色 {role_name} 已逻辑删除")

        logger.info("=" * 50)
        logger.info(" 用户角色生命周期测试全部通过")

    @allure.story("RBAC权限链")
    @allure.title("角色→菜单→路由 权限链验证")
    @allure.severity(allure.severity_level.BLOCKER)
    @pytest.mark.p0
    def test_rbac_permission_chain(self, admin_login, role_api, system_user_api):
        """验证 RBAC 权限模型: 角色有菜单→用户有角色→用户有路由"""
        role_id = _first_id(role_api, "roleId")
        user_id = _first_id(system_user_api, "userId")

        with allure.step("1. 验证角色拥有菜单"):
            menus = role_api.role_menu_treeselect(role_id)
            assert_jsonpath_exact(menus, "$.code", 200)
            menu_list = menus.get("menus", [])
            assert len(menu_list) > 0, f"角色 {role_id} 应拥有菜单权限"
            logger.info(f"   角色 {role_id} 菜单数: {len(menu_list)}")

        with allure.step("2. 验证用户拥有角色"):
            roles = system_user_api.auth_role(user_id)
            assert_jsonpath_exact(roles, "$.code", 200)
            user_roles = roles.get("roles", [])
            assert len(user_roles) > 0, f"用户 {user_id} 应至少拥有一个角色"
            logger.info(f"   用户 {user_id} 角色数: {len(user_roles)}")

        with allure.step("3. 验证用户路由包含菜单"):
            routers = admin_login.get_routers()
            assert_jsonpath_exact(routers, "$.code", 200)
            router_data = routers.get("data", [])
            assert len(router_data) > 0, "用户应有可访问的路由"
            logger.info(f"   顶级路由数: {len(router_data)}")

        logger.info("=" * 50)
        logger.info(" RBAC 权限链验证全部通过")

    @allure.story("组织架构")
    @allure.title("部门树→岗位→用户 组织架构验证")
    @allure.severity(allure.severity_level.BLOCKER)
    @pytest.mark.p0
    def test_dept_post_hierarchy(self, dept_api, post_api, role_api):
        """验证组织架构: 部门层级→岗位列表→角色部门树"""
        with allure.step("1. 验证部门列表非空并获取首个部门"):
            depts = dept_api.list()
            assert_jsonpath_exact(depts, "$.code", 200)
            dept_id = _first_dept_id(dept_api)
            logger.info(f"   部门数: {len(depts.get('data', []))}, 首个部门ID: {dept_id}")

        with allure.step("2. 验证部门详情可查"):
            detail = dept_api.get(dept_id)
            assert_jsonpath_exact(detail, "$.code", 200)
            dept_info = detail.get("data", {})
            assert dept_info.get("deptName"), "部门应有名称"
            logger.info(f"   部门 {dept_id}: {dept_info.get('deptName')}")

        with allure.step("3. 验证岗位列表非空并获取首个岗位"):
            posts = post_api.list({"pageNum": 1, "pageSize": 10})
            assert_jsonpath_exact(posts, "$.code", 200)
            post_rows = posts.get("rows", [])
            assert len(post_rows) > 0, "系统应有至少一个岗位"
            post_id = _first_id(post_api, "postId")
            logger.info(f"   岗位数: {len(post_rows)}, 首个岗位ID: {post_id}")

        with allure.step("4. 验证角色部门树"):
            role_id = _first_id(role_api, "roleId")
            tree = role_api.dept_tree(role_id)
            assert_jsonpath_exact(tree, "$.code", 200)
            dept_list = tree.get("depts", [])
            assert len(dept_list) > 0, f"角色 {role_id} 应有部门树数据"
            logger.info(f"   角色 {role_id} 部门树节点: {len(dept_list)}")

        logger.info("=" * 50)
        logger.info(" 组织架构验证全部通过")
