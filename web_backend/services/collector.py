"""
用例收集器 —— 调用 pytest --collect-only 获取用例列表，结果存入 SQLite 缓存

解析规则:
  不同 pytest 版本输出格式不同:
    新版: tests/test_module.py::TestClass::test_function
    旧版/树形: <Module test_module.py>
                 <Class TestClass>
                   <Function test_function>

  优先匹配 :: 格式，回退到树形解析。

安全约束:
  - 使用 list 方式组装命令，shell=False
  - 设置超时防止子进程卡死
"""
import re
import subprocess
import sys
from ..config import PROJECT_ROOT
from ..database import clear_case_cache, insert_case


# :: 格式: tests/test_role.py::TestRole::test_list_roles
COLLECT_LINE = re.compile(
    r"^(?P<module>(?:tests|testcases)/.+?\.py)::(?:(?P<class>[^:]+?)::)?(?P<func>test_\w+)(?:\[.+?\])?$"
)

# 树形格式: <Module test_role.py> / <Class TestRole> / <Function test_list_roles>
TREE_MODULE = re.compile(r"<Module\s+(.+?)>")
TREE_CLASS = re.compile(r"<Class\s+(.+?)>")
TREE_FUNC = re.compile(r"<Function\s+(.+?)>")


def refresh_case_cache() -> dict:
    """
    全量刷新用例缓存

    步骤:
      1. 调用 pytest --collect-only（不传 -q，兼容新旧版输出格式）
      2. 逐行解析 stdout，提取 module / class / function
      3. 清空旧缓存，写入新数据
    """
    cmd = [
        sys.executable, "-m", "pytest", "tests/", "testcases/",
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

    # 合并 stdout + stderr（某些 pytest 版本输出到 stderr）
    output = result.stdout + "\n" + result.stderr

    if result.returncode not in (0, 1):
        return {
            "count": 0,
            "message": f"pytest 收集失败 (exit={result.returncode}):\n{output[:500]}",
        }

    # 解析输出 — 优先 :: 格式，回退树形格式
    cases = _parse_colon_format(output)

    if not cases:
        cases = _parse_tree_format(output)

    if not cases:
        return {"count": 0, "message": "未收集到任何用例，请检查 tests/ 目录\n输出:\n" + output[:500]}

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


def _parse_colon_format(text: str) -> list:
    """解析 :: 格式"""
    cases = []
    for line in text.splitlines():
        line = line.strip()
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
            "nodeid": nodeid, "module": module,
            "class_name": class_name, "func_name": func_name, "markers": [],
        })
    return cases


def _parse_tree_format(text: str) -> list:
    """解析树形格式 <Module> <Class> <Function>"""
    cases = []
    current_module = ""
    current_class = ""

    for line in text.splitlines():
        line = line.strip()

        m = TREE_MODULE.search(line)
        if m:
            current_module = f"tests/{m.group(1)}"
            current_class = ""
            continue

        c = TREE_CLASS.search(line)
        if c:
            current_class = c.group(1)
            continue

        f = TREE_FUNC.search(line)
        if f:
            func_name = f.group(1)
            if current_module:
                nodeid = f"{current_module}::{current_class}::{func_name}" if current_class else f"{current_module}::{func_name}"
                cases.append({
                    "nodeid": nodeid, "module": current_module,
                    "class_name": current_class, "func_name": func_name, "markers": [],
                })

    return cases
