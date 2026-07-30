"""
测试运行入口 —— 对 pytest 的薄封装，你也可以直接用 pytest 命令

用法:
    python run.py                # 跑全部测试
    python run.py -m p0          # 只跑 P0
    python run.py -k login       # 按关键字过滤
    python run.py --report       # 生成 Allure 报告
"""
import sys
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
ARGS = sys.argv[1:]

# 如果要求生成报告
if "--report" in ARGS:
    ARGS.remove("--report")
    results = BASE_DIR / "reports" / "allure-results"
    report = BASE_DIR / "reports" / "allure-report"
    cmd = ["allure", "generate", str(results), "-o", str(report), "--clean"]
    subprocess.run(cmd, cwd=BASE_DIR)
    sys.exit(0)

# 默认：跑测试
cmd = [
    "pytest", "tests/",
    "--alluredir=./reports/allure-results",
    "--clean-alluredir",
    "-v",
] + ARGS

print(f">>> {' '.join(cmd)}")
sys.exit(subprocess.run(cmd, cwd=BASE_DIR).returncode)
