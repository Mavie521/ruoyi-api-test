"""
真实用户管理模块 API 封装
对应若依后台: 系统管理 → 用户管理
真实接口: /system/user/**
操作数据库: sys_user 表
"""
import time
from typing import Optional
import allure
from .base_api import BaseApi


class SystemUserApi(BaseApi):
    """用户管理（真实业务）"""

    @allure.step("查询用户列表")
    def list_users(self, params: dict = None) -> dict:
        """
        查询用户列表（分页）
        GET /system/user/list
        返回: {code, msg, total, rows: [...]}
        """
        res = self.get("/system/user/list", params=params or {})
        return res.json()

    @allure.step("获取用户详情")
    def get_user(self, user_id: int) -> dict:
        """
        获取用户详情
        GET /system/user/{userId}
        """
        res = self.get(f"/system/user/{user_id}")
        return res.json()

    @allure.step("新增用户")
    def create_user(self, user_data: dict) -> dict:
        """
        新增用户
        POST /system/user
        """
        res = self.post("/system/user", json=user_data)
        return res.json()

    @allure.step("修改用户")
    def update_user(self, user_data: dict) -> dict:
        """
        修改用户
        PUT /system/user
        """
        res = self.put("/system/user", json=user_data)
        return res.json()

    @allure.step("删除用户")
    def delete_user(self, user_id: int) -> dict:
        """
        删除用户
        DELETE /system/user/{userId}
        """
        res = self.delete(f"/system/user/{user_id}")
        return res.json()

    @allure.step("重置密码")
    def reset_password(self, user_id: int, password: str = "123456") -> dict:
        """
        重置密码
        PUT /system/user/resetPwd
        """
        res = self.put("/system/user/resetPwd", json={"userId": user_id, "password": password})
        return res.json()

    @allure.step("修改用户状态")
    def change_status(self, user_id: int, status: str = "1") -> dict:
        """
        修改用户状态（启用/禁用）
        PUT /system/user/changeStatus
        """
        res = self.put("/system/user/changeStatus", json={"userId": user_id, "status": status})
        return res.json()

    # ---------------------------------------------------------
    # 业务辅助
    # ---------------------------------------------------------
    @staticmethod
    def build_user_data(
        username: str,
        password: str = "123456",
        user_id: Optional[int] = None,
        **extra,
    ) -> dict:
        """构造用户数据，默认生成带时间戳的用户信息"""
        suffix = str(int(time.time() * 1000))[-6:]
        data = {
            "userName": username,
            "nickName": extra.get("nick_name") or f"用户_{suffix}",
            "password": password,
            "deptId": extra.get("dept_id", 103),
            "email": extra.get("email") or f"{username}@ruoyi.com",
            "phonenumber": extra.get("phone") or f"138{suffix[:8].zfill(8)}",
            "sex": extra.get("sex", "0"),
            "status": extra.get("status", "0"),
            "postIds": [],
            "roleIds": [],
            "remark": "由接口测试框架创建",
        }
        if user_id is not None:
            data["userId"] = user_id
        return data
