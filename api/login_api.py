"""
登录模块 API 封装
对应接口文档: sys-login-controller
"""
import allure
from config.config import ADMIN_USERNAME as DEFAULT_USER, ADMIN_PASSWORD as DEFAULT_PWD
from utils.logger import logger
from .base_api import BaseApi


class LoginApi(BaseApi):
    """登录相关接口"""

    @allure.step("登录")
    def login(self, username: str = None, password: str = None) -> str:
        """
        用户登录
        POST /login
        - 成功时自动保存 token
        - 返回 token 字符串
        """
        username = DEFAULT_USER if username is None else username
        password = DEFAULT_PWD if password is None else password

        body = {
            "username": username,
            "password": password,
        }
        res = self.post("/login", json=body)

        body_resp = res.json()
        token = body_resp.get("token")

        if token:
            self.set_token(token)
            logger.info(f" 登录成功: {username}")
        else:
            logger.error(f" 登录失败: {body_resp.get('msg', '未知错误')}")

        return token

    @allure.step("获取菜单路由")
    def get_routers(self) -> dict:
        """
        获取当前用户的路由/菜单树
        GET /getRouters
        """
        res = self.get("/getRouters")
        return res.json()

    @allure.step("获取当前用户信息")
    def get_info(self) -> dict:
        """
        获取当前登录用户信息（角色、权限等）
        GET /getInfo
        """
        res = self.get("/getInfo")
        return res.json()
