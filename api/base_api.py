"""
基础 API 封装 —— requests.Session 封装 + Token 自动管理

核心功能:
1. 自动从 config 加载 BASE_URL
2. 提供 get/post/put/delete 通用方法（带日志 + Allure 步骤 + 自动附件）
3. token 自动管理：set_token() 后后续请求自动携带
4. 统一的响应日志和异常处理
5. 每次请求自动 attach 到 Allure 报告（方便失败定位）
"""
import json as json_lib
import allure
import requests
from requests import Response
from config.config import BASE_URL, DEFAULT_TIMEOUT
from utils.logger import logger
from utils.allure_utils import attach_request, attach_response


class BaseApi:
    """所有 API 对象的基类，封装请求发送、token 管理、日志"""

    def __init__(self):
        self.session = requests.Session()
        self.base_url = BASE_URL.rstrip("/")
        self._token = None
        self._last_response = None  # 保留最后响应，用于失败时 attach

    # ---------------------------------------------------------
    # Token 管理
    # ---------------------------------------------------------
    @property
    def token(self) -> str:
        return self._token

    def set_token(self, token: str):
        """设置 token，后续所有请求自动携带 Authorization 头"""
        self._token = token
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        logger.info("🔑 Token 已设置")

    def clear_token(self):
        """清除 token"""
        self._token = None
        self.session.headers.pop("Authorization", None)

    # ---------------------------------------------------------
    # 通用请求方法（每个方法都带 Allure 步骤 + 日志 + 附件）
    # ---------------------------------------------------------
    def _log_request(self, method: str, url: str, **kwargs):
        """记录请求日志"""
        log_data = {
            "method": method,
            "url": url,
            "headers": {k: v for k, v in self.session.headers.items() if k.lower() != "authorization"},
        }
        if "params" in kwargs and kwargs["params"]:
            log_data["params"] = kwargs["params"]
        if "json" in kwargs and kwargs["json"]:
            log_data["json"] = kwargs["json"]
        if "data" in kwargs and kwargs["data"]:
            log_data["data"] = kwargs["data"]
        logger.debug(f"请求详情: {json_lib.dumps(log_data, ensure_ascii=False, default=str)}")

    def _log_response(self, res: Response):
        """记录响应日志"""
        try:
            body = res.json()
            body_preview = json_lib.dumps(body, ensure_ascii=False, indent=2)[:500]
        except Exception:
            body_preview = res.text[:500]
        logger.debug(f"响应 ({res.status_code}): {body_preview}")

    @allure.step("{method} {url}")
    def request(self, method: str, url: str, **kwargs) -> Response:
        """
        通用请求方法，所有 API 请求最终都经过此方法
        - url: 完整 URL 或相对路径（自动拼接 base_url）
        - 自动注入 token（如果已设置）
        - 统一日志 + Allure 附件 + 异常处理
        """
        if not url.startswith("http"):
            url = f"{self.base_url}{url}"

        kwargs.setdefault("timeout", DEFAULT_TIMEOUT)

        # Attach 请求到 Allure
        attach_request(method, url, headers=self.session.headers, **kwargs)

        self._log_request(method, url, **kwargs)

        try:
            res = self.session.request(method, url, **kwargs)
            self._last_response = res
            self._log_response(res)
            # Attach 响应到 Allure
            attach_response(res)
            return res
        except requests.RequestException as e:
            logger.error(f"请求异常: {method} {url} - {e}")
            allure.attach(str(e), name="❌ 请求异常", attachment_type=allure.attachment_type.TEXT)
            raise

    def get(self, url: str, **kwargs) -> Response:
        return self.request("GET", url, **kwargs)

    def post(self, url: str, **kwargs) -> Response:
        return self.request("POST", url, **kwargs)

    def put(self, url: str, **kwargs) -> Response:
        return self.request("PUT", url, **kwargs)

    def delete(self, url: str, **kwargs) -> Response:
        return self.request("DELETE", url, **kwargs)
