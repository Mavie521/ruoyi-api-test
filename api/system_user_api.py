"""用户管理模块 API"""
import uuid
from typing import Optional
from .base_api import BaseApi


class SystemUserApi(BaseApi):
    resource = "/system/user"

    # ── 用户特有的方法 ──

    def reset_password(self, user_id: int, password: str = "123456") -> dict:
        return self._call(method="PUT", path=f"{self.resource}/resetPwd",
                          json={"userId": user_id, "password": password})

    def auth_role(self, user_id: int) -> dict:
        """查询用户已分配的角色列表"""
        return self._call(method="GET", path=f"{self.resource}/authRole/{user_id}")

    def profile(self) -> dict:
        """获取当前登录用户个人信息"""
        return self._call(method="GET", path=f"{self.resource}/profile")

    @staticmethod
    def build_user_data(username: str, password: str = "123456",
                        user_id: Optional[int] = None, **extra) -> dict:  #类型提示 (Type Hinting) + 默认参数None
        """构造用户数据，默认生成带随机后缀的用户信息"""
        suffix = uuid.uuid4().hex[:8]
        return {
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
            **({"userId": user_id} if user_id is not None else {}),
        }


# 这段代码是典型的“工厂模式（Factory Pattern）”在测试数据构造中的应用。
# 你可以把这个 build_user_data 函数理解为一个“智能数据组装车间”。
# 1. 核心机制：它是怎么做到“既灵活又省事”的？
# 这个函数最巧妙的地方在于 **extra 和 extra.get() 的配合。
# **extra (魔法口袋)： 这是一个关键字参数。意思是，除了 username、password 这些明确定义的参数外，你传进来的任何其他参数（比如 nick_name、email），都会被打包成一个字典塞进 extra 里。这让函数变得极其灵活。
# extra.get("key", default) (智能兜底)： 这是 Python 字典的一个方法。它的意思是：“去 extra 口袋里找 key，如果找到了就用它，如果没找到，就用 default 默认值。”
# 最终 user_data 是一个包含 11 个字段的完整字典。build_user_data 帮你填了
# deptId=103、sex="0"、status="0"、postIds=[]、roleIds=[] 这些不需要你关心的字段。