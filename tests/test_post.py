"""
岗位管理模块测试用例
覆盖: 岗位 CRUD（创建/修改/删除/禁启用）
"""
import uuid
import allure
import pytest
from utils.assertions import assert_jsonpath_exact, assert_db_value
from utils.logger import logger


# ── 内部工具 ────────────────────────────────────────────

def _build_post_data(name: str, code: str, sort: int = 0, status: str = "0", **kwargs) -> dict:
    """构造岗位请求体，消除字典硬编码重复"""
    return {"postName": name, "postCode": code, "postSort": sort, "status": status, **kwargs}


def _find_post_id(post_api, name: str):
    """从岗位列表中按名称查找 postId，未找到返回 None"""
    resp = post_api.list({"pageNum": 1, "pageSize": 100})
    if resp.get("code") != 200:
        return None
    rows = resp.get("rows", [])
    target = next((r for r in rows if r.get("postName") == name), None)
    return target["postId"] if target else None


# ═════════════════════════════════════════════════════════
# 测试类
# ═════════════════════════════════════════════════════════

@allure.epic("若依接口测试")
@allure.feature("岗位管理")
class TestPost:

    # ---------------------------------------------------------
    # P1 · 核心 CRUD
    # ---------------------------------------------------------
    @allure.story("岗位 CRUD")
    @allure.title("创建岗位 → 修改岗位名称 → 删除岗位")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.p1
    def test_post_crud(self, post_api):
        """岗位全生命周期：创建 → 修改 → 删除"""
        suffix = uuid.uuid4().hex[:8]
        name = f"测试岗位_{suffix}"
        code = f"test_{suffix}"

        # 1. 创建
        with allure.step("1. 创建岗位"):
            resp = post_api.create(_build_post_data(name, code))
            assert_jsonpath_exact(resp, "$.code", 200)
            post_id = _find_post_id(post_api, name)
            assert post_id, f"创建后列表中未找到: {name}"
            logger.info(f"   创建成功: post_id={post_id}")

        # 2. 修改
        with allure.step("2. 修改岗位名称"):
            new_name = f"测试岗位_改_{suffix}"
            post_api.update(_build_post_data(new_name, code, postId=post_id))
            assert _find_post_id(post_api, new_name), f"修改后未找到: {new_name}"
            logger.info(f"   修改成功: {name} → {new_name}")
            name = new_name

        # 3. 删除
        with allure.step("3. 删除岗位"):
            post_api.delete([post_id])
            assert _find_post_id(post_api, name) is None, f"删除后仍存在: {name}"
            logger.info(f"   删除成功: post_id={post_id}")

    # ---------------------------------------------------------
    # P1 · 状态切换
    # ---------------------------------------------------------
    @allure.story("岗位状态")
    @allure.title("禁用岗位 — update status + 数据库双重验证")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.p1
    def test_disable_post(self, post_api, db):
        """创建 → update status='1' → DB 验证 → 清理

        若依岗位没有独立 /changeStatus 端点，禁启用走 update 改 status 字段。
        """
        suffix = uuid.uuid4().hex[:8]
        name = f"禁用岗_{suffix}"
        code = f"dis_{suffix}"

        with allure.step("1. 创建岗位"):
            post_api.create(_build_post_data(name, code))
            post_id = _find_post_id(post_api, name)
            assert post_id, f"创建后未找到: {name}"

        with allure.step("2. 禁用（update status='1'）"):
            post_api.update(_build_post_data(name, code, postId=post_id, status="1"))

        with allure.step("3. 数据库验证 status='1'"):
            assert_db_value(db,
                "SELECT status FROM sys_post WHERE post_id=%s",
                expected="1", params=(post_id,),
            )

        with allure.step("4. 清理"):
            post_api.delete([post_id])
