"""
角色管理模块 API 封装
对应接口文档: sys-role-controller
"""
from typing import Optional
import allure
from .base_api import BaseApi


class RoleApi(BaseApi):
    """角色管理相关接口"""

    # ---------------------------------------------------------
    # 基础 CRUD
    # ---------------------------------------------------------
    @allure.step("查询角色列表")
    def list_roles(self, params: dict = None) -> dict:
        """
        查询角色列表（支持分页、条件过滤）
        GET /system/role/list
        """
        res = self.get("/system/role/list", params=params or {})
        return res.json()

    @allure.step("获取角色详情")
    def get_role(self, role_id: int) -> dict:
        """
        获取角色详情
        GET /system/role/{roleId}
        """
        res = self.get(f"/system/role/{role_id}")
        return res.json()

    @allure.step("新增角色")
    def create_role(self, role_data: dict) -> dict:
        """
        新增角色
        POST /system/role
        """
        res = self.post("/system/role", json=role_data)
        return res.json()

    @allure.step("编辑角色")
    def update_role(self, role_data: dict) -> dict:
        """
        编辑角色
        PUT /system/role
        """
        res = self.put("/system/role", json=role_data)
        return res.json()

    @allure.step("删除角色")
    def delete_role(self, role_ids: list) -> dict:
        """
        删除角色（支持批量）
        DELETE /system/role/{roleIds}
        """
        path = f"/system/role/{','.join(str(rid) for rid in role_ids)}"
        res = self.delete(path)
        return res.json()

    # ---------------------------------------------------------
    # 角色状态 & 权限
    # ---------------------------------------------------------
    @allure.step("修改角色状态")
    def change_status(self, role_data: dict) -> dict:
        """
        启用/禁用角色
        PUT /system/role/changeStatus
        """
        res = self.put("/system/role/changeStatus", json=role_data)
        return res.json()

    @allure.step("分配数据权限")
    def data_scope(self, role_data: dict) -> dict:
        """
        分配数据权限（菜单权限）
        PUT /system/role/dataScope
        """
        res = self.put("/system/role/dataScope", json=role_data)
        return res.json()

    # ---------------------------------------------------------
    # 角色选项 & 部门树
    # ---------------------------------------------------------
    @allure.step("获取角色下拉选项")
    def option_select(self) -> dict:
        """
        角色下拉选项（用于表单选择）
        GET /system/role/optionselect
        """
        res = self.get("/system/role/optionselect")
        return res.json()

    @allure.step("获取部门树")
    def dept_tree(self, role_id: int) -> dict:
        """
        获取部门树（用于数据权限设置）
        GET /system/role/deptTree/{roleId}
        """
        res = self.get(f"/system/role/deptTree/{role_id}")
        return res.json()

    # ---------------------------------------------------------
    # 用户授权
    # ---------------------------------------------------------
    @allure.step("取消用户授权")
    def cancel_auth_user(self, user_id: int, role_id: int) -> dict:
        """
        取消单个用户的角色授权
        PUT /system/role/authUser/cancel
        """
        body = {"userId": user_id, "roleId": role_id}
        res = self.put("/system/role/authUser/cancel", json=body)
        return res.json()

    @allure.step("获取未绑定用户列表")
    def unallocated_user_list(self, params: dict = None) -> dict:
        """
        获取尚未绑定该角色的用户列表
        GET /system/role/authUser/unallocatedList
        """
        res = self.get("/system/role/authUser/unallocatedList", params=params or {})
        return res.json()

    @allure.step("获取已绑定用户列表")
    def allocated_user_list(self, params: dict = None) -> dict:
        """
        获取已绑定该角色的用户列表
        GET /system/role/authUser/allocatedList
        """
        res = self.get("/system/role/authUser/allocatedList", params=params or {})
        return res.json()

    # ---------------------------------------------------------
    # 业务辅助方法
    # ---------------------------------------------------------
    def build_role_data(
        self, role_name: str, role_key: str,
        role_id: Optional[int] = None, **extra
    ) -> dict:
        """构造角色数据（role_name + role_key 为必填）"""
        data = {
            "roleName": role_name,
            "roleKey": role_key,
            "roleSort": extra.get("role_sort", 1),
            "status": extra.get("status", "0"),
        }
        if role_id is not None:
            data["roleId"] = role_id
        if "menu_ids" in extra:
            data["menuIds"] = extra["menu_ids"] or []
        return data
