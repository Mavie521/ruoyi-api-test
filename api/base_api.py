"""
基础 API 封装 —— requests.Session 封装 + Token 自动管理 + 超时重试

核心功能:
1. 自动从 config 加载 BASE_URL
2. 提供 get/post/put/delete 通用方法（带日志 + Allure 步骤 + 自动附件）
3. Token 自动管理：set_token() 后后续请求自动携带
4. 【新增】统一超时（15s）+ 失败自动重试 1 次（网络波动容错）
5. 【新增】空响应/异常响应容错（避免 500 时程序崩溃）
"""
import json as json_lib
import time
import allure
import requests
from requests import Response
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from config.config import BASE_URL, DEFAULT_TIMEOUT
from utils.logger import logger
from utils.allure_utils import attach_request, attach_response


class BaseApi:
    """所有 API 对象的基类，封装请求发送、token 管理、日志、重试"""

    def __init__(self):
        self.session = requests.Session()
        self.base_url = BASE_URL.rstrip("/")
        self._token = None
        self._last_response = None
        # === 【新增】统一超时配置（15s，避免接口卡死） ===
        self.timeout = DEFAULT_TIMEOUT

        # === 【新增】requests 自动重试（最多重试 1 次，间隔 1s） ===
        retry_strategy = Retry(
            total=1,                        # 总重试次数（排除首次）
            backoff_factor=1,               # 重试间隔 1s
            status_forcelist=[500, 502, 503, 504],  # 服务端错误才重试
            allowed_methods=["GET", "POST", "PUT", "DELETE"],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

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
        logger.info(" Token 已设置")

    def clear_token(self):
        """清除 token"""
        self._token = None
        self.session.headers.pop("Authorization", None)

    # ---------------------------------------------------------
    # 通用请求方法
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
        通用请求方法
        - url: 完整 URL 或相对路径（自动拼接 base_url）
        - 【新增】超时 + 重试 + 异常响应容错
        """
        if not url.startswith("http"):
            url = f"{self.base_url}{url}"

        # === 【新增】统一超时设置 ===
        kwargs.setdefault("timeout", self.timeout)

        # Attach 请求到 Allure
        attach_request(method, url, headers=self.session.headers, **kwargs)
        self._log_request(method, url, **kwargs)

        try:
            # === 【优化】带重试的请求 ===
            res = self.session.request(method, url, **kwargs)
            self._last_response = res
            self._log_response(res)
            attach_response(res)
            return res

        except requests.exceptions.ConnectionError as e:
            # === 【新增】连接失败容错：记录到 Allure 但不崩溃 ===
            logger.error(f"连接失败: {method} {url} - {e}")
            allure.attach(str(e), name=" 连接异常", attachment_type=allure.attachment_type.TEXT)
            # 返回一个模拟的 503 Response，避免调用方崩
            mock_res = Response()
            mock_res.status_code = 503
            mock_res._content = b'{"code":500,"msg":"Connection refused"}'
            return mock_res

        except requests.Timeout as e:
            logger.error(f"请求超时: {method} {url} - {e}")
            allure.attach(str(e), name=" 超时异常", attachment_type=allure.attachment_type.TEXT)
            mock_res = Response()
            mock_res.status_code = 504
            mock_res._content = b'{"code":500,"msg":"Timeout"}'
            return mock_res

        except requests.RequestException as e:
            logger.error(f"请求异常: {method} {url} - {e}")
            allure.attach(str(e), name=" 请求异常", attachment_type=allure.attachment_type.TEXT)
            raise   # 未知异常往上抛

    def get(self, url: str, **kwargs) -> Response:
        return self.request("GET", url, **kwargs)

    def post(self, url: str, **kwargs) -> Response:
        return self.request("POST", url, **kwargs)

    def put(self, url: str, **kwargs) -> Response:
        return self.request("PUT", url, **kwargs)

    def delete(self, url: str, **kwargs) -> Response:
        return self.request("DELETE", url, **kwargs)
