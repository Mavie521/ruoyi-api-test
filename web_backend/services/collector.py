"""
用例收集器 —— 调用 pytest --collect-only 获取用例列表，结果存入 SQLite 缓存

解析规则（基于 pytest --collect-only -q 标准输出）:
  每行格式: tests/test_module.py::TestClass::test_function
  不包含路径的行（如函数级用例）: tests/test_module.py::test_function

安全约束:
  - 使用 list 方式组装命令，shell=False
  - 设置超时防止子进程卡死
"""
import re
import subprocess
import sys
from pathlib import Path
from datetime import datetime
from ..config import PROJECT_ROOT
from ..database import clear_case_cache, insert_case


# pytest --collect-only 输出行模式:
#   tests/test_role.py::TestRole::test_list_roles
#   tests/test_security.py::test_login_sql_injection[admin' OR '1'='1]
COLLECT_LINE = re.compile(
    r"^(?P<module>tests/.+?\.py)::(?:(?P<class>[^:]+?)::)?(?P<func>test_\w+)(?:\[.+?\])?$"
)


def refresh_case_cache() -> dict:
    """
    全量刷新用例缓存

    步骤:
      1. 调用 pytest --collect-only -q --no-header
      2. 逐行解析 stdout，提取 module / class / function
      3. 清空旧缓存，写入新数据

    返回:
      {"count": 31, "message": "用例缓存已刷新"}
    """
    cmd = [
        sys.executable, "-m", "pytest", "tests/",
        "--collect-only", "-q", "--no-header",
    ]

    try:
        result = subprocess.run(
            cmd,
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            timeout=30,
        )
    except subprocess.TimeoutExpired:
        return {"count": 0, "message": "用例收集超时（30秒），请检查 pytest 环境"}
    except FileNotFoundError:
        return {"count": 0, "message": "未找到 pytest，请确认已安装 pytest 依赖"}

    if result.returncode not in (0, 1):  # pytest collect 有时返回 1 但有标准输出
        return {
            "count": 0,
            "message": f"pytest 收集失败 (exit={result.returncode}):\n{result.stderr[:500]}",
        }

    # 解析输出
    cases = []
    for line in result.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        match = COLLECT_LINE.match(line)
        if not match:
            continue

        module = match.group("module")
        class_name = match.group("class") or ""
        func_name = match.group("func")

        if not func_name:
            continue

        nodeid = f"{module}::{class_name}::{func_name}" if class_name else f"{module}::{func_name}"
        cases.append({
            "nodeid": nodeid,
            "module": module,
            "class_name": class_name,
            "func_name": func_name,
            "markers": [],  # markers 解析留到后续版本
        })

    if not cases:
        return {"count": 0, "message": "未收集到任何用例，请检查 tests/ 目录"}

    # 写入缓存
    clear_case_cache()
    for c in cases:
        insert_case(
            nodeid=c["nodeid"],
            module=c["module"],
            class_name=c["class_name"],
            func_name=c["func_name"],
            markers=c["markers"],
        )

    return {"count": len(cases), "message": f"用例缓存已刷新，共 {len(cases)} 条"}
