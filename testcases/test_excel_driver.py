"""
Excel 数据驱动测试执行器

核心设计：Excel 列名对齐 requests.request() 参数名，通过 **kwargs 万能透传。
新增请求参数只需在 Excel 加列，不用改代码。

变量传递：用例间通过 excel_vars 共享变量（模块级 fixture）。
  例：用例1 登录后提取 TOKEN → excel_vars["TOKEN"] → 用例2 的 {{TOKEN}} 被渲染

限制：
  - 仅支持单进程顺序执行（Excel 用例有变量依赖，不适合并行）
  - 并发场景请用 tests/ 下的代码用例

用法：
  pytest testcases/ -v               # 全量 Excel
  pytest testcases/ -v -m p0         # P0 级别
"""
import time
import allure
import pytest
from utils.logger import logger
from utils.excel_utils import read_excel, render_case, _parse_field
from utils.allure_utils import allure_init
from utils.assertions import do_assert, do_db_assert, do_binary_assert
from utils.extract_utils import do_extract_json, do_extract_sql
from api.base_api import BaseApi
from config.config import ADMIN_USERNAME, ADMIN_PASSWORD

# Excel 列名 → requests.request() 参数名映射
_REQUEST_PARAMS = {"params", "json", "data", "headers", "files", "cookies", "timeout", "auth"}


# ═══════════════════════════════════════════════════════════════
# Fixture：替代原来的模块级全局变量
# ═══════════════════════════════════════════════════════════════

@pytest.fixture(scope="module")
def excel_vars():
    """模块级共享变量池（线程安全的 dict，替代 GLOBAL_VARS）
    存放 TIMESTAMP + 运行时 extract 提取的变量，供后续用例 Jinja2 渲染
    """
    return {
        "TIMESTAMP": str(int(time.time())),
        "TS": str(int(time.time()))[-5:],   # 后5位短戳，用于拼用户名
    }


@pytest.fixture(scope="module")
def excel_api(excel_vars):
    """模块级已认证 BaseApi（替代 BASE_API），依赖 excel_vars
    登录一次 → token 注入变量池 → 整个模块复用
    """
    base = BaseApi()
    resp = base.request(
        method="POST", path="/login",
        json={"username": ADMIN_USERNAME, "password": ADMIN_PASSWORD},
    )
    body = resp.json()
    token = body.get("token")
    assert token, f"Excel 驱动登录失败: {body.get('msg', '')}"
    base.set_token(token)
    excel_vars["TOKEN"] = token
    logger.info(f"Excel BaseApi 初始化完成，{len(read_excel())} 条用例待执行")
    return base


# ═══════════════════════════════════════════════════════════════
# 参数化构建
# ═══════════════════════════════════════════════════════════════

def _build_params():
    """Excel 用例按 marker 字段打标记，兼容 pytest -m 过滤"""
    result = []
    for case in read_excel():
        marker_name = case.get("marker", "")
        if marker_name and marker_name != "all":
            marker = getattr(pytest.mark, marker_name, None)
            result.append(pytest.param(case, marks=[marker]) if marker else case)
        else:
            result.append(case)
    return result


# ═══════════════════════════════════════════════════════════════
# 执行器
# ═══════════════════════════════════════════════════════════════

class TestExcelDataLayer:
    """Excel 数据驱动：读取 → 渲染 → 请求 → 断言 → 提取"""

    @pytest.mark.parametrize("case", _build_params())
    def test_excel_case(self, case, excel_api, excel_vars):
        """每条 Excel 用例的执行入口"""
        allure_init(case)
        rendered = render_case(case, excel_vars)

        method = rendered.get("method", "get").lower()
        path = rendered.get("path", "")

        # 万能透传：Excel 列名 → request() 参数
        kwargs = {
            k: _parse_field(rendered[k])
            for k in _REQUEST_PARAMS
            if k in rendered and rendered[k] is not None
        }
        res = excel_api.request(method=method, path=path, **kwargs)

        # HTTP 状态码强制校验
        if res.status_code != 200:
            raise ConnectionError(
                f"\n  [HTTP 状态码异常]"
                f"\n  请求: {method.upper()} {path}"
                f"\n  期望: 200 | 实际: {res.status_code}"
                f"\n  响应体: {res.text[:500]}"
            )

        # 四步业务逻辑（变量提取会回写到 excel_vars，后续用例自动可用）
        if rendered.get("response_type") == "binary":
            do_binary_assert(rendered, res)
        else:
            do_assert(rendered, res)
            do_extract_json(rendered, res, excel_vars)
        do_db_assert(rendered)
        do_extract_sql(rendered, excel_vars)
