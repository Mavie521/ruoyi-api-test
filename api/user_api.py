"""
用户管理模块 API 封装
对应接口文档: 用户信息管理 (/test/user/*)
"""
import allure
from .base_api import BaseApi


class UserApi(BaseApi):
    """用户管理相关接口"""

    @allure.step("获取用户列表")
    def list_users(self, params: dict = None) -> dict:
        """
        获取用户列表
        GET /test/user/list
        注意：此接口返回格式为 {"code": 200, "data": [...], "msg": "操作成功"}
        """
        res = self.get("/test/user/list", params=params or {})
        return res.json()

    @allure.step("获取用户详情")
    def get_user(self, user_id: int) -> dict:
        """
        获取指定用户详情
        GET /test/user/{userId}
        """
        res = self.get(f"/test/user/{user_id}")
        return res.json()

    @allure.step("新增用户")
    def create_user(self, user_data: dict) -> dict:
        """
        新增用户
        POST /test/user/save
        user_data 作为展开的 query 参数发送（Spring @RequestParam 绑定方式）
        """
        res = self.post("/test/user/save", params=user_data)
        return res.json()

    @allure.step("更新用户")
    def update_user(self, user_data: dict) -> dict:
        """
        更新用户
        PUT /test/user/update (json body)
        """
        res = self.put("/test/user/update", json=user_data)
        return res.json()

    @allure.step("删除用户")
    def delete_user(self, user_id: int) -> dict:
        """
        删除用户
        DELETE /test/user/{userId}
        """
        res = self.delete(f"/test/user/{user_id}")
        return res.json()

    # ---------------------------------------------------------
    # 业务辅助方法
    # ---------------------------------------------------------
    def build_user_data(
        self,
        username: str,
        user_id: int,
        password: str = "123456",
        mobile: str = "13800138000",
    ) -> dict:
        """构造用户数据（/test/user/save 需要 userId）"""
        return {
            "userId": user_id,
            "username": username,
            "password": password,
            "mobile": mobile,
        }
