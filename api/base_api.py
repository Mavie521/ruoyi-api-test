"""requests.Session 封装 + Token 管理 + 超时重试 + 通用 CRUD + 通用请求入口"""
from typing import Union, List
import allure
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from config.config import BASE_URL, DEFAULT_TIMEOUT
from utils.logger import logger
from utils.allure_utils import attach_request, attach_response


class BaseApi:
    """所有 API 对象的基类 —— 统一管理 Session / Token / 重试 / CRUD 模板方法
    子类覆盖 resource 属性即可获得完整 CRUD 能力（如 resource="/system/role"）。
    不需要 CRUD 的子类（如 LoginApi）不设置 resource 即可。
    """
    #子类只需要定义 resource="/system/role"，自动拥有一套 CRUD 接口调用方法
    resource: str = ""

    def __init__(self):
        self.base_url = BASE_URL.rstrip("/")
        self._token = None  #私有变量，存放登录凭证
        self.timeout = DEFAULT_TIMEOUT

        self.session = requests.Session()
        # requests底层用来定制网络行为的适配器。
        # 默认的requests没有自动重试、连接池控制能力；
        # HTTPAdapter允许我们挂载自定义策略：连接复用、失败重试。配合Retry类，实现接口5xx错误自动重试。
        adapter = HTTPAdapter(
            max_retries=Retry(
            total=2, connect=1, read=0, status=1, other=0,
            backoff_factor=1,
            status_forcelist=[500, 502, 503, 504],
            allowed_methods=["GET", "POST", "PUT", "DELETE"],
        ))
        #session 设置规则：只要发起 http:// 或者https://开头的请求，全部套用我们写好的「重试策略adapter」
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

    # ── Token ──
    @property
    def token(self) -> str:
        return self._token

    def set_token(self, token: str):
        self._token = token
        self.session.headers.update({"Authorization": f"Bearer {token}"})

    def clear_token(self):
        self._token = None
        self.session.headers.pop("Authorization", None)

    # ── 请求  等着被调用 ──
    # 拼接url、token请求头、超时、日志打印、allure报告附件、使用session发送网络请求
    # 职责：真正和后端建立网络通信，发出HTTP请求，返回原始Response响应对象
    @allure.step("HTTP 请求")
    def request(self, **kwargs) -> "Response":
        """通用请求入口。method/path 必填，其余参数透传给 requests.request()
        method=  path=  params=  json=  data=  headers=  files=  cookies=  timeout=  auth=
        """
        method = kwargs.pop("method", "get").lower()
        url = kwargs.pop("path", kwargs.pop("url", None))
        assert url, "request() 缺少 path 或 url"
        if not url.startswith("http"):
            url = f"{self.base_url}{url}"

        kwargs.setdefault("timeout", self.timeout)

        excel_headers = kwargs.pop("headers", None)
        request_headers = dict(self.session.headers)
        if excel_headers:
            for k, v in excel_headers.items():
                if k.lower() != "authorization":
                    request_headers[k] = v

        #把请求参数嵌入 Allure 测试报告
        attach_request(method, url, headers=request_headers, **kwargs)
        logger.debug(f">> {method.upper()} {url}")

        res = self.session.request(method, url, headers=request_headers, **kwargs)
        res.encoding = "utf-8"
        logger.debug(f"<< {res.status_code}")
        #把响应结果嵌入Allure测试报告
        attach_response(res)
        return res
    #作用：调用 request() → 拿到响应 → 立刻执行.json()，把 json 字符串转换成 Python 字典，对外返回字典
    def _call(self, **kwargs) -> dict:
        return self.request(**kwargs).json()

    # ── 通用 CRUD（子类设置 resource 属性即可使用）──

    def list(self, params: dict = None) -> dict:
        return self._call(method="GET", path=f"{self.resource}/list",
                          params=params or {})

    def get(self, id_: int) -> dict:
        return self._call(method="GET", path=f"{self.resource}/{id_}")

    def create(self, data: dict) -> dict:
        return self._call(method="POST", path=self.resource, json=data)

    def update(self, data: dict) -> dict:
        return self._call(method="PUT", path=self.resource, json=data)

    def delete(self, ids: Union[int, List[int]]) -> dict:
        """批量删除，兼容单 ID 和多 ID 场景"""
        if isinstance(ids, int):
            ids = [ids]
        return self._call(method="DELETE",
                          path=f"{self.resource}/{','.join(map(str, ids))}")

    def change_status(self, **kwargs) -> dict:
        return self._call(method="PUT",
                          path=f"{self.resource}/changeStatus",
                          json=kwargs)
