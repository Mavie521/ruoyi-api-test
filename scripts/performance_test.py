"""
RuoYi API 性能压测脚本 (Locust)
覆盖: 登录/查询/增删改/安全/混合场景

基础用法:
  # 快速压测（50并发60秒）
  locust -f scripts/performance_test.py --headless -u 50 -r 5 -t 60s --host=http://ruoyi-api:8080

  # Web 监控模式
  locust -f scripts/performance_test.py --web-host 0.0.0.0 --host=http://ruoyi-api:8080

  # CSV 导出结果
  locust -f scripts/performance_test.py --headless -u 50 -r 5 -t 60s --csv=reports/perf/report --host=http://ruoyi-api:8080
"""
from locust import HttpUser, task, between, tag


class RuoYiUser(HttpUser):
    """模拟真实用户操作"""
    wait_time = between(1, 3)
    token = None
    host = "http://ruoyi-api:8080"

    def on_start(self):
        """用户启动时登录"""
        resp = self.client.post("/login", json={
            "username": "admin", "password": "admin123"
        })
        if resp.status_code == 200:
            data = resp.json()
            self.token = data.get("token")
            if self.token:
                self.client.headers.update({"Authorization": f"Bearer {self.token}"})

    # ═══════════════════════════════════════
    # 场景一：常规查询（高频，占比最高）
    # ═══════════════════════════════════════
    @tag("query")
    @task(5)
    def list_users(self):
        """查询用户列表"""
        self.client.get("/system/user/list?pageNum=1&pageSize=10")

    @tag("query")
    @task(4)
    def list_roles(self):
        """查询角色列表"""
        self.client.get("/system/role/list?pageNum=1&pageSize=10")

    @tag("query")
    @task(3)
    def get_user_detail(self):
        """查看用户详情"""
        self.client.get("/system/user/1")

    @tag("query")
    @task(2)
    def get_info(self):
        """获取个人信息"""
        self.client.get("/getInfo")

    @tag("query")
    @task(2)
    def get_routers(self):
        """获取菜单路由"""
        self.client.get("/getRouters")

    @tag("query")
    @task(2)
    def list_depts(self):
        """查询部门列表"""
        self.client.get("/system/dept/list")

    # ═══════════════════════════════════════
    # 场景二：写操作（低频，占比低但关键）
    # ═══════════════════════════════════════
    @tag("write")
    @task(1)
    def role_option_select(self):
        """获取角色下拉选项（常用于表单）"""
        self.client.get("/system/role/optionselect")

    @tag("write")
    @task(1)
    def dept_tree(self):
        """获取部门树"""
        self.client.get("/system/dept/treeselect")

    # ═══════════════════════════════════════
    # 场景三：安全测试（极低频）
    # ═══════════════════════════════════════
    @tag("security")
    @task(1)
    def fake_token(self):
        """模拟无效 token 请求（验证后端容错）"""
        old_token = self.client.headers.get("Authorization")
        self.client.headers.update({"Authorization": "Bearer fake_token_here"})
        self.client.get("/getInfo")
        if old_token:
            self.client.headers.update({"Authorization": old_token})


class RuoYiWriteUser(HttpUser):
    """模拟管理员高频写操作（单独运行）"""
    wait_time = between(2, 5)
    token = None
    host = "http://ruoyi-api:8080"

    def on_start(self):
        resp = self.client.post("/login", json={
            "username": "admin", "password": "admin123"
        })
        if resp.status_code == 200:
            self.token = resp.json().get("token")
            if self.token:
                self.client.headers.update({"Authorization": f"Bearer {self.token}"})

    @tag("write-heavy")
    @task(1)
    def update_role(self):
        """编辑角色"""
        self.client.put("/system/role", json={
            "roleId": 1, "roleName": "超管", "roleKey": "admin",
            "roleSort": 1, "status": "0", "menuIds": []
        })
