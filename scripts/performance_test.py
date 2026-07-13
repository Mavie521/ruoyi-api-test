"""
RuoYi API 性能压测脚本 (Locust)
用法: locust -f scripts/performance_test.py --headless -u 50 -r 5 -t 60s
"""
import random
from locust import HttpUser, task, between, tag


class RuoYiUser(HttpUser):
    """模拟一个普通用户的操作行为"""
    wait_time = between(1, 3)           # 每个操作间隔 1-3 秒
    token = None
    host = "http://ruoyi-api:8080"     # Docker 环境

    def on_start(self):
        """用户启动时：登录"""
        resp = self.client.post("/login", json={
            "username": "admin",
            "password": "admin123"
        })
        if resp.status_code == 200:
            data = resp.json()
            self.token = data.get("token")
            if self.token:
                self.client.headers.update({"Authorization": f"Bearer {self.token}"})

    @tag("query")
    @task(5)
    def list_users(self):
        """查询用户列表（高频操作）"""
        self.client.get("/system/user/list?pageNum=1&pageSize=10")

    @tag("query")
    @task(3)
    def list_roles(self):
        """查询角色列表"""
        self.client.get("/system/role/list?pageNum=1&pageSize=10")

    @tag("query")
    @task(2)
    def get_user_detail(self):
        """获取用户详情"""
        self.client.get("/system/user/1")

    @tag("write")
    @task(1)
    def get_info(self):
        """获取当前用户信息"""
        self.client.get("/getInfo")
