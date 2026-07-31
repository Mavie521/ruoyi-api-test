"""
Excel 测试用例工具 —— 读取 + 渲染 + 字段解析

┌─────────────────────────────────────────────────────────────────────┐
│ 这个文件做了什么？                                                  │
├─────────────────────────────────────────────────────────────────────┤
│ 1. read_excel()    — 打开 Excel，只读 is_true=TRUE 的有效用例      │
│ 2. render_case()   — 用 Jinja2 把 {{变量名}} 替换成实际值          │
│ 3. _parse_field()  — 把 Excel 单元格的 JSON 字符串转成 Python 对象 │
│                                                                     │
│ 数据流：                                                            │
│ Excel 文件 → read_excel() → render_case() → _parse_field() → 用例  │
└─────────────────────────────────────────────────────────────────────┘
"""
import json
import openpyxl
from jinja2 import Template
from config.config import EXCEL_FILE, SHEET_NAME
from utils.logger import logger


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║                        1. 读取 Excel                                    ║
# ╚══════════════════════════════════════════════════════════════════════════╝

def read_excel(file_path: str = None, sheet_name: str = None) -> list[dict]:
    """从 Excel 读取测试用例，只返回 is_true 为 True 的行

    Excel 格式要求：
      - 第 1 行 = 表头（列名）
      - 第 2 行起 = 数据
      - 必须有 is_true 列，值为 TRUE 的才会执行

    返回: list[dict]，每个 dict 是一行用例，key=列名, value=单元格值
    """
    file_path = file_path or EXCEL_FILE
    sheet_name = sheet_name or SHEET_NAME

    try:
        workbook = openpyxl.load_workbook(file_path)
    except FileNotFoundError:
        logger.warning(f"Excel 文件不存在: {file_path}，跳过数据驱动加载")
        return []

    worksheet = workbook[sheet_name]

    # 第 1 行 = 表头
    headers = [cell.value for cell in worksheet[1]]

    data = []
    for row in worksheet.iter_rows(min_row=2, values_only=True):
        # 跳过完全空白的行
        if not any(cell is not None for cell in row):
            continue

        # zip: 把 [列1值, 列2值, ...] 和 [列1名, 列2名, ...] 配对成 dict
        row_dict = dict(zip(headers, row))

        # 只保留 is_true 为 True 的行
        is_true = row_dict.get("is_true")
        if is_true is True or str(is_true).upper() == "TRUE":
            data.append(row_dict)

    workbook.close()
    logger.info(f"从 Excel 加载 {len(data)} 条有效用例")
    return data


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║                        2. 变量渲染（Jinja2）                           ║
# ╚══════════════════════════════════════════════════════════════════════════╝

def render_case(case: dict, global_vars: dict) -> dict:
    """用 Jinja2 模板引擎把用例中的 {{变量}} 替换成实际值

    工作原理：
      1. 把整个用例字典序列化成 JSON 字符串
      2. Jinja2 扫描字符串，找到所有 {{xxx}}
      3. 从 global_vars 字典里取对应的值替换
      4. 把替换后的 JSON 字符串解析回 dict

    例:
      global_vars = {"token": "abc123"}
      case = {"headers": '{"Authorization": "Bearer {{token}}"}'}
      → 渲染后: {"headers": '{"Authorization": "Bearer abc123"}'}

    为什么用 JSON 序列化中转？
      因为用例字典的值可能是嵌套的 JSON 字符串，Jinja2 需要整体文本扫描。
      直接遍历 dict 的 key-value 会漏掉嵌套在 JSON 字符串内部的 {{变量}}。
    """
    case_str = json.dumps(case, ensure_ascii=False)
    return json.loads(Template(case_str).render(global_vars))


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║                        3. 字段类型转换                                  ║
# ╚══════════════════════════════════════════════════════════════════════════╝

def _parse_field(value):
    """把 Excel 单元格的 JSON 字符串自动转成 Python 对象

    Excel 单元格只能存字符串/数字，但要传 dict/list 给 API，
    所以约定：以 { 或 [ 开头的字符串 = JSON，自动解析。

    处理流程:
      ① 是字符串吗？
      ② 去掉前后空格 → 以 { 或 [ 开头吗？
      ③ 尝试 json.loads() 转成 dict/list
      ④ 转换失败 → 原样返回（可能是普通文本写成了 { 开头）
      ⑤ 不是字符串 → 直接返回（数字、None 等）
    """
    if isinstance(value, str):
        value = value.strip()
        if value.startswith(("{", "[")):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value  # 格式写错了，不崩溃，原样返回
    return value
