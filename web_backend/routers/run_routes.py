"""
执行管理 — 创建任务 + 历史查询 + 任务详情 + 状态轮询

接口:
  POST /api/runs               — 创建异步测试任务
  GET  /api/runs               — 执行历史（分页）
  GET  /api/runs/{id}          — 单次执行详情+结果
  GET  /api/runs/{id}/status   — 轻量状态轮询（2秒一次）
"""
import asyncio
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from ..config import ENV_OPTIONS
from ..database import list_runs, get_run, get_results, delete_run, is_running
from ..services.runner import execute_pytest

router = APIRouter()


class RunRequest(BaseModel):
    environment: str = "dev"
    markers: str = ""
    test_path: str = "tests/"
    keyword: str = ""
    extra_args: str = ""
    base_url: str = ""


@router.post("")
async def trigger_run(req: RunRequest):
    """创建并启动异步测试任务"""
    # 并发检查
    if is_running():
        raise HTTPException(
            status_code=409,
            detail="已有测试任务正在执行中，请等待完成后再提交",
        )

    # 环境参数校验
    if req.environment not in ENV_OPTIONS:
        raise HTTPException(
            status_code=400,
            detail=f"无效环境: {req.environment}，可选: {', '.join(ENV_OPTIONS)}",
        )

    # 后台异步执行（不阻塞 HTTP 响应）
    asyncio.create_task(
        execute_pytest(
            environment=req.environment,
            markers=req.markers,
            test_path=req.test_path,
            keyword=req.keyword,
            extra_args=req.extra_args,
            base_url=req.base_url,
        )
    )

    # 立即返回（任务在后台 running）
    # 查最新一条 pending/running 记录
    return {
        "code": 200,
        "message": "测试任务已提交，正在执行中...",
        "data": {"status": "pending"},
    }


@router.get("")
async def get_runs(page: int = 1, page_size: int = 20):
    """执行历史列表（分页）"""
    data = list_runs(page=page, page_size=page_size)
    return {"code": 200, "message": "success", "data": data}


@router.get("/{run_id}")
async def get_run_detail(run_id: int):
    """单次执行详情（含所有用例结果）"""
    run = get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="执行记录不存在")
    run["results"] = get_results(run_id)
    return {"code": 200, "message": "success", "data": run}


@router.get("/{run_id}/status")
async def get_run_status(run_id: int):
    """
    轻量状态轮询接口（前端 2 秒一次）

    仅返回状态 + 计数，不查询 results 表，适合高频调用
    """
    run = get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="执行记录不存在")

    return {
        "code": 200,
        "message": "success",
        "data": {
            "status": run["status"],
            "total": run["total_tests"],
            "passed": run["passed_tests"],
            "failed": run["failed_tests"],
            "skipped": run["skipped_tests"],
            "error": run["error_tests"],
            "duration": run["duration_sec"],
            "run_tag": run["run_tag"],
        },
    }


@router.post("/{run_id}/rerun-failed")
async def rerun_failed(run_id: int):
    """只重跑失败用例"""
    run = get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="执行记录不存在")
    if is_running():
        raise HTTPException(status_code=409, detail="已有测试任务正在执行中")

    # 从 run_results 中提取失败的 nodeid
    results = get_results(run_id, outcome="failed")
    if not results:
        raise HTTPException(status_code=400, detail="没有失败的用例可重跑")

    failed_nodes = [r["nodeid"] for r in results if r.get("nodeid")]
    if not failed_nodes:
        raise HTTPException(status_code=400, detail="失败用例缺少 nodeid")

    # 用 nodeid 拼接成 pytest 关键字（空格分隔）
    keywords = " or ".join(failed_nodes)

    asyncio.create_task(
        execute_pytest(
            environment=run.get("environment", "dev"),
            test_path="",          # 不传 test_path，全靠 -k
            keyword=run.get("keyword", ""),
            extra_args=f"-k \"{keywords}\"",
        )
    )
    return {"code": 200, "message": f"已提交重跑 {len(failed_nodes)} 条失败用例", "data": {"count": len(failed_nodes)}}


@router.post("/clear-stuck")
async def clear_stuck():
    """清除所有卡住的 running 任务"""
    from ..database import _get_conn
    c = _get_conn()
    cur = c.execute("UPDATE runs SET status='error', output_log='手动清除: 任务卡住' WHERE status='running'")
    c.commit()
    count = cur.rowcount
    return {"code": 200, "message": f"已清除 {count} 个卡住的任务", "data": {"count": count}}


@router.delete("/{run_id}")
async def remove_run(run_id: int):
    """删除执行记录"""
    if not get_run(run_id):
        raise HTTPException(status_code=404, detail="执行记录不存在")
    if is_running():
        # 如果正在执行，先检查是不是要删的这个
        run = get_run(run_id)
        if run["status"] == "running":
            raise HTTPException(status_code=409, detail="无法删除正在执行的任务")
    delete_run(run_id)
    return {"code": 200, "message": "已删除", "data": None}
