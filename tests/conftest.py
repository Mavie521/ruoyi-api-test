"""
API 测试专用 fixtures —— Token 管理 + 数据库 + 环境注入

使用方式:
    def test_something(login_api, role_api, db):
        info = login_api.get_info()
        user = db.query_one("SELECT * FROM sys_user WHERE user_name=%s", ("admin",))
"""
import uuid
import pytest
from config.config import ADMIN_USERNAME, ADMIN_PASSWORD
from utils.logger import logger
from utils.db_utils import DbClient
from api import LoginApi, RoleApi, SystemUserApi, DeptApi, PostApi


# ── 内部工具 ───────────────────────────────────────

def _query_role_id(role_key: str):
    """按 role_key 查询角色 ID（独立连接，清理用）"""
    try:
        c = DbClient()
        row = c.query_one("SELECT role_id FROM sys_role WHERE role_key=%s", (role_key,))
        c.close()
        return row["role_id"] if row else None
    except Exception:
        return None


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
        # 检查是否已有用户管理菜单权限
        has_menu = db.query_one(
            "SELECT 1 FROM sys_role_menu rm "
            "JOIN sys_menu m ON rm.menu_id=m.menu_id "
            "WHERE rm.role_id=%s AND m.menu_name='用户管理'", (row["role_id"],)
        )
        if not has_menu:
            logger.info(f" test_common 角色缺少用户管理菜单，删除后重建")
            role_api.delete([row["role_id"]])
        else:
            logger.info(f" 测试角色 test_common 已存在: role_id={row['role_id']}")
            role_api.data_scope({
                "roleId": row["role_id"], "dataScope": "5", "deptIds": [],
            })
            return row["role_id"]

    # 查询「用户管理」菜单及其子菜单（用于水平越权测试）
    user_mgmt = db.query_one(
        "SELECT menu_id FROM sys_menu WHERE menu_name='用户管理' AND status='0'"
    )
    sub_menus = db.query(
        "SELECT menu_id FROM sys_menu WHERE parent_id=%s AND status='0'",
        (user_mgmt["menu_id"],)
    ) if user_mgmt else []
    menu_ids = [user_mgmt["menu_id"]] if user_mgmt else []
    menu_ids += [m["menu_id"] for m in sub_menus] if sub_menus else []

    data = RoleApi.build_role_data(
        role_name="通用测试角色",
        role_key="test_common",
        role_sort=99,
        menu_ids=menu_ids,
    )
    resp = role_api.create(data)

    if resp.get("code") != 200:
        row = db.query_one(
            "SELECT role_id FROM sys_role WHERE role_key='test_common' AND del_flag='0'")
        if row:
            return row["role_id"]
        raise AssertionError(f"创建 test_common 角色失败且未查到: {resp}")

    new_row = db.query_one("SELECT role_id FROM sys_role WHERE role_key='test_common'")
    assert new_row, "test_common 角色创建后未查到"
    role_id = new_row["role_id"]
    logger.info(f" 已创建测试角色 test_common: role_id={role_id}")

    # 设置数据权限为「仅本人」(data_scope=5)，水平越权核心
    scope_resp = role_api.data_scope({
        "roleId": role_id,
        "dataScope": "5",
        "deptIds": [],
    })
    logger.info(f" test_common 数据权限设为'仅本人': code={scope_resp.get('code')}")

    return role_id


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

    # role_api / system_user_api复用是因为它们用同一个admintoken，可以共用。
    # 但non_admin_login需要的是另一个用户的token，必须新建LoginApi()调用login(username, password)拿到不同单位token
    login = LoginApi()
    token = login.login(username, password)
    assert token, f"普通用户登录失败: {username}"
    logger.info(f" 普通用户登录成功: {username}")

    yield login

    def cleanup():
        _cleanup_test_user(admin_login.token, username)
    request.addfinalizer(cleanup)


# ====================================================
# 测试数据 fixtures
# ====================================================


@pytest.fixture
def new_real_user_data(request, admin_login) -> dict:
    """生成用户数据 + API 软删除清理，避免 SQL DELETE 外键约束"""
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
        _cleanup_test_user(admin_login.token, username)
    request.addfinalizer(cleanup)


@pytest.fixture
def new_role_data(request, admin_login) -> dict:
    """生成角色数据 + API 软删除清理"""
    suffix = uuid.uuid4().hex[:8]
    role_key = f"test_role_{suffix}"
    data = RoleApi.build_role_data(
        role_name=f"测试角色_{suffix}",
        role_key=role_key,
        role_sort=1,
        menu_ids=[],
    )

    yield data

    def cleanup():
        try:
            uid_row = _query_role_id(role_key)
            if uid_row:
                ra = RoleApi()
                ra.set_token(admin_login.token)
                ra.delete([uid_row])
                logger.info(f"  清理测试角色: {role_key}")
        except Exception as e:
            logger.warning(f"  清理角色失败: {e}")
    request.addfinalizer(cleanup)
