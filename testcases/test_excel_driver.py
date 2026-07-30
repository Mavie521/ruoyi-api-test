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
    return base  #base = 已经完成登录、内置管理员 Token 的 BaseApi 实例对象


# ═══════════════════════════════════════════════════════════════
# 参数化构建
# ═══════════════════════════════════════════════════════════════

# getattr 动态获取属性
# ① read_excel() 返回 45 个 dict，每个 dict 是 Excel 一行。
# ② getattr(pytest.mark, "p0") ——把字符串 "p0" 转换成真正的 pytest 标记 pytest.mark.p0。
# ③ 如果 Excel 的 marker 列为空，不加标记，默认全跑。
# 这样：
# Excel 里填 "p0"  → pytest -m p0  只跑这条
# Excel 里填 "p1"  → pytest -m p1  只跑这条
# Excel 里空着    → 全量跑时也跑
#p0 = 核心冒烟用例；p1 = 完整回归；日常版本迭代只跑 p0 快速冒烟

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
        #allure.dynamic.xxx动态API（你框架使用方案）在用例运行期间实时赋值！
        # 数据来源就是当前这条用例的字典case（Excel一行数据）。
        # 运行时读取Excel里的feature、story、id、title，自动渲染到报告。
        allure_init(case)
        # Jinja2是模板工具，核心功能是扫描字符串中的{{变量名}}占位符，根据传入的变量字典进行文本替换。但是它只能处理字符串，无法直接解析
        # Python字典。所以我的render_case函数先用json.dumps把整个用例字典转字符串，交给Jinja渲染填充变量；渲染完成后再通过json.loads转回字典，给后续接口调用使用。

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
        # 在进JSON断言之前先检查HTTP层面是否正常。
        # 如果服务器根本没响应（500 / 502 / 404），
        # 后续的res.json()可能出错或拿到错误页面的HTML，报错信息会很乱。
        if res.status_code != 200:
            raise ConnectionError(
                f"\n  [HTTP 状态码异常]"
                f"\n  请求: {method.upper()} {path}"
                f"\n  期望: 200 | 实际: {res.status_code}"
                f"\n  响应体: {res.text[:500]}" #防止后端返回超大长文本，日志疯狂刷屏，限制长度
            )

        # 四步业务逻辑（变量提取会回写到 excel_vars，后续用例自动可用）
        if rendered.get("response_type") == "binary":
            do_binary_assert(rendered, res)               # 文件下载：Content-Type/大小/SHA-256
        else:
            do_assert(rendered, res)                      # JSON 断言：$.code == 200
            do_extract_json(rendered, res, excel_vars)    # 提取变量 → 写回 excel_vars
        # 数据库校验
        do_db_assert(rendered)
        # SQL 提取变量
        do_extract_sql(rendered, excel_vars)
