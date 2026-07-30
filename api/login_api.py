"""登录模块 API"""
import allure
from config.config import ADMIN_USERNAME as DEFAULT_USER, ADMIN_PASSWORD as DEFAULT_PWD
from utils.logger import logger
from .base_api import BaseApi


class LoginApi(BaseApi):

    @allure.step("登录")
    def login(self, username: str = None, password: str = None) -> str:
        """登录成功自动保存 token，返回 token 字符串"""
        username = username or DEFAULT_USER
        password = password or DEFAULT_PWD
        body = {"username": username, "password": password}

        res = self.request(method="POST", path="/login", json=body).json()
        token = res.get("token")
        if token:
            self.set_token(token)
            logger.info(f"登录成功: {username}")
        else:
            logger.error(f"登录失败: {res.get('msg', '未知错误')}")
        return token

    # 返回当前用户可见的菜单路由树
    def get_routers(self) -> dict:
        return self._call(method="GET", path="/getRouters")

    # 返回当前登录用户的个人信息：userName, nickName, roles, permissions
    # 用来验证"这个用户确实是一个正常的、激活的、有登录能力的用户"的最低门槛接口
    #如果get_info()都调不通，只有两种可能：- token无效（登录没成功）- 用户被禁用（status = '1'）
    def get_info(self) -> dict:
        return self._call(method="GET", path="/getInfo")
