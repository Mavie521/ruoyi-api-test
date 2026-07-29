"""部门管理模块 API"""
from .base_api import BaseApi


class DeptApi(BaseApi):
    resource = "/system/dept"
