"""
测试执行器 —— subprocess 调用 pytest（线程池方案，兼容 Windows/Linux）

职责:
  1. 全局并发控制（同一时间只允许一个任务 running）
  2. 组装 pytest 命令（list 方式，shell=False）
  3. 线程池执行 subprocess.Popen，不阻塞事件循环
  4. 解析 junitxml（委托 parser.py）
  5. 生成 Allure 报告（allure generate）
  6. 任务状态流转（pending → running → passed/failed/error）

不负责:
  - HTTP 接口（由 run_routes.py 负责）
  - XML 解析细节（由 parser.py 负责）
  - 用例收集（由 collector.py 负责）
"""
import os
import sys
import asyncio
import subprocess
import concurrent.futures
from typing import Optional
from pathlib import Path
from datetime import datetime
from ..config import PROJECT_ROOT, REPORTS_DIR, PYTEST_TIMEOUT
from ..database import create_run, update_run, is_running
from .parser import parse_and_store


# 线程池 + 全局锁
_executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
_run_lock = asyncio.Lock()


def _run_pytest_sync(cmd: list, cwd: str, timeout: int, env: dict) -> str:
    """
    同步执行 pytest（在线程池中运行）

    参数:
      cmd:     命令 list
      cwd:     工作目录
      timeout: 超时秒数
      env:     环境变量 dict

    返回:
      stdout + stderr 合并字符串
    """
    process = subprocess.Popen(
        cmd,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        env=env,
    )

    try:
        stdout, _ = process.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        process.terminate()
        stdout, _ = process.communicate()
        stdout += "\n[TIMEOUT] pytest 执行超时，已终止"

    return stdout or ""


async def execute_pytest(
    environment: str = "dev",
    markers: str = "",
    test_path: str = "tests/",
    keyword: str = "",
    extra_args: str = "",
    base_url: str = "",
) -> dict:
    """
    异步执行 pytest（线程池 + subprocess.Popen）

    并发控制:
      - 使用 asyncio.Lock 确保全局只有一个任务
      - 请求时先检查 is_running()，有 running 则拒绝

    命令组装（list 方式，shell=False）:
      [python, -m, pytest, tests/, --env=dev, -m, p0,
       --junitxml=reports/junit_{tag}.xml,
       --alluredir=reports/allure-results-{tag}, -v, --tb=short]
    """
    # ── 并发控制 ──
    if is_running():
        return None

    async with _run_lock:
        if is_running():
            return None

        # ── 1. 创建数据库记录 ──
        run = create_run(
            environment=environment,
            markers=markers,
            test_path=test_path,
            keyword=keyword,
            extra_args=extra_args,
        )
        run_id = run["id"]
        tag = run["run_tag"]

        # ── 2. 组装 pytest 命令 ──
        allure_results_dir = REPORTS_DIR / f"allure-results-{tag}"
        allure_report_dir = REPORTS_DIR / f"allure-report-{tag}"
        junit_path = REPORTS_DIR / f"junit-{tag}.xml"

        allure_results_dir.mkdir(parents=True, exist_ok=True)

        cmd = [
            sys.executable, "-m", "pytest",
            test_path,
            f"--alluredir={str(allure_results_dir)}",
            f"--junitxml={str(junit_path)}",
            "-v", "--tb=short",
        ]

        if markers:
            cmd.extend(["-m", markers])
        if keyword:
            cmd.extend(["-k", keyword])
        if extra_args:
            cmd.extend(extra_args.split())

        # ── 3. 线程池执行 pytest ──
        started_at = datetime.now().isoformat()
        update_run(run_id, status="running", started_at=started_at)

        try:
            loop = asyncio.get_event_loop()
            sub_env = {**os.environ, "ENV": environment}
            if base_url:
                sub_env["BASE_URL"] = base_url
            output = await loop.run_in_executor(
                _executor,
                _run_pytest_sync,
                cmd,
                str(PROJECT_ROOT),
                PYTEST_TIMEOUT,
                sub_env,
            )
        except Exception as exc:
            import traceback
            output = f"[ERROR] 执行异常: {exc}\n{traceback.format_exc()}"

        finished_at = datetime.now().isoformat()

        # ── 4. 解析结果并入库 ──
        summary = parse_and_store(str(junit_path), run_id)

        # ── 5. 判定最终状态 ──
        if summary["failed"] > 0 or summary["error"] > 0:
            status = "failed"
        elif summary["total"] == 0:
            status = "error"
        else:
            status = "passed"

        # ── 6. 更新 runs 记录 ──
        update_run(
            run_id,
            status=status,
            total_tests=summary["total"],
            passed_tests=summary["passed"],
            failed_tests=summary["failed"],
            skipped_tests=summary["skipped"],
            error_tests=summary["error"],
            duration_sec=summary["duration"],
            finished_at=finished_at,
            output_log=output,
            allure_dir=str(allure_report_dir.relative_to(PROJECT_ROOT)),
        )

        # ── 7. 生成 Allure 报告（同步方式） ──
        await _generate_allure(allure_results_dir, allure_report_dir)

        # ── 8. 钉钉通知 ──
        try:
            from .dingtalk import send_notification
            send_notification(
                run_tag=tag, status=status,
                total=summary["total"], passed=summary["passed"],
                failed=summary["failed"], duration=summary["duration"],
                report_url=f"http://localhost:8001/api/reports/{tag}",
            )
        except Exception:
            pass

        return get_full_run(run_id)


async def _generate_allure(results_dir: Path, report_dir: Path):
    """调用 allure generate 生成离线 HTML 报告"""
    try:
        loop = asyncio.get_event_loop()
        report_dir.mkdir(parents=True, exist_ok=True)
        await loop.run_in_executor(
            _executor,
            lambda: subprocess.run(
                ["allure", "generate", str(results_dir), "-o", str(report_dir), "--clean"],
                cwd=str(PROJECT_ROOT),
                capture_output=True,
                timeout=60,
            ),
        )
    except Exception:
        pass


def get_full_run(run_id: int) -> Optional[dict]:
    """获取执行记录 + 关联的用例结果"""
    from ..database import get_run, get_results
    run = get_run(run_id)
    if not run:
        return None
    run["results"] = get_results(run_id)
    return run
