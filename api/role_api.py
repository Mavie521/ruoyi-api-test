"""角色管理模块 API"""
from typing import Optional
from .base_api import BaseApi


class RoleApi(BaseApi):
    resource = "/system/role"

    # ── 角色特有的方法 ──

    def option_select(self) -> dict:
        return self._call(method="GET", path=f"{self.resource}/optionselect")

    def data_scope(self, role_data: dict) -> dict:
        """修改角色数据权限范围"""
        return self._call(method="PUT", path=f"{self.resource}/dataScope",
                          json=role_data)

    def dept_tree(self, role_id: int) -> dict:
        return self._call(method="GET", path=f"{self.resource}/deptTree/{role_id}")

    def allocated_user_list(self, params: dict = None) -> dict:
        return self._call(method="GET",
                          path=f"{self.resource}/authUser/allocatedList",
                          params=params or {})

    def unallocated_user_list(self, params: dict = None) -> dict:
        return self._call(method="GET",
                          path=f"{self.resource}/authUser/unallocatedList",
                          params=params or {})

    def role_menu_treeselect(self, role_id: int) -> dict:
        """角色授权时加载菜单树"""
        return self._call(method="GET",
                          path=f"/system/menu/roleMenuTreeselect/{role_id}")

    @staticmethod
    def build_role_data(role_name: str, role_key: str,
                        role_id: Optional[int] = None, **extra) -> dict:
        """构造角色数据，role_name + role_key 必填"""
        return {
            "roleName": role_name,
            "roleKey": role_key,
            "roleSort": extra.get("role_sort", 1),
            "status": extra.get("status", "0"),
            "menuIds": extra.get("menu_ids", []),
            **({"roleId": role_id} if role_id is not None else {}),
        }
