"""
测试执行器 —— subprocess 调用 pytest（asyncio.to_thread 方案）

职责:
  1. 全局并发控制（同一时间只允许一个任务 running）
  2. 组装 pytest 命令（list 方式，shell=False）
  3. asyncio.to_thread 执行 subprocess.Popen
  4. 解析 junitxml（委托 parser.py）
  5. 生成 Allure 报告（allure generate）
  6. 任务状态流转（pending → running → passed/failed/error）
"""
import os
import sys
import asyncio
import subprocess
from typing import Optional
from pathlib import Path
from datetime import datetime
from ..config import PROJECT_ROOT, REPORTS_DIR, PYTEST_TIMEOUT
from ..database import create_run, update_run, is_running
from .parser import parse_and_store


_run_lock = asyncio.Lock()


def _run_pytest_sync(cmd: list, cwd: str, timeout: int, env: dict) -> str:
    """同步执行 pytest（在 asyncio.to_thread 中运行）"""
    process = subprocess.Popen(
        cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, env=env,
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
    """异步执行 pytest（asyncio.to_thread + subprocess.Popen）"""
    # ── 并发控制：锁内只做 DB 写入，不放耗时操作 ──
    run = None
    async with _run_lock:
        if is_running():
            return None
        run = create_run(
            environment=environment, markers=markers, test_path=test_path,
            keyword=keyword, extra_args=extra_args,
        )
        run_id = run["id"]
        update_run(run_id, status="running", started_at=datetime.now().isoformat())

    if run is None:
        return None

    # ── 1. 使用已创建的记录 ──
    tag = run["run_tag"]

    # ── 2. 组装 pyt est 命令 ──
    allure_results_dir = REPORTS_DIR / f"allure-results-{tag}"
    allure_report_dir = REPORTS_DIR / f"allure-report-{tag}"
    junit_path = REPORTS_DIR / f"junit-{tag}.xml"
    allure_results_dir.mkdir(parents=True, exist_ok=True)

    cmd = [
        sys.executable, "-m", "pytest",
        f"--alluredir={str(allure_results_dir)}",
        f"--junitxml={str(junit_path)}",
        "-v", "--tb=short",
    ]
    if test_path:
        cmd.extend(test_path.split())
    if markers:
        cmd.extend(["-m", markers])
    if keyword:
        cmd.extend(["-k", keyword])
    if extra_args:
        cmd.extend(extra_args.split())

    # ── 3. 执行（锁已释放，不阻塞其他请求的 DB 查询）──
    output_lines = []

    try:
        sub_env = {**os.environ, "ENV": environment}
        if base_url:
            sub_env["BASE_URL"] = base_url
            output_lines.append(f"[CONFIG] 使用环境 {environment} 的 BASE_URL={base_url}")
        else:
            output_lines.append(f"[CONFIG] 使用默认 BASE_URL={sub_env.get('BASE_URL', '未设置')}")

        output = await asyncio.to_thread(
            _run_pytest_sync, cmd, str(PROJECT_ROOT), PYTEST_TIMEOUT, sub_env,
        )
    except Exception as exc:
        import traceback
        output = f"[ERROR] 执行异常: {exc}\n{traceback.format_exc()}"

    finished_at = datetime.now().isoformat()

    # ── 4. 解析结果 ──
    summary = parse_and_store(str(junit_path), run_id)

    status = "failed" if (summary["failed"] > 0 or summary["error"] > 0) else (
        "error" if summary["total"] == 0 else "passed")

    # ── 5. 更新 runs ──
    update_run(
        run_id, status=status,
        total_tests=summary["total"], passed_tests=summary["passed"],
        failed_tests=summary["failed"], skipped_tests=summary["skipped"],
        error_tests=summary["error"], duration_sec=summary["duration"],
        finished_at=finished_at,
        output_log="\n".join(output_lines) + "\n" + output,
        allure_dir=str(allure_report_dir.relative_to(PROJECT_ROOT)),
    )

    # ── 6. Allure ──
    try:
        report_dir = allure_report_dir
        report_dir.mkdir(parents=True, exist_ok=True)
        await asyncio.to_thread(
            lambda: subprocess.run(
                ["allure", "generate", str(allure_results_dir), "-o", str(report_dir), "--clean"],
                cwd=str(PROJECT_ROOT), capture_output=True, timeout=60,
            )
        )
    except Exception:
        pass

    # ── 7. 钉钉 ──
    try:
        from .dingtalk import send_notification
        from ..config import PLATFORM_URL
        send_notification(
            run_tag=tag, status=status, total=summary["total"],
            passed=summary["passed"], failed=summary["failed"],
            duration=summary["duration"],
            report_url=f"{PLATFORM_URL.rstrip('/')}/api/reports/{tag}",
        )
    except Exception:
        pass

    return get_full_run(run_id)


def get_full_run(run_id: int) -> Optional[dict]:
    from ..database import get_run, get_results
    run = get_run(run_id)
    if not run:
        return None
    run["results"] = get_results(run_id)
    return run
