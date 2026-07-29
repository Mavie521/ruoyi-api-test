"""
API 对象层 - 包入口 让外面所有文件，不用关心这个类到底藏在哪个 xxx_api.py 文件里，只需要认识 api 这个包即可
"""
from .base_api import BaseApi
from .login_api import LoginApi
from .role_api import RoleApi
from .system_user_api import SystemUserApi
from .dept_api import DeptApi
from .post_api import PostApi

__all__ = ["BaseApi", "LoginApi", "RoleApi", "SystemUserApi", "DeptApi", "PostApi"]
