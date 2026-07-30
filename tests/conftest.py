"""
API 测试专用 fixtures —— Token 管理 + 数据库 + 环境注入

使用方式:
    def test_something(login_api, role_api, db):
        info = login_api.get_info()
        user = db.query_one("SELECT * FROM sys_user WHERE user_name=%s", ("admin",))
"""
import uuid
import mysql.connector
import pytest
from config.config import ADMIN_USERNAME, ADMIN_PASSWORD
from utils.logger import logger
from utils.db_utils import DbClient
from api import LoginApi, RoleApi, SystemUserApi, DeptApi, PostApi


# ── 内部工具 ───────────────────────────────────────

def _cleanup_test_user(admin_token: str, username: str):
    """通过 API 软删除测试用户（不触发外键约束）"""
    try:
        c = DbClient()
        uid_row = c.query_one("SELECT user_id FROM sys_user WHERE user_name=%s", (username,))
        c.close()
        if uid_row:
            ua = SystemUserApi()
            ua.set_token(admin_token)
            ua.delete([uid_row[0]])
            logger.info(f"  清理测试用户: {username}")
    except Exception as e:
        logger.warning(f"  清理测试用户失败: {e}")


# ── fixtures ───────────────────────────────────────

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


@pytest.fixture(scope="session")
def dept_api(admin_login) -> DeptApi:
    """已登录的 DeptApi（部门管理）"""
    api = DeptApi()
    api.set_token(admin_login.token)
    return api


@pytest.fixture(scope="session")
def post_api(admin_login) -> PostApi:
    """已登录的 PostApi（岗位管理）"""
    api = PostApi()
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
    assert_db_value(db, "SELECT status FROM sys_role WHERE role_id=%s", expected="0", params=(1,))
    """
    client = DbClient()
    yield client
    client.close()


# ====================================================
# 非管理员登录 fixture（权限测试用）
# ====================================================

@pytest.fixture(scope="session")
def non_admin_role(role_api, db):
    """幂等创建通用测试角色（session 级别，仅执行一次）"""
    row = db.query_one(
        "SELECT role_id FROM sys_role WHERE role_key='test_common' AND del_flag='0'"
    )
    if row:
        logger.info(f" 测试角色 test_common 已存在: role_id={row[0]}")
        return row[0]

    data = RoleApi.build_role_data(
        role_name="通用测试角色",
        role_key="test_common",
        role_sort=99,
        menu_ids=[],
    )
    resp = role_api.create(data)
    assert resp.get("code") == 200, f"创建 test_common 角色失败: {resp}"

    new_row = db.query_one("SELECT role_id FROM sys_role WHERE role_key='test_common'")
    assert new_row, "test_common 角色创建后未查到"
    logger.info(f" 已创建测试角色 test_common: role_id={new_row[0]}")
    return new_row[0]


@pytest.fixture(scope="session")
def non_admin_login(request, admin_login, non_admin_role, system_user_api):
    """普通用户登录 fixture，返回带普通 token 的 LoginApi"""
    suffix = uuid.uuid4().hex[:8]
    username = f"perm_test_{suffix}"
    password = "test123456"

    data = SystemUserApi.build_user_data(
        username=username, password=password,
        nick_name=f"权限测试_{suffix}",
        role_ids=[non_admin_role],
    )
    resp = system_user_api.create(data)
    assert resp.get("code") == 200, f"创建权限测试用户失败: {resp}"
    logger.info(f" 创建权限测试用户: {username}")

    login = LoginApi()
    token = login.login(username, password)
    assert token, f"普通用户登录失败: {username}"
    logger.info(f" 普通用户登录成功: {username}")

    yield login

    def cleanup():
        _cleanup_test_user(admin_login.token, username)
    request.addfinalizer(cleanup)


@pytest.fixture
def non_admin_target_user(request, admin_login, non_admin_role, system_user_api):
    """为越权删除测试准备的第二个测试用户（function 级别）"""
    suffix = uuid.uuid4().hex[:8]
    username = f"perm_target_{suffix}"

    data = SystemUserApi.build_user_data(
        username=username,
        nick_name=f"删除目标_{suffix}",
        role_ids=[non_admin_role],
    )
    resp = system_user_api.create(data)
    assert resp.get("code") == 200, f"创建删除目标用户失败: {resp}"

    yield username

    def cleanup():
        _cleanup_test_user(admin_login.token, username)

    request.addfinalizer(cleanup)


# ====================================================
# 测试数据 fixtures
# ====================================================


@pytest.fixture
def new_real_user_data(request, db) -> dict:
    """生成真实用户数据，用例结束后自动清理（/system/user 需要 userName 等）"""
    suffix = uuid.uuid4().hex[:8]
    username = f"test_real_{suffix}"
    data = SystemUserApi.build_user_data(
        username=username,
        nick_name=f"测试用户_{suffix}",
        email=f"real_{suffix}@ruoyi.com",
        phone=f"138{suffix[:8].zfill(8)}",
        remark="接口测试-真实用户",
    )

    yield data

    def cleanup():
        try:
            db.execute("DELETE FROM sys_user WHERE user_name=%s", (username,))
            logger.info(f"  清理测试用户: {username}")
        except mysql.connector.Error as e:
            logger.warning(f"  清理用户失败（可能已被删除）: {e}")

    request.addfinalizer(cleanup)


@pytest.fixture
def new_role_data(request, db) -> dict:
    """
    生成新角色数据
    自动清理：用例结束后删除创建的角色（防止测试数据污染）
    """
    suffix = uuid.uuid4().hex[:8]
    role_key = f"test_role_{suffix}"
    data = RoleApi.build_role_data(
        role_name=f"测试角色_{suffix}",
        role_key=role_key,
        role_sort=1,
        menu_ids=[],
    )

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
