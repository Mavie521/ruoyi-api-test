"""
业务流程测试 —— 用户完整生命周期
模拟真实业务：创建用户 → 创建角色 → 分配角色 → 验证 → 清理

这是面试官最想看到的"业务场景覆盖"类测试
"""
import allure
import pytest
from utils.logger import logger


@allure.epic("若依接口测试")
@allure.feature("业务流程")
class TestBusinessFlow:

    @allure.story("用户角色生命周期")
    @allure.title("创建用户→创建角色→分配角色→验证→清理")
    @allure.severity(allure.severity_level.BLOCKER)
    @pytest.mark.smoke
    def test_user_role_full_lifecycle(self, system_user_api, role_api, db):
        """完整的用户+角色分配业务流程"""
        import time
        suffix = str(int(time.time() * 1000))[-6:]

        # =========================================================
        # Step 1: 创建新用户
        # =========================================================
        with allure.step("1. 创建新用户"):
            username = f"flow_user_{suffix}"
            user_data = {
                "userName": username,
                "nickName": f"流程用户_{suffix}",
                "password": "123456",
                "deptId": 103,
                "email": f"{username}@ruoyi.com",
                "phonenumber": f"138{suffix[:8].zfill(8)}",
                "sex": "0",
                "status": "0",
                "postIds": [],
                "roleIds": [],
                "remark": "业务流程测试-自动创建",
            }
            resp = system_user_api.create_user(user_data)
            assert resp.get("code") == 200, f"创建用户失败: {resp}"
            logger.info(f"   用户 {username} 创建成功")

            # 从列表中找到新建用户的 ID
            list_resp = system_user_api.list_users({"pageSize": 100})
            rows = list_resp.get("rows", [])
            user = next((u for u in rows if u.get("userName") == username), None)
            assert user is not None, "创建后未在列表中找到用户"
            user_id = user.get("userId")
            logger.info(f"  用户ID: {user_id}")

            # 数据库验证
            db.assert_exists(
                "SELECT user_id FROM sys_user WHERE user_id=%s AND del_flag='0'",
                params=(user_id,),
            )
            logger.info(f"   数据库已确认用户存在")

        # =========================================================
        # Step 2: 创建新角色
        # =========================================================
        with allure.step("2. 创建新角色"):
            role_name = f"flow_role_{suffix}"
            role_key = f"flow_role_key_{suffix}"
            role_data = {
                "roleName": role_name,
                "roleKey": role_key,
                "roleSort": 1,
                "status": "0",
                "menuIds": [],
            }
            resp = role_api.create_role(role_data)
            assert resp.get("code") == 200, f"创建角色失败: {resp}"
            logger.info(f"   角色 {role_name} 创建成功")

            # 从列表中找到新建角色的 ID
            list_resp = role_api.list_roles({"pageSize": 100})
            rows = list_resp.get("rows", [])
            role = next((r for r in rows if r.get("roleName") == role_name), None)
            assert role is not None, "创建后未在列表中找到角色"
            role_id = role.get("roleId")
            logger.info(f"  角色ID: {role_id}")

            # 数据库验证
            db.assert_value(
                "SELECT role_name FROM sys_role WHERE role_id=%s",
                expected=role_name,
                params=(role_id,),
            )

        # =========================================================
        # Step 3: 给用户分配角色
        # =========================================================
        with allure.step("3. 给用户分配角色"):
            # 修改用户，赋予角色（注意：不要传 password，否则会覆盖为明文）
            update_data = {"userId": user_id, "userName": username, "roleIds": [role_id]}
            resp = system_user_api.update_user(update_data)
            assert resp.get("code") == 200, f"分配角色失败: {resp}"

            # 数据库验证：确认用户-角色关联
            db.assert_exists(
                "SELECT * FROM sys_user_role WHERE user_id=%s AND role_id=%s",
                params=(user_id, role_id),
            )
            logger.info(f"   用户 {user_id} 已分配角色 {role_id}")

        # =========================================================
        # Step 4: 验证新用户可以登录
        # =========================================================
        with allure.step("4. 验证新用户能登录"):
            from api import LoginApi
            new_login = LoginApi()
            token = new_login.login(username, "123456")
            assert token is not None, f"新用户 {username} 登录失败"
            logger.info(f"   新用户 {username} 登录成功")

            # 验证能查到自己的信息
            info = new_login.get_info()
            assert info.get("code") == 200
            logger.info(f"   新用户可正常查询个人信息")

        # =========================================================
        # Step 5: 清理数据（删除用户和角色）
        # =========================================================
        with allure.step("5. 清理测试数据"):
            # 删除用户
            resp = system_user_api.delete_user(user_id)
            assert resp.get("code") == 200, f"删除用户失败: {resp}"
            db.assert_value(
                "SELECT del_flag FROM sys_user WHERE user_id=%s",
                expected="2",
                params=(user_id,),
            )
            logger.info(f"   用户 {username} 已逻辑删除")

            # 删除角色
            resp = role_api.delete_role([role_id])
            assert resp.get("code") == 200, f"删除角色失败: {resp}"
            db.assert_value(
                "SELECT del_flag FROM sys_role WHERE role_id=%s",
                expected="2",
                params=(role_id,),
            )
            logger.info(f"   角色 {role_name} 已逻辑删除")

        logger.info("=" * 50)
        logger.info(" 用户角色生命周期测试全部通过")
