"""
三层架构 → 数据层执行器（统一标记版）

核心改动：Excel 用例的 marker 字段自动转为 @pytest.mark.xxx，
与代码用例共用 -m p0/p1 统一过滤。

用法（统一入口）：
  pytest tests/ testcases/ -m p0 -v   # P0 代码 + Excel 一起跑
  pytest tests/ testcases/ -m p1 -v   # P1 一起跑
  pytest testcases/ -v                 # 全量 Excel
"""
import allure
import pytest
import requests
from utils.logger import logger
from utils.excel_utils import read_excel
from utils.allure_utils import allure_init
from utils.data_driver import render_case, send_request, do_assert, do_db_assert, do_extract
from config.config import BASE_URL

# 读取所有 Excel 用例
ALL_CASES = read_excel()
GLOBAL_VARS = {}


def setup_module():
    """全局初始化：登录一次，提取 TOKEN"""
    logger.info(f"--- Excel 数据驱动: 共 {len(ALL_CASES)} 条用例 ---")
    resp = requests.post(BASE_URL + "/login",
                         json={"username": "admin", "password": "admin123"}, timeout=10)
    token = resp.json().get("token")
    if token:
        GLOBAL_VARS["TOKEN"] = token


def _build_params():
    """
    构建带动态标记的参数列表。
    每条 Excel 用例的 marker 字段（p0/p1/p2/...）自动转为 @pytest.mark.p0 等。
    这样 pytest -m p0 既能筛代码用例，也能筛 Excel 用例。
    """
    result = []
    for case in ALL_CASES:
        marker_name = case.get("marker", "")
        if marker_name and marker_name != "all":
            marker = getattr(pytest.mark, marker_name, None)
            if marker:
                result.append(pytest.param(case, marks=[marker]))
            else:
                result.append(case)
        else:
            result.append(case)
    return result


class TestExcelDataLayer:
    """Excel 数据驱动测试执行器"""

    @pytest.mark.parametrize("case", _build_params())
    def test_excel_case(self, case):
        allure_init(case)
        rendered = render_case(case, GLOBAL_VARS)
        res = send_request(rendered)
        do_assert(rendered, res)
        if rendered.get("sql_check"):
            do_db_assert(rendered)
        do_extract(rendered, res, GLOBAL_VARS)
