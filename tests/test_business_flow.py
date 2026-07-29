"""
业务流程测试 —— 用户完整生命周期
模拟真实业务：创建用户 → 创建角色 → 分配角色 → 验证 → 清理

这是面试官最想看到的"业务场景覆盖"类测试
"""
import time
import allure
import pytest
from api import LoginApi
from utils.logger import logger
from utils.assertions import assert_jsonpath_exact, assert_db_value, assert_db_exists


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
        suffix = str(int(time.time() * 1000))[-6:]

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

            # 从数据库查询用户 ID
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
