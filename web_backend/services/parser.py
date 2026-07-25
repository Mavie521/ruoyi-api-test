"""
JUnit XML 解析器 —— 解析 pytest --junitxml 输出，写入数据库

职责:
  1. 解析 xml 的 <testsuite> 汇总信息
  2. 解析每个 <testcase> 的结果 (passed/failed/skipped/error)
  3. 批量写入 run_results 表

不负责:
  - 调用 pytest（由 runner.py 负责）
  - 生成 Allure 报告（由 runner.py 负责）
  - 任务状态更新（由 runner.py 负责）
"""
import xml.etree.ElementTree as ET
from pathlib import Path
from ..database import insert_result


def parse_and_store(xml_path, run_id: int) -> dict:
    """
    解析 JUnit XML 文件，将每条用例结果写入 run_results 表

    参数:
      xml_path:  JUnit XML 文件路径
      run_id:    对应的 runs 表主键

    返回:
      {
        "total": 9, "passed": 8, "failed": 1,
        "skipped": 0, "error": 0, "duration": 12.5
      }
    """
    path = Path(xml_path)
    if not path.exists():
        return {"total": 0, "passed": 0, "failed": 0, "skipped": 0, "error": 0, "duration": 0}

    tree = ET.parse(str(path))
    root = tree.getroot()

    total = int(root.get("tests", 0))
    failures = int(root.get("failures", 0))
    errors = int(root.get("errors", 0))
    skipped = int(root.get("skipped", 0))
    duration = float(root.get("time", 0))
    passed = total - failures - errors - skipped

    for testcase in root.findall("testcase"):
        classname = testcase.get("classname", "")
        name = testcase.get("name", "")
        time_val = float(testcase.get("time", 0))
        nodeid = f"{classname}::{name}" if classname else name

        outcome = "passed"
        message = ""

        failure_el = testcase.find("failure")
        error_el = testcase.find("error")
        skipped_el = testcase.find("skipped")

        if failure_el is not None:
            outcome = "failed"
            msg = failure_el.get("message", "")
            text = (failure_el.text or "").strip()
            message = f"{msg}\n{text}" if msg else text
            if len(message) > 2000:
                message = message[:2000] + "..."
        elif error_el is not None:
            outcome = "error"
            msg = error_el.get("message", "")
            text = (error_el.text or "").strip()
            message = f"{msg}\n{text}" if msg else text
            if len(message) > 2000:
                message = message[:2000] + "..."
        elif skipped_el is not None:
            outcome = "skipped"
            msg = skipped_el.get("message", "")
            message = msg if msg else "Skipped"

        insert_result(
            run_id=run_id,
            test_name=name,
            nodeid=nodeid,
            outcome=outcome,
            duration_sec=round(time_val, 3),
            message=message,
        )

    return {
        "total": total,
        "passed": passed,
        "failed": failures,
        "skipped": skipped,
        "error": errors,
        "duration": round(duration, 2),
    }
