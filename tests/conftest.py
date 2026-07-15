"""
API 测试专用 fixtures —— Token 管理 + 数据库 + 环境注入

使用方式:
    def test_something(login_api, user_api, db):
        info = login_api.get_info()
        user = db.query_one("SELECT * FROM sys_user WHERE user_name=%s", ("admin",))
"""
import time
import mysql.connector
import pytest
from config.config import ADMIN_USERNAME, ADMIN_PASSWORD
from utils.logger import logger
from utils.db_utils import DbClient
from api import LoginApi, UserApi, RoleApi, SystemUserApi


@pytest.fixture(scope="session")
def admin_login() -> LoginApi:
    """
    管理员登录 fixture
    - 返回已登录的 LoginApi 实例（token 已设置好）
    - session 级别，整个测试会话只登录一次
    """
    api = LoginApi()
    token = api.login(ADMIN_USERNAME, ADMIN_PASSWORD)
    assert token, f"管理员登录失败！请检查 {ADMIN_USERNAME}@BASE_URL"
    logger.info(" 管理员登录成功，token 已获取")
    return api


@pytest.fixture(scope="session")
def login_api(admin_login) -> LoginApi:
    """已登录的 LoginApi"""
    return admin_login


@pytest.fixture(scope="session")
def user_api(admin_login) -> UserApi:
    """已登录的 UserApi（继承 token）"""
    api = UserApi()
    api.set_token(admin_login.token)
    return api


@pytest.fixture(scope="session")
def role_api(admin_login) -> RoleApi:
    """已登录的 RoleApi（继承 token）"""
    api = RoleApi()
    api.set_token(admin_login.token)
    return api


@pytest.fixture(scope="session")
def system_user_api(admin_login) -> SystemUserApi:
    """已登录的 SystemUserApi（真实用户管理）"""
    api = SystemUserApi()
    api.set_token(admin_login.token)
    return api


# ====================================================
# 数据库 fixture
# ====================================================
@pytest.fixture(scope="session")
def db():
    """
    数据库客户端 fixture
    测试函数中直接使用: def test_xxx(db):
    db.assert_value("SELECT status FROM sys_role WHERE role_id=%s", expected="0", params=(1,))
    """
    client = DbClient()
    yield client
    client.close()


# ====================================================
# 测试数据 fixtures
# ====================================================


@pytest.fixture
def new_real_user_data() -> dict:
    """生成真实用户数据（/system/user 需要 userName 等）"""
    suffix = str(int(time.time() * 1000))[-6:]
    return {
        "userName": f"test_real_{suffix}",
        "nickName": f"测试用户_{suffix}",
        "password": "123456",
        "deptId": 103,
        "email": f"real_{suffix}@ruoyi.com",
        "phonenumber": f"138{suffix[:8].zfill(8)}",
        "sex": "0",
        "status": "0",
        "postIds": [],
        "roleIds": [],
        "remark": "接口测试-真实用户",
    }


@pytest.fixture
def new_role_data(request, db) -> dict:
    """
    生成新角色数据
    自动清理：用例结束后删除创建的角色（防止测试数据污染）
    """
    suffix = str(int(time.time() * 1000))[-6:]
    role_key = f"test_role_{suffix}"
    data = {
        "roleName": f"测试角色_{suffix}",
        "roleKey": role_key,
        "roleSort": 1,
        "status": "0",
        "menuIds": [],
    }

    # yield 之前的代码在测试前执行
    yield data

    # === 【新增】测试后自动清理创建的角色 ===
    def cleanup():
        try:
            db.execute("DELETE FROM sys_role WHERE role_key=%s", (role_key,))
            logger.info(f"  清理测试角色: {role_key}")
        except mysql.connector.Error as e:
            logger.warning(f"  清理失败（可能已被删除）: {e}")

    # 注册清理函数，确保即使断言失败也会执行
    request.addfinalizer(cleanup)
