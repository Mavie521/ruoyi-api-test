"""
部门管理模块测试用例
覆盖: 部门 CRUD（创建/修改/删除/禁启用）
"""
import uuid
import allure
import pytest
from utils.assertions import assert_jsonpath_exact, assert_db_value
from utils.logger import logger


# ── 内部工具 ────────────────────────────────────────────

def _build_dept_data(name: str, parent_id: int = 100, status: str = "0", **kwargs) -> dict:
    """构造部门请求体，消除字典硬编码重复"""
    return {"parentId": parent_id, "deptName": name, "orderNum": 0, "status": status, **kwargs}


def _find_dept_id(dept_api, name: str):
    """从部门列表中按名称查找 deptId，未找到返回 None"""
    resp = dept_api.list()
    if resp.get("code") != 200:
        return None
    data = resp.get("data", [])
    target = next((d for d in data if d.get("deptName") == name), None)
    return target["deptId"] if target else None


# ═════════════════════════════════════════════════════════
# 测试类
# ═════════════════════════════════════════════════════════

@allure.epic("若依接口测试")
@allure.feature("部门管理")
class TestDept:

    # ---------------------------------------------------------
    # P1 · 核心 CRUD
    # ---------------------------------------------------------
    @allure.story("部门 CRUD")
    @allure.title("创建部门 → 修改部门名称 → 删除部门")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.p1
    def test_dept_crud(self, dept_api):
        """部门全生命周期：创建 → 修改 → 删除"""
        suffix = uuid.uuid4().hex[:8]
        name = f"测试部门_{suffix}"

        # 1. 创建
        with allure.step("1. 创建部门"):
            resp = dept_api.create(_build_dept_data(name, leader="测试"))
            assert_jsonpath_exact(resp, "$.code", 200)
            dept_id = _find_dept_id(dept_api, name)
            assert dept_id, f"创建后列表中未找到: {name}"
            logger.info(f"   创建成功: dept_id={dept_id}")

        # 2. 修改
        with allure.step("2. 修改部门名称"):
            new_name = f"测试部门_改_{suffix}"
            dept_api.update(_build_dept_data(new_name, deptId=dept_id))
            assert _find_dept_id(dept_api, new_name), f"修改后未找到: {new_name}"
            logger.info(f"   修改成功: {name} → {new_name}")
            name = new_name

        # 3. 删除
        with allure.step("3. 删除部门"):
            dept_api.delete([dept_id])
            assert _find_dept_id(dept_api, name) is None, f"删除后仍存在: {name}"
            logger.info(f"   删除成功: dept_id={dept_id}")

    # ---------------------------------------------------------
    # P1 · 状态切换
    # ---------------------------------------------------------
    @allure.story("部门状态")
    @allure.title("禁用部门 — update status + 数据库双重验证")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.p1
    def test_disable_dept(self, dept_api, db):
        """创建 → update status='1' → DB 验证 → 清理

        若依部门没有独立 /changeStatus 端点，禁启用走 update 改 status 字段。
        """
        suffix = uuid.uuid4().hex[:8]
        name = f"禁用部_{suffix}"

        with allure.step("1. 创建部门"):
            dept_api.create(_build_dept_data(name))
            dept_id = _find_dept_id(dept_api, name)
            assert dept_id, f"创建后未找到: {name}"

        with allure.step("2. 禁用（update status='1'）"):
            dept_api.update(_build_dept_data(name, deptId=dept_id, status="1"))

        with allure.step("3. 数据库验证 status='1'"):
            assert_db_value(db,
                "SELECT status FROM sys_dept WHERE dept_id=%s",
                expected="1", params=(dept_id,),
            )

        with allure.step("4. 清理"):
            dept_api.delete([dept_id])
