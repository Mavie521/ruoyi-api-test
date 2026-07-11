"""
Excel 测试用例读取工具
支持按 is_true 字段过滤用例，实现分组执行
"""
import openpyxl
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
    headers = [cell.value for cell in worksheet[2]]

    data = []
    for row in worksheet.iter_rows(min_row=3, values_only=True):
        row_dict = dict(zip(headers, row))
        # is_true 列控制是否执行
        if row_dict.get("is_true") in (True, 1, "TRUE", "true", "True", "是"):
            data.append(row_dict)

    workbook.close()
    logger.info(f"从 Excel 加载 {len(data)} 条有效用例")
    return data
