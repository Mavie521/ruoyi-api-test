"""
若依接口测试框架 - 运行入口

用法:
    python run.py run              # 运行全部测试
    python run.py run -m smoke     # 只跑冒烟测试
    python run.py run -k login     # 按关键字过滤
    python run.py run -n 4         # 4 进程并发
    python run.py report           # 生成 Allure 报告
    python run.py open             # 打开 Allure 报告
"""
import os
import sys
import subprocess
from pathlib import Path


# 内置 marker 列表（用于 run.py 的智能解析）
KNOWN_MARKERS = {"smoke", "regression", "critical", "slow"}


def resolve_target(args, base_dir: Path) -> tuple:
    """
    智能解析命令行参数:
    - 直接传 marker 名（如 smoke）自动转为 -m smoke
    - 传路径则作为测试目录执行
    - 默认跑 tests/
    """
    target = args.test_path
    if not target:
        return ["tests/"], None, None

    target_path = Path(target)
    if target_path.exists():
        return [str(target_path)], args.mark, args.keyword

    if target in KNOWN_MARKERS and not args.mark:
        return ["tests/"], target, args.keyword

    return [target], args.mark, args.keyword


def run_tests(args):
    """执行 pytest 命令"""
    base_dir = Path(__file__).resolve().parent
    cmd = ["pytest"]

    test_paths, mark, keyword = resolve_target(args, base_dir)
    cmd.extend(test_paths)

    if mark:
        cmd.extend(["-m", mark])
    if keyword:
        cmd.extend(["-k", keyword])
    if args.workers and args.workers > 1:
        cmd.extend(["-n", str(args.workers)])

    cmd.extend(["--alluredir", "./reports/allure-results", "--clean-alluredir", "-v"])

    print("=" * 60)
    print(" RuoYi API Test Framework")
    print(f" CMD: {' '.join(cmd)}")
    print(f" URL: {os.getenv('BASE_URL', 'http://127.0.0.1:8080')}")
    print("=" * 60)

    return subprocess.run(cmd, cwd=base_dir).returncode


def generate_allure_report():
    """生成 Allure HTML 报告"""
    base_dir = Path(__file__).resolve().parent
    results_dir = base_dir / "reports" / "allure-results"
    report_dir = base_dir / "reports" / "allure-report"

    if not results_dir.exists() or not list(results_dir.iterdir()):
        print("[WARN] allure-results 目录为空，请先运行测试")
        return

    cmd = ["allure", "generate", str(results_dir), "-o", str(report_dir), "--clean"]
    print("生成 Allure 报告...")
    if subprocess.run(cmd, cwd=base_dir).returncode == 0:
        print(f"\n[OK] 报告已生成: {report_dir}")
        print(f"[INFO] 查看报告: allure open {report_dir}")
    else:
        print("[FAIL] 报告生成失败，请确保已安装 Allure 命令行工具")
        print("   下载: https://github.com/allure-framework/allure2/releases")


def open_allure_report():
    """打开 Allure 报告"""
    base_dir = Path(__file__).resolve().parent
    report_dir = base_dir / "reports" / "allure-report"
    if not report_dir.exists():
        print("[WARN] 报告目录不存在，请先运行 python run.py report")
        return
    subprocess.run(["allure", "open", str(report_dir)], cwd=base_dir)


def main():
    import argparse

    parser = argparse.ArgumentParser(description="若依接口测试框架")
    sub = parser.add_subparsers(dest="command")

    # run 子命令
    p = sub.add_parser("run", help="运行测试")
    p.add_argument("test_path", nargs="?", help="测试路径或 marker 名（如 smoke）")
    p.add_argument("-m", "--mark", help="按 marker 运行")
    p.add_argument("-k", "--keyword", help="按关键字运行")
    p.add_argument("-n", "--workers", type=int, default=1, help="并发进程数")

    # report 子命令
    sub.add_parser("report", help="生成 Allure 报告")
    sub.add_parser("open", help="打开 Allure 报告")

    args = parser.parse_args()

    if args.command == "run":
        code = run_tests(args)
        if code == 0:
            generate_allure_report()
        sys.exit(code)
    elif args.command == "report":
        generate_allure_report()
    elif args.command == "open":
        open_allure_report()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
