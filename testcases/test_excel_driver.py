"""
Excel数据驱动测试执行器

工作原理:
  1. 读取 data/test_cases.xlsx 中 is_true=True 的用例
  2. 逐条执行: 渲染模板 → 发请求 → 断言 → 提取变量
  3. 登录token等变量会自动传递

用法:
  在Excel中新增一行用例 → 保存 → 跑这条命令:
  python -m pytest testcases/test_excel_driver.py -v
"""
import allure
import pytest
from utils.logger import logger
from utils.excel_utils import read_excel
from utils.allure_utils import allure_init
from utils.data_driver import render_case, send_request, do_assert, do_extract


# 读取所有Excel用例（is_true=True的才会被加载）
ALL_CASES = read_excel()

# 全局变量存储（用于用例间传递数据，如token）
GLOBAL_VARS = {}


class TestExcelDriver:
    """Excel数据驱动测试"""

    @pytest.mark.parametrize("case", ALL_CASES)
    def test_excel_case(self, case):
        # 0. Allure报告：动态设置feature/story/title
        allure_init(case)

        # 1. 模板渲染：替换 {{TOKEN}} 等占位符
        rendered = render_case(case, GLOBAL_VARS)

        # 2. 发HTTP请求
        res = send_request(rendered)

        # 3. Attach请求响应到Allure报告
        url = f"{rendered.get('method', 'GET').upper()} {rendered.get('path', '')}"
        with allure.step(f"请求: {url}"):
            allure.attach(
                f"状态码: {res.status_code}\n响应: {res.text[:500]}",
                name="响 应",
                attachment_type=allure.attachment_type.TEXT,
            )

        # 4. 断言
        with allure.step("断言验证"):
            do_assert(rendered, res)

        # 5. 提取变量（如提取token供后续用例使用）
        with allure.step("提取变量"):
            do_extract(rendered, res, GLOBAL_VARS)
