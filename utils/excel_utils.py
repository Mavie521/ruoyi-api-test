"""
Excel 测试用例工具 —— 读取 + 渲染 + 字段解析

功能:
  1. read_excel()     — 读取 Excel，按 is_true 过滤
  2. render_case()    — Jinja2 渲染 {{变量}}
  3. _parse_field()   — Excel JSON 字符串 → Python 对象
"""
import json
import openpyxl
from jinja2 import Template
from config.config import EXCEL_FILE, SHEET_NAME
from utils.logger import logger


def read_excel(file_path: str = None, sheet_name: str = None) -> list[dict]:
    """
    从 Excel 读取测试用例数据
    - 只读取 is_true 为 True/1 的用例
    - 返回 list[dict]，每个 dict 对应一行用例
    """
    file_path = file_path or EXCEL_FILE
    sheet_name = sheet_name or SHEET_NAME

    try:
        workbook = openpyxl.load_workbook(file_path)
    except FileNotFoundError:
        logger.warning(f"Excel 文件不存在: {file_path}，跳过数据驱动加载")
        return []

    worksheet = workbook[sheet_name]

    # 第2行为表头（第1行可放注释）
    headers = [cell.value for cell in worksheet[1]]

    data = []
    for row in worksheet.iter_rows(min_row=2, values_only=True):
        if not any(cell is not None for cell in row):
            continue
        row_dict = dict(zip(headers, row))
        is_true = row_dict.get("is_true")
        if is_true is True or str(is_true).upper() == "TRUE":
            data.append(row_dict)
    workbook.close()
    logger.info(f"从 Excel 加载 {len(data)} 条有效用例")
    return data


# ── 渲染 ─────────────────────────────────────────────


def render_case(case: dict, global_vars: dict) -> dict:
    """Jinja2 渲染 {{变量}}"""
    case_str = json.dumps(case, ensure_ascii=False)
    return json.loads(Template(case_str).render(global_vars))


def _parse_field(value):
    # ① 判断：是不是字符串
    if isinstance(value, str):
        # 去掉前后空格（防止Excel不小心多打空格）
        value = value.strip()
        # 判断：文字是不是 { 或者 [ 开头
        if value.startswith(("{", "[")):
            try:
                # 尝试把文本转成字典/列表
                return json.loads(value)
            except json.JSONDecodeError:
                # 格式写错，转失败了，不崩溃，原样返回文字
                return value
    # 不是字符串（数字、字典、空值）直接原封不动返回
    return value
